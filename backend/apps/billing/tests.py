import tempfile
from datetime import date, time
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.attendance.models import Attendance
from apps.scheduling.models import Session
from apps.students.models import Student
from apps.teacher.models import Teacher

from . import report_builder
from .models import MonthlyReport


def make_student(**kwargs):
    defaults = {
        "teacher": Teacher.load(),
        "name": "Nguyen Van A",
        "start_date": date(2024, 1, 1),
        "price_per_session": Decimal("200000"),
    }
    defaults.update(kwargs)
    return Student.objects.create(**defaults)


def make_session(student, session_date, **kwargs):
    defaults = {"start_time": time(18, 0), "end_time": time(19, 0)}
    defaults.update(kwargs)
    return Session.objects.create(student=student, session_date=session_date, **defaults)


class BuildReportDataTests(TestCase):
    def setUp(self):
        self.student = make_student(price_per_session=Decimal("200000"))

    def test_counts_only_billable_sessions_in_target_month(self):
        present = make_session(self.student, date(2026, 3, 5))
        Attendance.objects.create(session=present, status=Attendance.Status.PRESENT)
        absent = make_session(self.student, date(2026, 3, 12))
        Attendance.objects.create(session=absent, status=Attendance.Status.ABSENT)
        make_session(self.student, date(2026, 3, 19))  # chưa điểm danh
        make_session(self.student, date(2026, 4, 1))  # tháng khác

        data = report_builder.build_report_data(self.student, month=3, year=2026)

        self.assertEqual(data["total_sessions"], 1)
        self.assertEqual(data["total_amount"], Decimal("200000"))
        self.assertEqual(len(data["sessions"]), 3)
        statuses = {row["status"] for row in data["sessions"]}
        self.assertIn("Chưa điểm danh", statuses)

    def test_empty_month_returns_zero(self):
        data = report_builder.build_report_data(self.student, month=1, year=2020)
        self.assertEqual(data["total_sessions"], 0)
        self.assertEqual(data["sessions"], [])
        self.assertEqual(data["total_amount"], Decimal("0"))


class RenderPngTests(TestCase):
    def test_render_png_returns_valid_png_bytes(self):
        student = make_student()
        data = report_builder.build_report_data(student, month=1, year=2026)
        content = report_builder.render_png(data)
        self.assertTrue(content.startswith(b"\x89PNG"))

    def test_render_png_handles_many_rows(self):
        student = make_student()
        data = report_builder.build_report_data(student, month=1, year=2026)
        data["sessions"] = [
            {"session_date": date(2026, 1, d), "start_time": time(18, 0), "status": "Có mặt", "billable": True}
            for d in range(1, 9)
        ]
        content = report_builder.render_png(data)
        self.assertTrue(content.startswith(b"\x89PNG"))


class GenerateReportTests(TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.tmp_dir.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.student = make_student(price_per_session=Decimal("200000"))
        session = make_session(self.student, date(2026, 5, 5))
        Attendance.objects.create(session=session, status=Attendance.Status.PRESENT)

    @patch("apps.billing.report_builder.render_png", return_value=b"fake-png-bytes")
    def test_generate_creates_file_and_report_row(self, mock_render):
        report = report_builder.generate_report(self.student, 5, 2026, "png")

        self.assertEqual(report.total_sessions, 1)
        self.assertEqual(report.total_amount, Decimal("200000"))
        full_path = Path(self.tmp_dir.name) / report.file_url
        self.assertTrue(full_path.exists())
        self.assertEqual(full_path.read_bytes(), b"fake-png-bytes")

    @patch("apps.billing.report_builder.render_pdf", return_value=b"fake-pdf-bytes")
    @patch("apps.billing.report_builder.render_png", return_value=b"fake-png-bytes")
    def test_regenerate_with_different_format_overwrites_and_removes_old_file(
        self, mock_png, mock_pdf
    ):
        first = report_builder.generate_report(self.student, 5, 2026, "png")
        first_path = Path(self.tmp_dir.name) / first.file_url
        self.assertTrue(first_path.exists())

        second = report_builder.generate_report(self.student, 5, 2026, "pdf")

        self.assertEqual(first.id, second.id)  # cùng 1 bản ghi (unique student/month/year)
        self.assertFalse(first_path.exists())  # file .png cũ đã bị xóa
        second_path = Path(self.tmp_dir.name) / second.file_url
        self.assertTrue(second_path.exists())
        self.assertEqual(MonthlyReport.objects.filter(student=self.student, month=5, year=2026).count(), 1)

    @patch("apps.billing.report_builder.render_png", return_value=b"v1")
    def test_regenerate_same_format_overwrites_content(self, mock_render):
        report_builder.generate_report(self.student, 5, 2026, "png")
        mock_render.return_value = b"v2"
        report = report_builder.generate_report(self.student, 5, 2026, "png")

        full_path = Path(self.tmp_dir.name) / report.file_url
        self.assertEqual(full_path.read_bytes(), b"v2")


class MonthlyReportAPITests(APITestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.tmp_dir.name)
        self.override.enable()
        self.addCleanup(self.override.disable)

        self.user = get_user_model().objects.create_user(username="teacher1", password="pass12345")
        self.client.force_authenticate(user=self.user)
        self.student = make_student(price_per_session=Decimal("200000"))
        session = make_session(self.student, date(2026, 6, 1))
        Attendance.objects.create(session=session, status=Attendance.Status.PRESENT)

    def test_unauthenticated_rejected(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get("/api/monthly-reports/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_preview_returns_rows_and_totals(self):
        resp = self.client.get(
            f"/api/monthly-reports/preview/?student={self.student.id}&month=6&year=2026"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertEqual(resp.data["total_sessions"], 1)
        self.assertEqual(len(resp.data["sessions"]), 1)

    def test_preview_missing_student_returns_400(self):
        resp = self.client.get("/api/monthly-reports/preview/?month=6&year=2026")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.billing.report_builder.render_pdf", return_value=b"%PDF-fake")
    def test_generate_creates_report_and_history_lists_it(self, mock_render):
        resp = self.client.post(
            "/api/monthly-reports/generate/",
            {"student": str(self.student.id), "month": 6, "year": 2026, "format": "pdf"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertIn("download_url", resp.data)

        history = self.client.get(f"/api/monthly-reports/?student={self.student.id}")
        self.assertEqual(len(history.data), 1)
        self.assertEqual(history.data[0]["month"], 6)

    @patch("apps.billing.report_builder.render_png", return_value=b"fake-png-bytes")
    def test_download_returns_file_content(self, mock_render):
        gen_resp = self.client.post(
            "/api/monthly-reports/generate/",
            {"student": str(self.student.id), "month": 6, "year": 2026, "format": "png"},
            format="json",
        )
        report_id = gen_resp.data["id"]

        resp = self.client.get(f"/api/monthly-reports/{report_id}/download/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        content = b"".join(resp.streaming_content)
        self.assertEqual(content, b"fake-png-bytes")
        self.assertEqual(resp["Content-Type"], "image/png")

    def test_download_404_when_file_missing_on_disk(self):
        report = MonthlyReport.objects.create(
            student=self.student,
            month=1,
            year=2020,
            total_sessions=0,
            total_amount=Decimal("0"),
            file_url="reports/nonexistent.pdf",
        )
        resp = self.client.get(f"/api/monthly-reports/{report.id}/download/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

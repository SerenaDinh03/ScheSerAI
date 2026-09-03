from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.attendance.models import Attendance
from apps.billing.models import MonthlyReport
from apps.students.models import Student
from apps.teacher.models import Teacher

from .models import Session


def make_student(**kwargs):
    defaults = {
        "teacher": Teacher.load(),
        "name": "Nguyen Van A",
        "start_date": date(2024, 1, 1),
        "price_per_session": Decimal("200000"),
    }
    defaults.update(kwargs)
    return Student.objects.create(**defaults)


def make_session(student, session_date, start_time=time(18, 0), **kwargs):
    return Session.objects.create(
        student=student,
        session_date=session_date,
        start_time=start_time,
        end_time=time(19, 0),
        **kwargs,
    )


class SessionModelTests(TestCase):
    def setUp(self):
        self.student = make_student()

    def test_has_started_true_for_past_date(self):
        session = make_session(self.student, date.today() - timedelta(days=1))
        self.assertTrue(session.has_started())

    def test_has_started_false_for_future_date(self):
        session = make_session(self.student, date.today() + timedelta(days=1))
        self.assertFalse(session.has_started())

    def test_has_started_uses_start_time_for_today(self):
        now = timezone.localtime()
        past_time_today = (now - timedelta(hours=1)).time()
        future_time_today = (now + timedelta(hours=1)).time()
        started = make_session(self.student, now.date(), start_time=past_time_today)
        not_started = make_session(self.student, now.date(), start_time=future_time_today)
        self.assertTrue(started.has_started())
        self.assertFalse(not_started.has_started())

    def test_mark_attendance_rejects_future_session(self):
        session = make_session(self.student, date.today() + timedelta(days=1))
        with self.assertRaises(ValueError):
            session.mark_attendance(Attendance.Status.PRESENT)

    def test_mark_attendance_creates_for_past_session(self):
        session = make_session(self.student, date.today() - timedelta(days=1))
        result = session.mark_attendance(Attendance.Status.PRESENT)
        self.assertIsNone(result["warning"])
        self.assertEqual(result["attendance"].status, Attendance.Status.PRESENT)
        self.assertTrue(result["attendance"].is_billable)

    def test_mark_attendance_updates_existing(self):
        session = make_session(self.student, date.today() - timedelta(days=1))
        session.mark_attendance(Attendance.Status.PRESENT)
        result = session.mark_attendance(Attendance.Status.ABSENT)
        self.assertEqual(Attendance.objects.filter(session=session).count(), 1)
        self.assertEqual(result["attendance"].status, Attendance.Status.ABSENT)
        self.assertFalse(result["attendance"].is_billable)

    def test_mark_attendance_warns_when_month_already_reported(self):
        session_date = date.today() - timedelta(days=1)
        session = make_session(self.student, session_date)
        MonthlyReport.objects.create(
            student=self.student,
            month=session_date.month,
            year=session_date.year,
            total_sessions=0,
            total_amount=Decimal("0"),
            file_url="http://example.com/r.pdf",
        )
        result = session.mark_attendance(Attendance.Status.PRESENT)
        self.assertIsNotNone(result["warning"])

    def test_pending_attendance_only_includes_started_without_attendance(self):
        started_no_attendance = make_session(self.student, date.today() - timedelta(days=1))
        started_with_attendance = make_session(self.student, date.today() - timedelta(days=2))
        Attendance.objects.create(session=started_with_attendance, status=Attendance.Status.PRESENT)
        not_started = make_session(self.student, date.today() + timedelta(days=1))

        pending_ids = set(Session.objects.pending_attendance().values_list("id", flat=True))
        self.assertIn(started_no_attendance.id, pending_ids)
        self.assertNotIn(started_with_attendance.id, pending_ids)
        self.assertNotIn(not_started.id, pending_ids)


class SessionAPITests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="teacher1", password="pass12345")
        self.client.force_authenticate(user=self.user)
        self.student = make_student()

    def test_unauthenticated_requests_are_rejected(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get("/api/sessions/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_filters_by_student(self):
        other_student = make_student(name="Tran Thi B")
        s1 = make_session(self.student, date.today())
        make_session(other_student, date.today())
        resp = self.client.get(f"/api/sessions/?student={self.student.id}")
        ids = [row["id"] for row in resp.data]
        self.assertEqual(ids, [str(s1.id)])

    def test_list_filters_by_date_range(self):
        make_session(self.student, date(2024, 1, 1))
        s2 = make_session(self.student, date(2024, 6, 1))
        make_session(self.student, date(2024, 12, 1))
        resp = self.client.get("/api/sessions/?date_from=2024-05-01&date_to=2024-07-01")
        ids = [row["id"] for row in resp.data]
        self.assertEqual(ids, [str(s2.id)])

    def test_list_pending_true_returns_only_pending(self):
        pending = make_session(self.student, date.today() - timedelta(days=1))
        attended = make_session(self.student, date.today() - timedelta(days=2))
        Attendance.objects.create(session=attended, status=Attendance.Status.PRESENT)
        resp = self.client.get("/api/sessions/?pending=true")
        ids = [row["id"] for row in resp.data]
        self.assertEqual(ids, [str(pending.id)])

    def test_mark_attendance_success(self):
        session = make_session(self.student, date.today() - timedelta(days=1))
        resp = self.client.post(
            f"/api/sessions/{session.id}/mark-attendance/", {"status": "present"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertEqual(resp.data["status"], "present")
        self.assertTrue(resp.data["is_billable"])
        self.assertNotIn("warning", resp.data)

    def test_mark_attendance_rejects_future_session(self):
        session = make_session(self.student, date.today() + timedelta(days=1))
        resp = self.client.post(
            f"/api/sessions/{session.id}/mark-attendance/", {"status": "present"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mark_attendance_invalid_status(self):
        session = make_session(self.student, date.today() - timedelta(days=1))
        resp = self.client.post(
            f"/api/sessions/{session.id}/mark-attendance/", {"status": "late"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mark_attendance_correction_includes_warning_when_month_reported(self):
        session_date = date.today() - timedelta(days=1)
        session = make_session(self.student, session_date)
        session.mark_attendance("present")
        MonthlyReport.objects.create(
            student=self.student,
            month=session_date.month,
            year=session_date.year,
            total_sessions=1,
            total_amount=Decimal("200000"),
            file_url="http://example.com/r.pdf",
        )
        resp = self.client.post(
            f"/api/sessions/{session.id}/mark-attendance/", {"status": "absent"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("warning", resp.data)

    def test_bulk_mark_attendance_mixed_results(self):
        ok_session = make_session(self.student, date.today() - timedelta(days=1))
        future_session = make_session(self.student, date.today() + timedelta(days=1))
        resp = self.client.post(
            "/api/sessions/bulk-mark-attendance/",
            [
                {"session": str(ok_session.id), "status": "present"},
                {"session": str(future_session.id), "status": "present"},
                {"session": "00000000-0000-0000-0000-000000000099", "status": "present"},
            ],
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        results = {row["session"]: row for row in resp.data}
        self.assertTrue(results[str(ok_session.id)]["ok"])
        self.assertFalse(results[str(future_session.id)]["ok"])
        self.assertFalse(results["00000000-0000-0000-0000-000000000099"]["ok"])

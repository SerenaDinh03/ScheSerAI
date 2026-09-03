from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.attendance.models import Attendance
from apps.billing.models import MonthlyReport
from apps.scheduling.models import Schedule, Session
from apps.teacher.models import Teacher

from .models import Student


def make_student(**kwargs):
    defaults = {
        "teacher": Teacher.load(),
        "name": "Nguyen Van A",
        "start_date": date(2024, 1, 1),
        "price_per_session": Decimal("200000"),
    }
    defaults.update(kwargs)
    return Student.objects.create(**defaults)


class StudentModelTests(TestCase):
    def test_age_none_when_no_dob(self):
        student = make_student(dob=None)
        self.assertIsNone(student.age)

    def test_age_before_and_after_birthday(self):
        today = date.today()
        not_yet_birthday = date(today.year - 10, today.month, today.day) + timedelta(days=1)
        already_had_birthday = date(today.year - 10, today.month, today.day) - timedelta(days=1)
        s1 = make_student(dob=not_yet_birthday, name="A")
        s2 = make_student(dob=already_had_birthday, name="B")
        self.assertEqual(s1.age, 9)
        self.assertEqual(s2.age, 10)

    def test_has_related_data_false_for_fresh_student(self):
        student = make_student()
        self.assertFalse(student.has_related_data())

    def test_has_related_data_true_with_schedule(self):
        student = make_student()
        Schedule.objects.create(
            student=student, day_of_week=0, start_time="18:00", end_time="19:00"
        )
        self.assertTrue(student.has_related_data())

    def test_has_related_data_true_with_session(self):
        student = make_student()
        Session.objects.create(
            student=student,
            session_date=date.today(),
            start_time="18:00",
            end_time="19:00",
        )
        self.assertTrue(student.has_related_data())

    def test_has_related_data_true_with_monthly_report(self):
        student = make_student()
        MonthlyReport.objects.create(
            student=student,
            month=1,
            year=2024,
            total_sessions=1,
            total_amount=Decimal("200000"),
            file_url="http://example.com/r.pdf",
        )
        self.assertTrue(student.has_related_data())


class StudentAPITests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="teacher1", password="pass12345")
        self.client.force_authenticate(user=self.user)

    def test_unauthenticated_requests_are_rejected(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get("/api/students/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # US 2.1
    def test_create_student_success(self):
        resp = self.client.post(
            "/api/students/",
            {
                "name": "Nguyen Van A",
                "dob": "2012-05-01",
                "start_date": "2024-01-01",
                "price_per_session": 200000,
                "note": "",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        student = Student.objects.get()
        self.assertEqual(student.status, Student.Status.ACTIVE)
        self.assertEqual(student.teacher, Teacher.load())

    def test_create_student_rejects_blank_name(self):
        resp = self.client.post(
            "/api/students/",
            {"name": "", "start_date": "2024-01-01", "price_per_session": 200000},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_student_rejects_zero_price(self):
        resp = self.client.post(
            "/api/students/",
            {"name": "A", "start_date": "2024-01-01", "price_per_session": 0},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_student_rejects_negative_price(self):
        resp = self.client.post(
            "/api/students/",
            {"name": "A", "start_date": "2024-01-01", "price_per_session": -100},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_student_ignores_client_supplied_teacher_and_status(self):
        resp = self.client.post(
            "/api/students/",
            {
                "name": "A",
                "start_date": "2024-01-01",
                "price_per_session": 200000,
                "status": "inactive",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        student = Student.objects.get()
        self.assertEqual(student.status, Student.Status.ACTIVE)

    # US 2.2
    def test_list_defaults_to_active_only(self):
        make_student(name="Active One", status=Student.Status.ACTIVE)
        make_student(name="Inactive One", status=Student.Status.INACTIVE)
        resp = self.client.get("/api/students/")
        names = [s["name"] for s in resp.data]
        self.assertIn("Active One", names)
        self.assertNotIn("Inactive One", names)

    def test_list_status_query_param_returns_inactive(self):
        make_student(name="Inactive One", status=Student.Status.INACTIVE)
        resp = self.client.get("/api/students/?status=inactive")
        names = [s["name"] for s in resp.data]
        self.assertIn("Inactive One", names)

    def test_list_search_by_name(self):
        make_student(name="Nguyen Van A")
        make_student(name="Tran Thi B")
        resp = self.client.get("/api/students/?search=Nguyen")
        names = [s["name"] for s in resp.data]
        self.assertEqual(names, ["Nguyen Van A"])

    def test_list_response_shape(self):
        make_student(name="A", dob=date(2010, 1, 1))
        resp = self.client.get("/api/students/")
        row = resp.data[0]
        self.assertEqual(set(row.keys()), {"id", "name", "age", "price_per_session", "status"})

    # US 2.3
    def test_retrieve_detail_includes_related_data(self):
        student = make_student()
        Schedule.objects.create(
            student=student, day_of_week=1, start_time="18:00", end_time="19:00", is_active=False
        )
        today = timezone.localdate()
        session_this_month = Session.objects.create(
            student=student, session_date=today, start_time="18:00", end_time="19:00"
        )
        Attendance.objects.create(session=session_this_month, status=Attendance.Status.PRESENT)

        last_month = today.replace(day=1) - timedelta(days=1)
        session_last_month = Session.objects.create(
            student=student, session_date=last_month, start_time="18:00", end_time="19:00"
        )
        Attendance.objects.create(session=session_last_month, status=Attendance.Status.PRESENT)

        resp = self.client.get(f"/api/students/{student.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["schedules"]), 1)
        self.assertEqual(resp.data["schedules"][0]["is_active"], False)
        self.assertEqual(len(resp.data["recent_attendance"]), 2)
        self.assertEqual(resp.data["sessions_this_month_count"], 1)

    # US 2.4
    def test_update_allows_name_dob_note(self):
        student = make_student()
        resp = self.client.patch(
            f"/api/students/{student.id}/", {"note": "ghi chu moi"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        student.refresh_from_db()
        self.assertEqual(student.note, "ghi chu moi")

    def test_update_rejects_price_per_session(self):
        student = make_student()
        resp = self.client.patch(
            f"/api/students/{student.id}/", {"price_per_session": 999999}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_rejects_status(self):
        student = make_student()
        resp = self.client.patch(
            f"/api/students/{student.id}/", {"status": "inactive"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_start_date_no_confirmation_needed_when_no_related_data(self):
        student = make_student()
        resp = self.client.patch(
            f"/api/students/{student.id}/", {"start_date": "2024-02-01"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)

    def test_update_start_date_requires_confirmation_when_related_data_exists(self):
        student = make_student()
        Schedule.objects.create(
            student=student, day_of_week=0, start_time="18:00", end_time="19:00"
        )
        resp = self.client.patch(
            f"/api/students/{student.id}/", {"start_date": "2024-02-01"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(resp.data["requires_confirmation"])
        student.refresh_from_db()
        self.assertEqual(student.start_date, date(2024, 1, 1))

        resp2 = self.client.patch(
            f"/api/students/{student.id}/",
            {"start_date": "2024-02-01", "confirm": True},
            format="json",
        )
        self.assertEqual(resp2.status_code, status.HTTP_200_OK, resp2.data)
        student.refresh_from_db()
        self.assertEqual(student.start_date, date(2024, 2, 1))

    # US 2.5
    @patch("apps.scheduling.calendar_sync.delete_calendar_event")
    def test_deactivate_sets_status_and_deletes_future_sessions_without_attendance(self, mock_delete):
        student = make_student()
        today = timezone.localdate()
        future_no_attendance = Session.objects.create(
            student=student,
            session_date=today + timedelta(days=7),
            start_time="18:00",
            end_time="19:00",
            google_event_id="evt-1",
        )
        future_with_attendance = Session.objects.create(
            student=student,
            session_date=today + timedelta(days=1),
            start_time="18:00",
            end_time="19:00",
        )
        Attendance.objects.create(session=future_with_attendance, status=Attendance.Status.PRESENT)
        past_session = Session.objects.create(
            student=student,
            session_date=today - timedelta(days=7),
            start_time="18:00",
            end_time="19:00",
        )

        resp = self.client.post(f"/api/students/{student.id}/deactivate/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertEqual(resp.data["status"], Student.Status.INACTIVE)
        self.assertEqual(resp.data["deleted_sessions_count"], 1)

        student.refresh_from_db()
        self.assertEqual(student.status, Student.Status.INACTIVE)
        self.assertFalse(Session.objects.filter(pk=future_no_attendance.pk).exists())
        self.assertTrue(Session.objects.filter(pk=future_with_attendance.pk).exists())
        self.assertTrue(Session.objects.filter(pk=past_session.pk).exists())
        mock_delete.assert_called_once_with("evt-1")

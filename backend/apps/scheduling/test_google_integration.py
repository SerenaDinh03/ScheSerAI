from datetime import date, datetime, time
from decimal import Decimal
from io import StringIO
from unittest.mock import MagicMock, patch

import httplib2
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from googleapiclient.errors import HttpError
from rest_framework import status
from rest_framework.test import APITestCase

from apps.students.models import Student
from apps.teacher.google_client import GoogleNotConnectedError
from apps.teacher.models import Teacher

from . import calendar_sync
from .google_sync import poll_google_calendar
from .models import Schedule, Session


def make_student(**kwargs):
    defaults = {
        "teacher": Teacher.load(),
        "name": "Nguyen Van A",
        "start_date": date(2024, 1, 1),
        "price_per_session": Decimal("200000"),
    }
    defaults.update(kwargs)
    return Student.objects.create(**defaults)


def http_error(status_code):
    return HttpError(httplib2.Response({"status": status_code}), b"error", uri="http://x")


class ScheduleGenerateSessionsTests(TestCase):
    def setUp(self):
        self.student = make_student()

    @patch("apps.scheduling.calendar_sync.create_calendar_event", return_value="")
    def test_generates_correct_number_of_sessions_on_right_weekday(self, mock_create):
        schedule = Schedule.objects.create(
            student=self.student, day_of_week=2, start_time=time(18, 0), end_time=time(19, 0)
        )
        created = schedule.generate_sessions(weeks_ahead=4)
        self.assertEqual(len(created), 4)
        for session in created:
            self.assertEqual(session.session_date.weekday(), 2)
        dates = sorted(s.session_date for s in created)
        self.assertEqual((dates[1] - dates[0]).days, 7)

    @patch("apps.scheduling.calendar_sync.create_calendar_event", return_value="")
    def test_skips_already_existing_dates_on_rerun(self, mock_create):
        schedule = Schedule.objects.create(
            student=self.student, day_of_week=0, start_time=time(18, 0), end_time=time(19, 0)
        )
        schedule.generate_sessions(weeks_ahead=3)
        self.assertEqual(mock_create.call_count, 3)
        created_again = schedule.generate_sessions(weeks_ahead=3)
        self.assertEqual(len(created_again), 0)
        self.assertEqual(Session.objects.filter(schedule=schedule).count(), 3)

    def test_does_not_generate_when_inactive(self):
        schedule = Schedule.objects.create(
            student=self.student,
            day_of_week=0,
            start_time=time(18, 0),
            end_time=time(19, 0),
            is_active=False,
        )
        created = schedule.generate_sessions()
        self.assertEqual(created, [])
        self.assertEqual(Session.objects.filter(schedule=schedule).count(), 0)

    @patch("apps.scheduling.calendar_sync.create_calendar_event", return_value="evt-123")
    def test_stores_google_event_id_when_calendar_connected(self, mock_create):
        schedule = Schedule.objects.create(
            student=self.student, day_of_week=0, start_time=time(18, 0), end_time=time(19, 0)
        )
        created = schedule.generate_sessions(weeks_ahead=1)
        self.assertEqual(created[0].google_event_id, "evt-123")


class CalendarSyncTests(TestCase):
    def setUp(self):
        self.student = make_student()
        self.session = Session.objects.create(
            student=self.student,
            session_date=date(2026, 1, 1),
            start_time=time(18, 0),
            end_time=time(19, 0),
        )
        self.teacher = Teacher.load()

    @patch("apps.teacher.google_client.get_calendar_service", side_effect=GoogleNotConnectedError())
    def test_create_returns_empty_when_not_connected(self, mock_get_service):
        self.assertEqual(calendar_sync.create_calendar_event(self.session), "")

    @patch("apps.teacher.google_client.get_calendar_service")
    def test_create_calls_insert_with_correct_calendar_and_body(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.events.return_value.insert.return_value.execute.return_value = {
            "id": "evt-abc"
        }
        mock_get_service.return_value = mock_service
        self.teacher.google_calendar_id = "teacher@gmail.com"
        self.teacher.save()

        event_id = calendar_sync.create_calendar_event(self.session)

        self.assertEqual(event_id, "evt-abc")
        _, kwargs = mock_service.events.return_value.insert.call_args
        self.assertEqual(kwargs["calendarId"], "teacher@gmail.com")
        self.assertIn(self.student.name, kwargs["body"]["summary"])
        self.teacher.refresh_from_db()
        self.assertIsNotNone(self.teacher.google_last_sync_at)

    @patch("apps.teacher.google_client.get_calendar_service")
    def test_create_records_error_on_http_error(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.events.return_value.insert.return_value.execute.side_effect = http_error(500)
        mock_get_service.return_value = mock_service

        event_id = calendar_sync.create_calendar_event(self.session)

        self.assertEqual(event_id, "")
        self.teacher.refresh_from_db()
        self.assertNotEqual(self.teacher.google_last_sync_error, "")

    @patch("apps.teacher.google_client.get_calendar_service")
    def test_update_calls_update_with_event_id(self, mock_get_service):
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        calendar_sync.update_calendar_event("evt-xyz", self.session)

        _, kwargs = mock_service.events.return_value.update.call_args
        self.assertEqual(kwargs["eventId"], "evt-xyz")

    @patch("apps.teacher.google_client.get_calendar_service", side_effect=GoogleNotConnectedError())
    def test_update_is_noop_when_not_connected(self, mock_get_service):
        calendar_sync.update_calendar_event("evt-xyz", self.session)  # không raise

    @patch("apps.teacher.google_client.get_calendar_service")
    def test_delete_calls_delete_with_event_id(self, mock_get_service):
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        calendar_sync.delete_calendar_event("evt-xyz")

        _, kwargs = mock_service.events.return_value.delete.call_args
        self.assertEqual(kwargs["eventId"], "evt-xyz")

    @patch("apps.teacher.google_client.get_calendar_service")
    def test_delete_treats_404_as_success_not_error(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.events.return_value.delete.return_value.execute.side_effect = http_error(404)
        mock_get_service.return_value = mock_service

        calendar_sync.delete_calendar_event("evt-already-gone")

        self.teacher.refresh_from_db()
        self.assertEqual(self.teacher.google_last_sync_error, "")


class GoogleSyncPollTests(TestCase):
    def setUp(self):
        self.student = make_student()
        self.teacher = Teacher.load()
        self.session = Session.objects.create(
            student=self.student,
            session_date=date(2026, 1, 1),
            start_time=time(18, 0),
            end_time=time(19, 0),
            google_event_id="evt-1",
        )

    @patch("apps.teacher.google_client.get_calendar_service", side_effect=GoogleNotConnectedError())
    def test_skips_when_not_connected(self, mock_get_service):
        result = poll_google_calendar()
        self.assertEqual(result, {"skipped": "not_connected"})

    @patch("apps.teacher.google_client.get_calendar_service")
    def test_updates_session_when_event_time_changed(self, mock_get_service):
        mock_service = MagicMock()
        new_start = timezone.make_aware(datetime.combine(date(2026, 1, 8), time(20, 0)))
        new_end = timezone.make_aware(datetime.combine(date(2026, 1, 8), time(21, 0)))
        mock_service.events.return_value.list.return_value.execute.return_value = {
            "items": [
                {
                    "id": "evt-1",
                    "status": "confirmed",
                    "start": {"dateTime": new_start.isoformat()},
                    "end": {"dateTime": new_end.isoformat()},
                }
            ],
            "nextSyncToken": "sync-token-1",
        }
        mock_get_service.return_value = mock_service

        result = poll_google_calendar()

        self.session.refresh_from_db()
        self.assertEqual(self.session.session_date, date(2026, 1, 8))
        self.assertEqual(self.session.start_time, time(20, 0))
        self.assertEqual(self.session.status, Session.Status.RESCHEDULED)
        self.assertEqual(result["updated"], 1)
        self.teacher.refresh_from_db()
        self.assertEqual(self.teacher.google_sync_token, "sync-token-1")

    @patch("apps.teacher.google_client.get_calendar_service")
    def test_deletes_session_when_event_cancelled(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.events.return_value.list.return_value.execute.return_value = {
            "items": [{"id": "evt-1", "status": "cancelled"}],
            "nextSyncToken": "sync-token-2",
        }
        mock_get_service.return_value = mock_service

        result = poll_google_calendar()

        self.assertFalse(Session.objects.filter(pk=self.session.pk).exists())
        self.assertEqual(result["deleted"], 1)

    @patch("apps.teacher.google_client.get_calendar_service")
    def test_ignores_events_with_no_matching_session(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.events.return_value.list.return_value.execute.return_value = {
            "items": [{"id": "evt-unrelated", "status": "confirmed"}],
            "nextSyncToken": "sync-token-3",
        }
        mock_get_service.return_value = mock_service

        result = poll_google_calendar()

        self.assertEqual(result, {"updated": 0, "deleted": 0})
        self.session.refresh_from_db()  # vẫn còn nguyên, không lỗi

    @patch("apps.teacher.google_client.get_calendar_service")
    def test_expired_sync_token_triggers_full_resync(self, mock_get_service):
        self.teacher.google_sync_token = "expired-token"
        self.teacher.save()

        mock_service = MagicMock()
        call_state = {"count": 0}

        def list_side_effect(**kwargs):
            call_state["count"] += 1
            if call_state["count"] == 1:
                mock_exec = MagicMock()
                mock_exec.execute.side_effect = http_error(410)
                return mock_exec
            mock_exec = MagicMock()
            mock_exec.execute.return_value = {"items": [], "nextSyncToken": "fresh-token"}
            return mock_exec

        mock_service.events.return_value.list.side_effect = list_side_effect
        mock_get_service.return_value = mock_service

        result = poll_google_calendar()

        self.teacher.refresh_from_db()
        self.assertEqual(self.teacher.google_sync_token, "fresh-token")
        self.assertEqual(result, {"updated": 0, "deleted": 0})


class ScheduleAPITests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="teacher1", password="pass12345")
        self.client.force_authenticate(user=self.user)
        self.student = make_student()

    @patch("apps.scheduling.calendar_sync.create_calendar_event", return_value="")
    def test_create_schedule_generates_sessions(self, mock_create):
        resp = self.client.post(
            "/api/schedules/",
            {
                "student": str(self.student.id),
                "day_of_week": 1,
                "start_time": "18:00",
                "end_time": "19:00",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        schedule_id = resp.data["id"]
        self.assertTrue(Session.objects.filter(schedule_id=schedule_id).exists())

    @patch("apps.scheduling.calendar_sync.create_calendar_event", return_value="")
    def test_pause_stops_generation_resume_regenerates(self, mock_create):
        schedule = Schedule.objects.create(
            student=self.student, day_of_week=0, start_time=time(18, 0), end_time=time(19, 0)
        )
        resp = self.client.post(f"/api/schedules/{schedule.id}/pause/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["is_active"])
        self.assertEqual(Session.objects.filter(schedule=schedule).count(), 0)

        resp = self.client.post(f"/api/schedules/{schedule.id}/resume/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["is_active"])
        self.assertGreater(Session.objects.filter(schedule=schedule).count(), 0)


class BootstrapScheduledJobsCommandTests(TestCase):
    def test_command_registers_periodic_jobs(self):
        from django_q.models import Schedule as QSchedule

        call_command("bootstrap_scheduled_jobs", stdout=StringIO())

        self.assertTrue(QSchedule.objects.filter(name="generate_upcoming_sessions").exists())
        self.assertTrue(QSchedule.objects.filter(name="sync_google_calendar").exists())

        # idempotent - chạy lại không tạo trùng
        call_command("bootstrap_scheduled_jobs", stdout=StringIO())
        self.assertEqual(QSchedule.objects.filter(name="generate_upcoming_sessions").count(), 1)

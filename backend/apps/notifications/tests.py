from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.teacher.models import Teacher

from .models import Notification


class NotificationAPITests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="teacher1", password="pass12345")
        self.client.force_authenticate(user=self.user)
        self.teacher = Teacher.load()

    def test_unauthenticated_requests_are_rejected(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get("/api/notifications/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_returns_newest_first(self):
        n1 = Notification.objects.create(teacher=self.teacher, message="cu")
        n2 = Notification.objects.create(teacher=self.teacher, message="moi")
        resp = self.client.get("/api/notifications/")
        ids = [row["id"] for row in resp.data]
        self.assertEqual(ids, [str(n2.id), str(n1.id)])

    def test_unread_count(self):
        Notification.objects.create(teacher=self.teacher, message="a", is_read=False)
        Notification.objects.create(teacher=self.teacher, message="b", is_read=False)
        Notification.objects.create(teacher=self.teacher, message="c", is_read=True)
        resp = self.client.get("/api/notifications/unread-count/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 2)

    def test_mark_read(self):
        n = Notification.objects.create(teacher=self.teacher, message="a")
        resp = self.client.post(f"/api/notifications/{n.id}/mark-read/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        n.refresh_from_db()
        self.assertTrue(n.is_read)

    def test_mark_all_read(self):
        Notification.objects.create(teacher=self.teacher, message="a")
        Notification.objects.create(teacher=self.teacher, message="b")
        resp = self.client.post("/api/notifications/mark-all-read/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["updated"], 2)
        self.assertEqual(Notification.objects.filter(is_read=False).count(), 0)

from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlsplit

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from . import crypto
from .models import Teacher


class CryptoTests(TestCase):
    def test_encrypt_decrypt_roundtrip(self):
        ciphertext = crypto.encrypt("my-refresh-token")
        self.assertNotEqual(ciphertext, "my-refresh-token")
        self.assertEqual(crypto.decrypt(ciphertext), "my-refresh-token")

    def test_encrypt_empty_string_returns_empty(self):
        self.assertEqual(crypto.encrypt(""), "")

    def test_decrypt_empty_string_returns_empty(self):
        self.assertEqual(crypto.decrypt(""), "")

    def test_decrypt_invalid_token_returns_empty(self):
        self.assertEqual(crypto.decrypt("not-a-valid-fernet-token"), "")


class TeacherModelTests(TestCase):
    def test_set_get_refresh_token_roundtrip_stores_ciphertext(self):
        teacher = Teacher.load()
        teacher.set_google_refresh_token("real-refresh-token")
        teacher.save()
        self.assertNotEqual(teacher.google_refresh_token, "real-refresh-token")
        self.assertEqual(teacher.get_google_refresh_token(), "real-refresh-token")

    def test_is_google_connected(self):
        teacher = Teacher.load()
        self.assertFalse(teacher.is_google_connected)
        teacher.set_google_refresh_token("tok")
        teacher.save()
        self.assertTrue(teacher.is_google_connected)

    def test_disconnect_google_clears_all_fields(self):
        teacher = Teacher.load()
        teacher.set_google_refresh_token("tok")
        teacher.google_calendar_id = "primary"
        teacher.google_account_email = "teacher@gmail.com"
        teacher.google_sync_token = "sync-tok"
        teacher.google_last_sync_error = "some error"
        teacher.save()

        teacher.disconnect_google()

        teacher.refresh_from_db()
        self.assertFalse(teacher.is_google_connected)
        self.assertEqual(teacher.google_calendar_id, "")
        self.assertEqual(teacher.google_account_email, "")
        self.assertEqual(teacher.google_sync_token, "")
        self.assertEqual(teacher.google_last_sync_error, "")


class GoogleOAuthAPITests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="teacher1", password="pass12345")
        self.client.force_authenticate(user=self.user)

    def test_connect_redirects_to_google_authorization_url(self):
        resp = self.client.get("/api/google/connect/")
        self.assertEqual(resp.status_code, status.HTTP_302_FOUND)
        self.assertIn("accounts.google.com", resp.url)

    def test_status_when_not_connected(self):
        resp = self.client.get("/api/google/status/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["connected"])

    def test_callback_rejects_error_param(self):
        resp = self.client.get("/api/google/callback/?error=access_denied")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_callback_rejects_missing_or_mismatched_state(self):
        resp = self.client.get("/api/google/callback/?code=abc&state=wrong")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.teacher.views.google_client.fetch_account_email")
    @patch("apps.teacher.views.google_client.exchange_code")
    def test_callback_success_stores_encrypted_token_and_email(self, mock_exchange, mock_email):
        # Đi qua /connect/ trước để session có sẵn state hợp lệ.
        connect_resp = self.client.get("/api/google/connect/")
        auth_url = connect_resp.url
        state = parse_qs(urlsplit(auth_url).query).get("state", [None])[0]

        mock_credentials = MagicMock()
        mock_credentials.refresh_token = "real-refresh-token"
        mock_exchange.return_value = mock_credentials
        mock_email.return_value = "teacher@gmail.com"

        resp = self.client.get(f"/api/google/callback/?code=fake-code&state={state}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertTrue(resp.data["connected"])
        self.assertEqual(resp.data["email"], "teacher@gmail.com")

        teacher = Teacher.load()
        self.assertTrue(teacher.is_google_connected)
        self.assertEqual(teacher.get_google_refresh_token(), "real-refresh-token")
        self.assertEqual(teacher.google_calendar_id, "primary")

        status_resp = self.client.get("/api/google/status/")
        self.assertTrue(status_resp.data["connected"])

    @patch("apps.teacher.views.google_client.exchange_code")
    def test_callback_without_refresh_token_returns_400(self, mock_exchange):
        connect_resp = self.client.get("/api/google/connect/")
        auth_url = connect_resp.url
        state = parse_qs(urlsplit(auth_url).query).get("state", [None])[0]

        mock_credentials = MagicMock()
        mock_credentials.refresh_token = None
        mock_exchange.return_value = mock_credentials

        resp = self.client.get(f"/api/google/callback/?code=fake-code&state={state}")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_disconnect_clears_connection(self):
        teacher = Teacher.load()
        teacher.set_google_refresh_token("tok")
        teacher.save()

        resp = self.client.post("/api/google/disconnect/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        teacher.refresh_from_db()
        self.assertFalse(teacher.is_google_connected)

    def test_unauthenticated_status_is_rejected(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get("/api/google/status/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

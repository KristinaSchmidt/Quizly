from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase


class AuthenticationTests(APITestCase):
    def test_register_login_refresh_logout(self):
        register = self.client.post(
            "/api/register/",
            {
                "username": "tester",
                "password": "Strong1",
                "confirmed_password": "Strong1",
                "email": "tester@example.com",
            },
            format="json",
        )
        self.assertEqual(register.status_code, status.HTTP_201_CREATED)

        login = self.client.post(
            "/api/login/",
            {"username": "tester", "password": "Strong1"},
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", login.cookies)
        self.assertTrue(login.cookies["access_token"]["httponly"])

        refresh = self.client.post("/api/token/refresh/", {}, format="json")
        self.assertEqual(refresh.status_code, status.HTTP_200_OK)

        logout = self.client.post("/api/logout/", {}, format="json")
        self.assertEqual(logout.status_code, status.HTTP_200_OK)

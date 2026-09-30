from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Question, Quiz


class QuizApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("owner", password="Strong1")
        self.other = User.objects.create_user("other", password="Strong1")
        login = self.client.post(
            "/api/login/",
            {"username": "owner", "password": "Strong1"},
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)

    def make_quiz(self, owner=None):
        quiz = Quiz.objects.create(
            user=owner or self.user,
            title="Quiz Title",
            description="Quiz Description",
            video_url="https://www.youtube.com/watch?v=example",
        )
        Question.objects.create(
            quiz=quiz,
            question_title="Question 1",
            question_options=["A", "B", "C", "D"],
            answer="A",
        )
        return quiz

    def test_list_contains_only_owned_quizzes(self):
        self.make_quiz()
        self.make_quiz(self.other)
        response = self.client.get("/api/quizzes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_detail_update_and_delete(self):
        quiz = self.make_quiz()
        detail = self.client.get(f"/api/quizzes/{quiz.id}/")
        self.assertEqual(detail.status_code, status.HTTP_200_OK)

        updated = self.client.patch(
            f"/api/quizzes/{quiz.id}/",
            {"title": "Changed"},
            format="json",
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.data["title"], "Changed")

        deleted = self.client.delete(f"/api/quizzes/{quiz.id}/")
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)

    def test_other_users_quiz_is_not_available(self):
        quiz = self.make_quiz(self.other)
        response = self.client.get(f"/api/quizzes/{quiz.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("quizzes.views.create_quiz_from_url")
    def test_create_quiz_endpoint(self, mocked_create):
        mocked_create.return_value = self.make_quiz()
        response = self.client.post(
            "/api/quizzes/",
            {"url": "https://www.youtube.com/watch?v=example"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

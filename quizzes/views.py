from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .functions import create_quiz_from_url
from .models import Quiz
from .serializers import QuizSerializer
from .utils import get_owned_quiz


class QuizListCreateView(APIView):
    """List the user's quizzes or create one from a YouTube URL."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        quizzes = Quiz.objects.filter(user=request.user)
        quizzes = quizzes.prefetch_related("questions")
        serializer = QuizSerializer(quizzes, many=True)
        return Response(serializer.data)

    def post(self, request):
        url = request.data.get("url", "").strip()
        if not url:
            return Response(
                {"detail": "URL is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return self.create_quiz(request, url)

    def create_quiz(self, request, url):
        try:
            quiz = create_quiz_from_url(request.user, url)
        except ValueError as error:
            return Response(
                {"detail": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return Response(
                {"detail": "Quiz generation failed."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(
            QuizSerializer(quiz).data,
            status=status.HTTP_201_CREATED,
        )


class QuizDetailView(APIView):
    """Retrieve, update or delete one owned quiz."""

    permission_classes = [IsAuthenticated]

    def get_quiz(self, request, quiz_id):
        quiz, error_status = get_owned_quiz(request.user, quiz_id)
        if error_status is None:
            return quiz, None
        detail = self.get_error_detail(error_status)
        return None, Response({"detail": detail}, status=error_status)

    def get_error_detail(self, error_status):
        if error_status == status.HTTP_403_FORBIDDEN:
            return "Forbidden."
        return "Quiz not found."

    def get(self, request, quiz_id):
        quiz, error = self.get_quiz(request, quiz_id)
        if error:
            return error
        return Response(QuizSerializer(quiz).data)

    def patch(self, request, quiz_id):
        quiz, error = self.get_quiz(request, quiz_id)
        if error:
            return error
        serializer = QuizSerializer(quiz, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, quiz_id):
        quiz, error = self.get_quiz(request, quiz_id)
        if error:
            return error
        quiz.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
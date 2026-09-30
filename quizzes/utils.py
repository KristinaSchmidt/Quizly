from rest_framework import status

from .models import Quiz


def get_owned_quiz(user, quiz_id):
    """Return a quiz and verify that it belongs to the current user."""
    quiz = Quiz.objects.filter(id=quiz_id).prefetch_related("questions").first()

    if quiz is None:
        return None, status.HTTP_404_NOT_FOUND

    if quiz.user != user:
        return None, status.HTTP_403_FORBIDDEN

    return quiz, None
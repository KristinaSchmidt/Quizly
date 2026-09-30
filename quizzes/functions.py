import json
import re
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import whisper
import yt_dlp
from django.conf import settings
from google import genai


YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com"}
VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")


def extract_video_id(url):
    """Extract a valid video ID from supported YouTube URLs."""
    parsed = urlparse(url)
    host = parsed.netloc.lower().split(":")[0]
    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]
    elif host in YOUTUBE_HOSTS:
        video_id = parse_qs(parsed.query).get("v", [""])[0]
    else:
        return ""
    return video_id if VIDEO_ID_PATTERN.fullmatch(video_id) else ""


def normalize_youtube_url(url):
    """Return the canonical YouTube watch URL."""
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError("Invalid YouTube URL.")
    return f"https://www.youtube.com/watch?v={video_id}"


def download_audio(url, directory):
    """Download the best available YouTube audio stream."""
    options = get_download_options(directory)
    try:
        with yt_dlp.YoutubeDL(options) as downloader:
            info = downloader.extract_info(url, download=True)
            return Path(downloader.prepare_filename(info))
    except yt_dlp.utils.DownloadError as error:
        raise ValueError("YouTube video could not be downloaded.") from error


def get_download_options(directory):
    """Return the yt-dlp configuration for audio downloads."""
    return {
        "format": "bestaudio/best",
        "outtmpl": str(Path(directory) / "audio.%(ext)s"),
        "quiet": True,
        "noplaylist": True,
    }


def transcribe_audio(audio_path):
    """Transcribe an audio file locally with Whisper."""
    model = whisper.load_model(settings.WHISPER_MODEL)
    result = model.transcribe(str(audio_path))
    return result["text"].strip()


def build_prompt(transcript):
    """Build the prompt for Gemini quiz generation."""
    return f"""
Generate a quiz from the transcript and return valid JSON only.

Required structure:
{{
  "title": "Concise title, maximum 150 characters",
  "description": "Summary, maximum 150 characters",
  "questions": [
    {{
      "question_title": "Question",
      "question_options": ["A", "B", "C", "D"],
      "answer": "One exact value from question_options"
    }}
  ]
}}

Requirements:
- Generate exactly 10 questions.
- Each question must have exactly 4 distinct options.
- Each answer must exactly match one option.
- Title and description must each be at most 150 characters.
- Do not include Markdown, comments or explanations.

Transcript:
{transcript}
""".strip()


def clean_json_output(text):
    """Remove optional Markdown fences from Gemini output."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def generate_quiz_data(transcript):
    """Generate and validate quiz data using Gemini."""
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured.")
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=build_prompt(transcript),
    )
    data = json.loads(clean_json_output(response.text))
    validate_quiz_data(data)
    return data


def validate_quiz_data(data):
    """Validate the complete generated quiz structure."""
    validate_quiz_text(data)
    questions = data.get("questions", [])
    if len(questions) != 10:
        raise ValueError("Gemini must return exactly 10 questions.")
    for question in questions:
        validate_question(question)


def validate_quiz_text(data):
    """Validate required quiz title and description."""
    title = data.get("title", "")
    description = data.get("description", "")
    if not title or len(title) > 150:
        raise ValueError("Title must contain 1 to 150 characters.")
    if not description or len(description) > 150:
        raise ValueError("Description must contain 1 to 150 characters.")


def validate_question(question):
    """Validate one generated quiz question."""
    options = question.get("question_options", [])
    if not question.get("question_title"):
        raise ValueError("Every question needs a title.")
    if len(options) != 4 or len(set(options)) != 4:
        raise ValueError("Each question needs 4 distinct options.")
    if question.get("answer") not in options:
        raise ValueError("The answer must be one of the options.")


def create_quiz_from_url(user, url):
    """Create and persist a quiz from a YouTube URL."""
    video_url = normalize_youtube_url(url)
    transcript = create_transcript(video_url)
    data = generate_quiz_data(transcript)
    return save_quiz(user, video_url, data)


def create_transcript(video_url):
    """Download and transcribe one YouTube video."""
    with tempfile.TemporaryDirectory() as directory:
        audio_path = download_audio(video_url, directory)
        return transcribe_audio(audio_path)


def save_quiz(user, video_url, data):
    """Persist a generated quiz and its questions."""
    from .models import Quiz

    quiz = Quiz.objects.create(
        user=user,
        title=data["title"],
        description=data["description"],
        video_url=video_url,
    )
    save_questions(quiz, data["questions"])
    return quiz


def save_questions(quiz, questions):
    """Persist all generated questions efficiently."""
    from .models import Question

    objects = [build_question(quiz, item) for item in questions]
    Question.objects.bulk_create(objects)


def build_question(quiz, item):
    """Build one unsaved Question instance."""
    from .models import Question

    return Question(
        quiz=quiz,
        question_title=item["question_title"],
        question_options=item["question_options"],
        answer=item["answer"],
    )
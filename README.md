# Quizly Backend

Django REST backend for the supplied Developer Akademie Quizly frontend.

## Implemented API

- `POST /api/register/`
- `POST /api/login/`
- `POST /api/logout/`
- `POST /api/token/refresh/`
- `POST /api/quizzes/`
- `GET /api/quizzes/`
- `GET /api/quizzes/{id}/`
- `PATCH /api/quizzes/{id}/`
- `DELETE /api/quizzes/{id}/`

Authentication uses JWT access and refresh tokens stored in HttpOnly cookies.
Protected API requests read the access token from the cookie.

Logout blacklists the refresh token and removes both authentication cookies.

## Quiz Generation

Quiz generation follows this pipeline:

1. Receive a YouTube URL.
2. Validate and normalize the YouTube URL.
3. Store the URL in the format `https://www.youtube.com/watch?v=VIDEO_ID`.
4. Download the audio with `yt-dlp` using `bestaudio/best`, `quiet=True` and `noplaylist=True`.
5. Transcribe the audio locally with OpenAI Whisper.
6. Send the transcript to Gemini Flash.
7. Remove optional Markdown JSON fences from the generated response.
8. Validate the generated quiz data.
9. Save the quiz and its questions to the database.

Each generated quiz contains:

- A title with a maximum length of 150 characters.
- A description with a maximum length of 150 characters.
- Exactly 10 questions.
- Exactly 4 distinct answer options per question.
- One correct answer that must be contained in the answer options.

## Requirements

Python 3.10+ is recommended.

**FFmpeg must be installed on the computer and available on PATH.**

Whisper and `yt-dlp` require FFmpeg for audio processing.

A Gemini API key is required for quiz generation.

Quiz generation uses the Gemini model configured through `GEMINI_MODEL`.
The current project configuration uses `gemini-3.5-flash`.

## Setup

Create a virtual environment:

```bash
python -m venv venv
```

### Windows

Activate the virtual environment:

```bash
venv\Scripts\activate
```

### macOS/Linux

Activate the virtual environment:

```bash
source venv/bin/activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and configure the environment variables:

```env
DJANGO_SECRET_KEY=your-secret-key
DEBUG=True
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-3.5-flash
WHISPER_MODEL=turbo
FRONTEND_ORIGIN=http://127.0.0.1:5500
```

Do not commit the `.env` file or real API keys to Git.

Run the database migrations:

```bash
python manage.py migrate
```

Create an admin user if needed:

```bash
python manage.py createsuperuser
```

Start the backend:

```bash
python manage.py runserver
```

The backend API is available at:

`http://127.0.0.1:8000/api/`

The supplied frontend normally runs with Live Server at:

`http://127.0.0.1:5500`

If the frontend uses another origin, update `FRONTEND_ORIGIN` in `.env`.

## Tests

Run the Django tests with:

```bash
python manage.py test
```

The Django system configuration can also be checked with:

```bash
python manage.py check
```

## Admin

The Django admin is available at:

`/admin/`

Quizzes can be managed through the Django admin.
The individual questions belonging to a quiz can also be viewed and edited.

## Authentication

JWT authentication uses two HttpOnly cookies:

- `access_token`
- `refresh_token`

The access token is used for protected API requests.

The refresh token is used to create a new access token through:

`POST /api/token/refresh/`

When a user logs out, the refresh token is blacklisted and both authentication cookies are removed.

## Security

For local development with `DEBUG=True`, authentication cookies use `Secure=False`.

When `DEBUG=False`, the project automatically enables secure authentication cookies.

The following files and values must never be committed to Git:

- `.env`
- Django secret keys
- Gemini API keys
- Authentication cookies or tokens

The repository contains `.env.example` only as a template and does not contain real credentials.
# Kobox Backend

FastAPI backend for the Kobox anime collection showcase project.

## Stack

- FastAPI
- Pydantic
- SQLAlchemy 2.x
- Alembic
- psycopg 3
- SQLite by default, PostgreSQL-compatible schema via `DATABASE_URL`

## Quick Start

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and adjust values if needed.
4. Run migrations:

```bash
alembic upgrade head
```

5. Start server:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## Environment Notes

- `CORS_ALLOW_ORIGINS` supports comma-separated or JSON array format.
- `UPLOADS_DIR` is the local directory for uploaded avatars.
- `UPLOADS_URL_PREFIX` is the static URL mount prefix (default `/uploads`).
- `ANILIST_API_URL` defaults to public AniList GraphQL endpoint and needs no API key.
- Supabase connection strings using `postgres://` or `postgresql://` are normalized to `postgresql+psycopg://`.
- For long-lived backend traffic, prefer Supabase direct connection or session pooler.
- If you must use the Supabase transaction pooler (`:6543`), the backend will switch to `NullPool` and disable prepared statements automatically.

## Supabase

This project can use Supabase as its managed PostgreSQL provider. See [SUPABASE_WORKTHROUGH.md](../markdown_set/SUPABASE_WORKTHROUGH.md) for:

- which connection mode to choose
- which database parameters to copy from the dashboard
- the current table design
- exact `.env` examples and migration steps

## New Endpoints

- `POST /api/me/avatar` (multipart form-data, `file`) uploads avatar and updates current user profile.
- Static files under `UPLOADS_DIR` are served at `UPLOADS_URL_PREFIX`.

## Smoke Test

Run minimum backend smoke coverage (settings/profile/upload/search):

```bash
python tests/smoke_api.py
```

## Seed Data

On startup, seed data is inserted when `SEED_ON_STARTUP=true` (default):

- Demo user: `demo@kobox.local`
- Password: `Demo1234!`
- Seed anime records + initial collections/favorites

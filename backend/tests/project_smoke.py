from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def _prepare_env() -> None:
    base_dir = Path(__file__).resolve().parent / ".tmp"
    base_dir.mkdir(parents=True, exist_ok=True)
    db_path = base_dir / "project-smoke.db"
    uploads_path = base_dir / "uploads"

    if db_path.exists():
        db_path.unlink()

    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    os.environ["SEED_ON_STARTUP"] = "true"
    os.environ["AUTO_CREATE_TABLES"] = "true"
    os.environ["UPLOADS_DIR"] = str(uploads_path)
    os.environ["UPLOADS_URL_PREFIX"] = "/uploads"
    os.environ["CORS_ALLOW_ORIGINS"] = "http://localhost:5173,http://127.0.0.1:5173"
    os.environ["APP_DEBUG"] = "false"


def _login(client: TestClient) -> dict[str, str]:
    login_resp = client.post(
        "/api/auth/login",
        json={"account": "demo@kobox.local", "password": "Demo1234!"},
    )
    assert login_resp.status_code == 200, login_resp.text
    login_data = login_resp.json()
    assert login_data["access_token"]
    assert login_data["refresh_token"]
    return login_data


def run_smoke() -> None:
    _prepare_env()

    from app.main import app
    from app.services.anime_service import AnimeService

    AnimeService._remote_cache.clear()
    AnimeService._source_cache.clear()
    AnimeService._search_remote_candidates = lambda self, **kwargs: []  # type: ignore[method-assign]

    with TestClient(app) as client:
        health_resp = client.get("/health")
        assert health_resp.status_code == 200, health_resp.text
        assert health_resp.json()["status"] == "ok"

        session = _login(client)
        refresh_resp = client.post("/api/auth/refresh", json={"refresh_token": session["refresh_token"]})
        assert refresh_resp.status_code == 200, refresh_resp.text
        session = refresh_resp.json()
        auth_headers = {"Authorization": f"Bearer {session['access_token']}"}

        settings_resp = client.get("/api/me/settings", headers=auth_headers)
        assert settings_resp.status_code == 200, settings_resp.text
        settings_data = settings_resp.json()
        assert settings_data["language"]

        update_settings_resp = client.put(
            "/api/me/settings",
            headers=auth_headers,
            json={
                "language": "en",
                "show_dynamic_background": False,
                "show_public_rank": True,
            },
        )
        assert update_settings_resp.status_code == 200, update_settings_resp.text
        assert update_settings_resp.json()["language"] == "en"

        profile_update_resp = client.put(
            "/api/me/profile",
            headers=auth_headers,
            json={
                "display_name": "Smoke Runner",
                "birthday": "2001-01-02",
                "bio": "Updated by project smoke.",
                "is_public": True,
            },
        )
        assert profile_update_resp.status_code == 200, profile_update_resp.text
        profile_data = profile_update_resp.json()
        assert profile_data["display_name"] == "Smoke Runner"
        assert profile_data["bio"] == "Updated by project smoke."

        me_resp = client.get("/api/me", headers=auth_headers)
        assert me_resp.status_code == 200, me_resp.text
        assert me_resp.json()["display_name"] == "Smoke Runner"

        search_headers = {"Accept-Language": "zh-CN", **auth_headers}
        search_resp = client.get(
            "/api/anime/search",
            headers=search_headers,
            params={"q": "芙莉莲", "page": 1, "page_size": 5},
        )
        assert search_resp.status_code == 200, search_resp.text
        search_data = search_resp.json()
        assert search_data["items"], "Expected local anime search results"
        first_anime = search_data["items"][0]
        assert "芙莉莲" in first_anime["title"]
        assert first_anime["source_id"]

        suggestions_resp = client.get(
            "/api/anime/search/suggestions",
            headers=search_headers,
            params={"q": "芙莉", "page": 1, "page_size": 5},
        )
        assert suggestions_resp.status_code == 200, suggestions_resp.text
        suggestions_data = suggestions_resp.json()
        assert suggestions_data["items"], "Expected search suggestions"
        assert any("芙莉莲" in item["title"] for item in suggestions_data["items"])

        add_resp = client.post(
            "/api/me/collections",
            headers=auth_headers,
            json={
                "source_id": first_anime["source_id"],
                "collection_status": "watching",
            },
        )
        assert add_resp.status_code == 201, add_resp.text
        added_item = add_resp.json()
        assert added_item["collection_status"] == "watching"
        assert added_item["anime"]["source_id"] == first_anime["source_id"]

        collections_resp = client.get("/api/me/collections", headers=search_headers)
        assert collections_resp.status_code == 200, collections_resp.text
        collections_data = collections_resp.json()
        assert collections_data["total"] >= 1
        assert any(item["anime"]["source_id"] == first_anime["source_id"] for item in collections_data["items"])

        public_profile_resp = client.get("/api/public/users/demo", headers={"Accept-Language": "zh-CN"})
        assert public_profile_resp.status_code == 200, public_profile_resp.text
        public_profile = public_profile_resp.json()
        assert public_profile["username"] == "demo"
        assert public_profile["is_public"] is True

        public_collections_resp = client.get(
            "/api/public/users/demo/collections",
            headers={"Accept-Language": "zh-CN"},
        )
        assert public_collections_resp.status_code == 200, public_collections_resp.text
        assert public_collections_resp.json()["total"] >= 1

    print("Project smoke tests passed.")


if __name__ == "__main__":
    run_smoke()

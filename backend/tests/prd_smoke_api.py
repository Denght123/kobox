from __future__ import annotations

import os
from pathlib import Path
import sys

from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def _prepare_env() -> None:
    base_dir = Path(__file__).resolve().parent / ".tmp"
    base_dir.mkdir(parents=True, exist_ok=True)
    db_path = base_dir / "prd_smoke.db"
    uploads_path = base_dir / "prd_uploads"

    if db_path.exists():
        db_path.unlink()

    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    os.environ["SEED_ON_STARTUP"] = "true"
    os.environ["AUTO_CREATE_TABLES"] = "true"
    os.environ["UPLOADS_DIR"] = str(uploads_path)
    os.environ["UPLOADS_URL_PREFIX"] = "/uploads"
    os.environ["CORS_ALLOW_ORIGINS"] = "http://localhost:5173,http://127.0.0.1:5173"
    os.environ["APP_DEBUG"] = "false"
    os.environ["ADMIN_STATS_TOKEN"] = "test-admin-stats-token"


def run_prd_smoke() -> None:
    _prepare_env()
    from app.main import app

    with TestClient(app) as client:
        health_resp = client.get("/health")
        assert health_resp.status_code == 200

        login_resp = client.post(
            "/api/auth/login",
            json={"account": "demo@kobox.local", "password": "Demo1234!"},
        )
        assert login_resp.status_code == 200, login_resp.text
        session = login_resp.json()
        headers = {
            "Authorization": f"Bearer {session['access_token']}",
            "Accept-Language": "zh-CN",
        }

        settings_resp = client.put(
            "/api/me/settings",
            headers=headers,
            json={"language": "zh-CN", "show_dynamic_background": True, "show_public_rank": True},
        )
        assert settings_resp.status_code == 200, settings_resp.text
        assert settings_resp.json()["language"] == "zh-CN"

        profile_resp = client.put(
            "/api/me/profile",
            headers=headers,
            json={"display_name": "Smoke Traveler", "birthday": "2006-05-17", "bio": "PRD smoke profile save."},
        )
        assert profile_resp.status_code == 200, profile_resp.text
        assert profile_resp.json()["display_name"] == "Smoke Traveler"

        background_resp = client.post(
            "/api/me/background",
            headers=headers,
            files={"file": ("background.png", b"fake-image-bytes", "image/png")},
        )
        assert background_resp.status_code == 200, background_resp.text
        background_data = background_resp.json()
        assert background_data["background_image_url"]
        assert background_data["profile"]["background_image_url"] == background_data["background_image_url"]

        search_resp = client.get(
            "/api/anime/search",
            headers=headers,
            params={"q": "芙莉莲", "page": 1, "page_size": 5},
        )
        assert search_resp.status_code == 200, search_resp.text
        search_items = search_resp.json()["items"]
        assert search_items, "search should return anime items"
        assert all(item.get("cover_url") for item in search_items)

        suggestion_resp = client.get(
            "/api/anime/search/suggestions",
            headers=headers,
            params={"q": "四月", "page": 1, "page_size": 5},
        )
        assert suggestion_resp.status_code == 200, suggestion_resp.text
        suggestion_items = suggestion_resp.json()["items"]
        assert suggestion_items, "suggestions should return anime items"
        assert any("四月" in item["title"] for item in suggestion_items)

        source_id = search_items[0]["source_id"]
        collection_resp = client.post(
            "/api/me/collections",
            headers=headers,
            json={"source_id": source_id, "collection_status": "completed"},
        )
        assert collection_resp.status_code == 201, collection_resp.text
        assert collection_resp.json()["collection_status"] == "completed"
        assert collection_resp.json()["anime"]["source_id"] == source_id

        collections_resp = client.get("/api/me/collections", headers=headers)
        assert collections_resp.status_code == 200, collections_resp.text
        collection_items = collections_resp.json()["items"]
        assert any(item["anime"]["source_id"] == source_id for item in collection_items)

        collection_id = collection_resp.json()["id"]
        update_collection_resp = client.put(
            f"/api/me/collections/{collection_id}",
            headers=headers,
            json={"collection_status": "watching"},
        )
        assert update_collection_resp.status_code == 200, update_collection_resp.text
        assert update_collection_resp.json()["collection_status"] == "watching"

        watching_resp = client.get(
            "/api/me/collections",
            headers=headers,
            params={"status": "watching", "page": 1, "page_size": 100},
        )
        assert watching_resp.status_code == 200, watching_resp.text
        assert any(item["id"] == collection_id for item in watching_resp.json()["items"])

        anime_id = collection_resp.json()["anime"]["id"]
        favorite_resp = client.put(
            "/api/me/favorites/rank",
            headers=headers,
            json={"items": [{"anime_id": anime_id, "rank_order": 1}]},
        )
        assert favorite_resp.status_code == 200, favorite_resp.text
        favorite_items = favorite_resp.json()["items"]
        assert favorite_items and favorite_items[0]["anime"]["id"] == anime_id

        duplicate_rank_resp = client.put(
            "/api/me/favorites/rank",
            headers=headers,
            json={"items": [{"anime_id": anime_id, "rank_order": 1}, {"anime_id": anime_id, "rank_order": 1}]},
        )
        assert duplicate_rank_resp.status_code == 400, duplicate_rank_resp.text
        assert duplicate_rank_resp.json()["code"] == "duplicate_rank_order"

        missing_collection_resp = client.put(
            "/api/me/favorites/rank",
            headers=headers,
            json={"items": [{"anime_id": 999999999, "rank_order": 1}]},
        )
        assert missing_collection_resp.status_code == 400, missing_collection_resp.text
        assert missing_collection_resp.json()["code"] == "favorite_not_in_collection"

        delete_resp = client.delete(f"/api/me/collections/{collection_id}", headers=headers)
        assert delete_resp.status_code == 200, delete_resp.text
        after_delete_resp = client.get("/api/me/collections", headers=headers, params={"page_size": 100})
        assert after_delete_resp.status_code == 200, after_delete_resp.text
        assert all(item["id"] != collection_id for item in after_delete_resp.json()["items"])

        public_resp = client.get("/api/public/users/demo", headers={"Accept-Language": "zh-CN"})
        assert public_resp.status_code == 200, public_resp.text
        assert public_resp.json()["username"] == "demo"

        admin_forbidden_resp = client.get("/api/admin/stats")
        assert admin_forbidden_resp.status_code == 403, admin_forbidden_resp.text

        admin_stats_resp = client.get(
            "/api/admin/stats",
            headers={"X-Admin-Token": "test-admin-stats-token"},
        )
        assert admin_stats_resp.status_code == 200, admin_stats_resp.text
        stats = admin_stats_resp.json()
        assert stats["total_users"] >= 1
        assert stats["today_users"] >= 1
        assert len(stats["daily_registrations"]) == 30

    print("PRD smoke tests passed.")


if __name__ == "__main__":
    run_prd_smoke()

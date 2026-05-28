# d:\Project\ContestMind\backend\app\services\codeforces_service.py
import httpx
import json
import time
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)
CACHE_EXPIRATION_SECONDS = 24 * 60 * 60  # 24 hours


class CodeforcesService:
    def __init__(self, base_url: str = "https://codeforces.com/api/"):
        self.base_url = base_url
        self.client = httpx.Client()  # Switched to synchronous client
        self.cache_dir = settings.RAW_DATA_DIR / "codeforces"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_problemset(self) -> Optional[Dict[str, Any]]:
        cache_file = self.cache_dir / "problemset_problems.json"

        if cache_file.exists():
            last_modified_time = cache_file.stat().st_mtime
            if time.time() - last_modified_time < CACHE_EXPIRATION_SECONDS:
                logger.info("Cache hit: Loading problemset from file.")
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)

        logger.info("Cache miss or expired: Fetching problemset from Codeforces API.")
        try:
            url = f"{self.base_url}problemset.problems"
            response = self.client.get(url)
            response.raise_for_status()
            data = response.json()

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Successfully saved problemset to cache: {cache_file}")

            return data
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return None

    def get_user_info(self, handle: str) -> Optional[Dict[str, Any]]:
        cache_file = self.cache_dir / f"user_info_{handle}.json"
        
        if cache_file.exists():
            last_modified_time = cache_file.stat().st_mtime
            if time.time() - last_modified_time < CACHE_EXPIRATION_SECONDS:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)

        try:
            url = f"{self.base_url}user.info?handles={handle}"
            response = self.client.get(url)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "OK" and len(data.get("result", [])) > 0:
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(data["result"][0], f, indent=2)
                return data["result"][0]
            return None
        except Exception as e:
            logger.error(f"Error fetching user info for {handle}: {e}")
            return None

    def get_user_status(self, handle: str) -> Optional[list]:
        cache_file = self.cache_dir / f"user_status_{handle}.json"
        # Shorter cache for user status (1 hour)
        if cache_file.exists():
            last_modified_time = cache_file.stat().st_mtime
            if time.time() - last_modified_time < 3600:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)

        try:
            url = f"{self.base_url}user.status?handle={handle}"
            response = self.client.get(url)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "OK":
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(data["result"], f, indent=2)
                return data["result"]
            return None
        except Exception as e:
            logger.error(f"Error fetching user status for {handle}: {e}")
            return None
    def get_user_rating(self, handle: str) -> Optional[list]:
        cache_file = self.cache_dir / f"user_rating_{handle}.json"
        if cache_file.exists():
            last_modified_time = cache_file.stat().st_mtime
            if time.time() - last_modified_time < 3600:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)

        try:
            url = f"{self.base_url}user.rating?handle={handle}"
            response = self.client.get(url)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "OK":
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(data["result"], f, indent=2)
                return data["result"]
            return None
        except Exception as e:
            logger.error(f"Error fetching user rating for {handle}: {e}")
            return None

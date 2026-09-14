from __future__ import annotations
import requests
from datetime import timedelta

BASE = "https://api.sportmonks.com/v3/football"

class SportmonksError(RuntimeError):
    pass

class SportmonksClient:
    def __init__(self, token: str, timeout: int = 25):
        self.token = token.strip()
        self.timeout = timeout
        self.session = requests.Session()

    def _get_all(self, path: str, params: dict | None = None):
        params = dict(params or {})
        params["api_token"] = self.token
        params.setdefault("per_page", 100)

        url = f"{BASE}/{path.lstrip('/')}"
        out = []
        page = 1

        while True:
            params["page"] = page
            try:
                r = self.session.get(url, params=params, timeout=self.timeout)
            except requests.RequestException as e:
                raise SportmonksError(f"Sportmonks bağlantı hatası: {e}") from e

            if r.status_code != 200:
                try:
                    detail = r.json()
                except Exception:
                    detail = r.text[:500]
                raise SportmonksError(
                    f"Sportmonks API hatası ({r.status_code}). "
                    f"Token/abonelik kapsamını kontrol et. Detay: {detail}"
                )

            payload = r.json()
            data = payload.get("data", [])
            if isinstance(data, dict):
                data = [data]
            out.extend(data)

            pagination = payload.get("pagination") or {}
            if pagination.get("has_more") is True:
                page += 1
                continue

            current = pagination.get("current_page")
            last = pagination.get("last_page")
            if current and last and current < last:
                page += 1
                continue
            break

        return out

    def fixtures_by_date(self, day):
        return self._get_all(
            f"fixtures/date/{day.isoformat()}",
            {"include": "participants;league"}
        )

    def fixtures_between(self, start, end):
        """
        Sportmonks free tiers can reject long date ranges.
        Split the request automatically into <= 95 day windows.
        """
        if end < start:
            return []

        out = []
        chunk_start = start
        while chunk_start <= end:
            chunk_end = min(chunk_start + timedelta(days=94), end)
            out.extend(
                self._get_all(
                    f"fixtures/between/{chunk_start.isoformat()}/{chunk_end.isoformat()}",
                    {"include": "participants;scores;league"}
                )
            )
            chunk_start = chunk_end + timedelta(days=1)

        # de-duplicate by fixture id
        seen = set()
        unique = []
        for f in out:
            fid = f.get("id")
            if fid in seen:
                continue
            seen.add(fid)
            unique.append(f)
        return unique

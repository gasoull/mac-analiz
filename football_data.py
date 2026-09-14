from __future__ import annotations

import time
from datetime import date
import requests

BASE_URL = "https://api.football-data.org/v4"


class FootballDataError(Exception):
    pass


class FootballDataClient:
    def __init__(self, token: str, timeout: int = 25):
        self.token = (token or "").strip()
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "X-Auth-Token": self.token,
            "User-Agent": "ONUR-Tahmin/4.0"
        })

    def _get(self, path: str, params: dict | None = None):
        if not self.token:
            raise FootballDataError("FOOTBALL_DATA_API_TOKEN bulunamadı.")

        url = f"{BASE_URL}{path}"
        try:
            r = self.session.get(url, params=params, timeout=self.timeout)
        except requests.RequestException as exc:
            raise FootballDataError(f"football-data.org bağlantı hatası: {exc}") from exc

        if r.status_code == 429:
            reset = r.headers.get("X-RequestCounter-Reset")
            msg = "API istek limiti doldu."
            if reset:
                msg += f" Yaklaşık {reset} saniye sonra tekrar dene."
            raise FootballDataError(msg)

        if r.status_code in (401, 403):
            raise FootballDataError(
                "API anahtarı kabul edilmedi veya bu veriye plan erişimi yok."
            )

        if not r.ok:
            detail = ""
            try:
                detail = (r.json() or {}).get("message") or ""
            except Exception:
                detail = r.text[:300]
            raise FootballDataError(
                f"football-data.org API hatası ({r.status_code}). {detail}"
            )

        try:
            return r.json()
        except Exception as exc:
            raise FootballDataError("API yanıtı JSON olarak okunamadı.") from exc

    def competitions(self):
        data = self._get("/competitions")
        return data.get("competitions") or []

    def matches_by_date(self, day: date | str):
        d = day.isoformat() if hasattr(day, "isoformat") else str(day)
        data = self._get("/matches", {"dateFrom": d, "dateTo": d})
        return data.get("matches") or []

    def matches_between(self, start: date | str, end: date | str, competition_ids=None, status="FINISHED"):
        s = start.isoformat() if hasattr(start, "isoformat") else str(start)
        e = end.isoformat() if hasattr(end, "isoformat") else str(end)
        params = {"dateFrom": s, "dateTo": e}
        if competition_ids:
            params["competitions"] = ",".join(str(x) for x in competition_ids)
        if status:
            params["status"] = status
        data = self._get("/matches", params)
        return data.get("matches") or []

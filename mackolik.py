from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any
import time
import requests

BASE_URL = "https://vd.mackolik.com/livedata"


class MackolikError(Exception):
    pass


def _get(row, idx, default=None):
    try:
        value = row[idx]
        return default if value is None else value
    except Exception:
        return default


def _to_int(value):
    try:
        if value in ("", None, "-", "null"):
            return None
        return int(value)
    except Exception:
        return None


def _league_name(row):
    meta = _get(row, 36, [])
    try:
        name = meta[9]
        if name:
            return str(name).strip()
    except Exception:
        pass
    # Defensive fallbacks for schema changes
    for idx in (9, 8, 7, 5):
        try:
            v = meta[idx]
            if isinstance(v, str) and v.strip():
                return v.strip()
        except Exception:
            pass
    return "Diğer"


def _season_name(row):
    meta = _get(row, 36, [])
    try:
        v = meta[5]
        return str(v).strip() if v else ""
    except Exception:
        return ""


def _is_football(row):
    # Historic/public client implementations identify index 23 == 1 as football.
    v = _get(row, 23)
    return v in (1, "1", True)


def _finished_score(row):
    # Older Mackolik schema exposed FT score in 29/30.
    h = _to_int(_get(row, 29))
    a = _to_int(_get(row, 30))
    if h is not None and a is not None:
        return h, a

    # Live/current score fallback.
    minute = str(_get(row, 6, "")).strip()
    h2 = _to_int(_get(row, 12))
    a2 = _to_int(_get(row, 13))
    if minute.upper() in ("MS", "FT", "BİTTİ", "BITTI") and h2 is not None and a2 is not None:
        return h2, a2

    return None


def normalize_match(row, requested_day: date):
    if not isinstance(row, list) or not _is_football(row):
        return None

    home = str(_get(row, 2, "") or "").strip()
    away = str(_get(row, 4, "") or "").strip()
    if not home or not away:
        return None

    match_id = _get(row, 0, "")
    code = _get(row, 14, 0)
    minute = str(_get(row, 6, "") or "").strip()
    match_time = str(_get(row, 16, "") or "").strip()
    raw_date = str(_get(row, 35, "") or "").strip()

    score = _finished_score(row)
    live_home = _to_int(_get(row, 12))
    live_away = _to_int(_get(row, 13))

    is_finished = score is not None
    is_live = (
        not is_finished
        and minute
        and minute.upper() not in ("MS", "FT", "-", "0")
        and any(ch.isdigit() for ch in minute)
    )

    status = "FINISHED" if is_finished else ("LIVE" if is_live else "SCHEDULED")

    if score:
        fh, fa = score
    else:
        fh = fa = None

    return {
        "id": match_id,
        "bet_code": code,
        "date": raw_date or requested_day.strftime("%d/%m/%Y"),
        "date_iso": requested_day.isoformat(),
        "time": match_time,
        "minute": minute,
        "status": status,
        "league": _league_name(row),
        "season": _season_name(row),
        "home": home,
        "away": away,
        "home_score": fh,
        "away_score": fa,
        "live_home_score": live_home,
        "live_away_score": live_away,
        "raw": row,
    }


class MackolikClient:
    def __init__(self, timeout: int = 18):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/152.0 Safari/537.36"
            ),
            "Accept": "application/json,text/plain,*/*",
            "Referer": "https://www.mackolik.com/",
        })

    def day(self, day: date):
        params = {
            "date": day.strftime("%d/%m/%Y"),
            "_": int(time.time() * 1000),
        }
        try:
            r = self.session.get(BASE_URL, params=params, timeout=self.timeout)
        except requests.RequestException as exc:
            raise MackolikError(f"Maçkolik veri bağlantısı kurulamadı: {exc}") from exc

        if not r.ok:
            raise MackolikError(f"Maçkolik veri servisi HTTP {r.status_code} döndürdü.")

        try:
            payload = r.json()
        except Exception as exc:
            raise MackolikError("Maçkolik yanıtı JSON olarak okunamadı.") from exc

        raw_matches = payload.get("m")
        if not isinstance(raw_matches, list):
            raise MackolikError("Maçkolik maç listesi beklenen formatta gelmedi.")

        out = []
        for row in raw_matches:
            m = normalize_match(row, day)
            if m:
                out.append(m)
        return out

    def range(self, start: date, end: date, delay: float = 0.06):
        if end < start:
            return []

        out = []
        d = start
        errors = []
        while d <= end:
            try:
                out.extend(self.day(d))
            except MackolikError as exc:
                errors.append((d.isoformat(), str(exc)))
            d += timedelta(days=1)
            if d <= end and delay:
                time.sleep(delay)
        return out, errors

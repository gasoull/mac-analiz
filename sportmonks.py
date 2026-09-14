from __future__ import annotations
import requests

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
            has_more = pagination.get("has_more")
            if has_more is True:
                page += 1
                continue

            # Bazı yanıtlarda has_more yerine current_page/last_page bulunabilir.
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
        return self._get_all(
            f"fixtures/between/{start.isoformat()}/{end.isoformat()}",
            {"include": "participants;scores;league"}
        )

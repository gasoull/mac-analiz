from __future__ import annotations

from collections import defaultdict
from datetime import datetime
import math

MARKETS = ["1.5 Üst", "2.5 Üst", "3.5 Alt", "KG Var", "KG Yok"]


def _dt(match):
    raw = match.get("utcDate") or ""
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return datetime.min


def _score(match):
    score = match.get("score") or {}
    full = score.get("fullTime") or {}
    h, a = full.get("home"), full.get("away")
    if h is None or a is None:
        return None
    return int(h), int(a)


def build_history_index(history):
    idx = defaultdict(list)
    for m in history:
        score = _score(m)
        home = m.get("homeTeam") or {}
        away = m.get("awayTeam") or {}
        hid, aid = home.get("id"), away.get("id")
        if score is None or hid is None or aid is None:
            continue

        row = {
            "id": m.get("id"),
            "date": _dt(m),
            "home_id": hid,
            "away_id": aid,
            "home_goals": score[0],
            "away_goals": score[1],
        }
        idx[hid].append(row)
        idx[aid].append(row)

    for tid in idx:
        idx[tid].sort(key=lambda x: x["date"], reverse=True)
    return idx


def _market_hit(row, market):
    total = row["home_goals"] + row["away_goals"]
    btts = row["home_goals"] > 0 and row["away_goals"] > 0
    return {
        "1.5 Üst": total >= 2,
        "2.5 Üst": total >= 3,
        "3.5 Alt": total <= 3,
        "KG Var": btts,
        "KG Yok": not btts,
    }[market]


def _goal_values(row, team_id):
    if row["home_id"] == team_id:
        return row["home_goals"], row["away_goals"]
    return row["away_goals"], row["home_goals"]


def _smoothed_rate(rows, market, prior=3.5):
    if not rows:
        return .50, 0
    hits = sum(_market_hit(r, market) for r in rows)
    return (hits + .5 * prior) / (len(rows) + prior), len(rows)


def _avg_goals(rows, team_id):
    if not rows:
        return 0.0, 0.0
    gf = ga = 0
    for r in rows:
        a, b = _goal_values(r, team_id)
        gf += a
        ga += b
    n = len(rows)
    return gf / n, ga / n


def _venue_rows(rows, team_id, venue):
    if venue == "home":
        return [r for r in rows if r["home_id"] == team_id]
    return [r for r in rows if r["away_id"] == team_id]


def _confidence_label(prob):
    if prob >= 82:
        return "Çok güçlü"
    if prob >= 75:
        return "Güçlü"
    if prob >= 68:
        return "Orta"
    return "Sınırda"


def analyze_fixture(match, history_index, market, sample_size=10):
    if market not in MARKETS:
        return None

    home = match.get("homeTeam") or {}
    away = match.get("awayTeam") or {}
    hid, aid = home.get("id"), away.get("id")
    if hid is None or aid is None:
        return None

    h_recent = (history_index.get(hid) or [])[:sample_size]
    a_recent = (history_index.get(aid) or [])[:sample_size]
    if len(h_recent) < 3 or len(a_recent) < 3:
        return None

    h_home = _venue_rows(h_recent, hid, "home")
    a_away = _venue_rows(a_recent, aid, "away")

    h_all_rate, hn = _smoothed_rate(h_recent, market)
    a_all_rate, an = _smoothed_rate(a_recent, market)
    h_venue_rate, hhn = _smoothed_rate(h_home, market)
    a_venue_rate, aan = _smoothed_rate(a_away, market)

    # Recent form is primary; home/away tendencies support it.
    raw = (
        .34 * h_all_rate +
        .34 * a_all_rate +
        .16 * h_venue_rate +
        .16 * a_venue_rate
    )

    effective = min(hn, sample_size) + min(an, sample_size) + min(hhn, 5) + min(aan, 5)
    confidence = min(1.0, effective / 26.0)

    # Pull small samples back toward 50%.
    prob = .50 + (raw - .50) * (.58 + .42 * confidence)
    prob = max(.05, min(.95, prob))

    hgf, hga = _avg_goals(h_recent, hid)
    agf, aga = _avg_goals(a_recent, aid)

    total_samples = hn + an
    avg_total = ((hgf+hga) + (agf+aga)) / 2

    # Extra descriptive stats for premium card.
    merged = h_recent + a_recent
    btts_rate = sum(
        (r["home_goals"] > 0 and r["away_goals"] > 0) for r in merged
    ) / len(merged) if merged else 0
    over25_rate = sum(
        (r["home_goals"] + r["away_goals"] >= 3) for r in merged
    ) / len(merged) if merged else 0

    comp = match.get("competition") or {}
    area = match.get("area") or {}
    kickoff = (match.get("utcDate") or "")[:16].replace("T", " ")

    return {
        "fixture_id": match.get("id"),
        "home": home.get("name") or home.get("shortName") or "Ev Sahibi",
        "away": away.get("name") or away.get("shortName") or "Deplasman",
        "home_short": home.get("shortName") or home.get("name") or "",
        "away_short": away.get("shortName") or away.get("name") or "",
        "home_crest": home.get("crest"),
        "away_crest": away.get("crest"),
        "league": comp.get("name") or comp.get("code") or "Lig",
        "league_code": comp.get("code") or "",
        "league_emblem": comp.get("emblem"),
        "country": area.get("name") or "",
        "kickoff": kickoff,
        "market": market,
        "probability": prob * 100,
        "confidence": _confidence_label(prob * 100),
        "sample_count": total_samples,
        "avg_goals": avg_total,
        "btts_rate": btts_rate * 100,
        "over25_rate": over25_rate * 100,
        "home_form": h_all_rate * 100,
        "away_form": a_all_rate * 100,
        "components": {
            f"{home.get('shortName') or home.get('name')} son {hn}": round(h_all_rate*100, 1),
            f"{away.get('shortName') or away.get('name')} son {an}": round(a_all_rate*100, 1),
            "Ev sahibi iç saha": round(h_venue_rate*100, 1),
            "Deplasman dış saha": round(a_venue_rate*100, 1),
            "Veri güveni": round(confidence*100, 0),
        },
    }


def strongest_market(match, history_index, sample_size=10):
    candidates = []
    for market in MARKETS:
        row = analyze_fixture(match, history_index, market, sample_size)
        if row:
            candidates.append(row)
    if not candidates:
        return None
    return max(candidates, key=lambda x: x["probability"])

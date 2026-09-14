from __future__ import annotations

from collections import defaultdict
from datetime import datetime

MARKETS = ["1.5 Üst", "2.5 Üst", "3.5 Alt", "KG Var", "KG Yok"]


def _norm_name(name: str) -> str:
    return " ".join((name or "").casefold().split())


def build_team_history(matches):
    index = defaultdict(list)
    for m in matches:
        if m.get("status") != "FINISHED":
            continue
        hs, as_ = m.get("home_score"), m.get("away_score")
        if hs is None or as_ is None:
            continue

        row = {
            "date_iso": m.get("date_iso") or "",
            "home": m.get("home") or "",
            "away": m.get("away") or "",
            "hg": int(hs),
            "ag": int(as_),
            "league": m.get("league") or "",
        }
        index[_norm_name(row["home"])].append(row)
        index[_norm_name(row["away"])].append(row)

    for key in index:
        index[key].sort(key=lambda x: x["date_iso"], reverse=True)
    return index


def _hit(row, market):
    total = row["hg"] + row["ag"]
    btts = row["hg"] > 0 and row["ag"] > 0
    return {
        "1.5 Üst": total >= 2,
        "2.5 Üst": total >= 3,
        "3.5 Alt": total <= 3,
        "KG Var": btts,
        "KG Yok": not btts,
    }[market]


def _rate(rows, market, prior=3.0):
    if not rows:
        return .50, 0
    hits = sum(_hit(r, market) for r in rows)
    # small-sample shrinkage to 50%
    return (hits + 0.5 * prior) / (len(rows) + prior), len(rows)


def _venue(rows, team_name, home=True):
    n = _norm_name(team_name)
    if home:
        return [r for r in rows if _norm_name(r["home"]) == n]
    return [r for r in rows if _norm_name(r["away"]) == n]


def _team_goals(rows, team):
    if not rows:
        return 0.0, 0.0
    key = _norm_name(team)
    gf = ga = 0
    for r in rows:
        if _norm_name(r["home"]) == key:
            gf += r["hg"]; ga += r["ag"]
        else:
            gf += r["ag"]; ga += r["hg"]
    return gf/len(rows), ga/len(rows)


def analyze(fixture, history_idx, market, sample_size=8):
    home, away = fixture["home"], fixture["away"]
    hr = (history_idx.get(_norm_name(home)) or [])[:sample_size]
    ar = (history_idx.get(_norm_name(away)) or [])[:sample_size]

    if len(hr) < 3 or len(ar) < 3:
        return None

    hh = _venue(hr, home, True)
    aa = _venue(ar, away, False)

    h_all, hn = _rate(hr, market)
    a_all, an = _rate(ar, market)
    h_venue, hhn = _rate(hh, market)
    a_venue, aan = _rate(aa, market)

    raw = .34*h_all + .34*a_all + .16*h_venue + .16*a_venue
    evidence = min(hn, sample_size) + min(an, sample_size) + min(hhn, 5) + min(aan, 5)
    trust = min(1.0, evidence / 24.0)

    # conservative probability; these are model scores, not bookmaker probabilities
    p = .50 + (raw - .50) * (.60 + .40*trust)
    p = min(.94, max(.06, p))

    hgf, hga = _team_goals(hr, home)
    agf, aga = _team_goals(ar, away)
    merged = hr + ar
    btts = sum((r["hg"] > 0 and r["ag"] > 0) for r in merged) / len(merged)
    over25 = sum((r["hg"] + r["ag"] >= 3) for r in merged) / len(merged)

    pct = p*100
    label = "Çok güçlü" if pct >= 82 else "Güçlü" if pct >= 75 else "Orta" if pct >= 68 else "Sınırda"

    return {
        **fixture,
        "market": market,
        "probability": pct,
        "confidence": label,
        "sample_count": hn + an,
        "avg_goals": ((hgf+hga)+(agf+aga))/2,
        "btts_rate": btts*100,
        "over25_rate": over25*100,
        "home_rate": h_all*100,
        "away_rate": a_all*100,
        "details": {
            f"{home} son {hn}": round(h_all*100,1),
            f"{away} son {an}": round(a_all*100,1),
            "Ev sahibi iç saha": round(h_venue*100,1),
            "Deplasman dış saha": round(a_venue*100,1),
            "Veri güveni": round(trust*100,0),
        }
    }


def strongest(fixture, history_idx, sample_size=8):
    candidates = [analyze(fixture, history_idx, m, sample_size) for m in MARKETS]
    candidates = [x for x in candidates if x]
    return max(candidates, key=lambda x: x["probability"]) if candidates else None

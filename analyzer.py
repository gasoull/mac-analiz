from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timedelta
import math
import random

MARKETS = {"1.5 Üst", "2.5 Üst", "3.5 Alt", "KG Var", "KG Yok"}

def _participants(f):
    ps = f.get("participants") or []
    home = away = None
    for p in ps:
        loc = ((p.get("meta") or {}).get("location") or "").lower()
        if loc == "home":
            home = p
        elif loc == "away":
            away = p
    # Demo/fallback
    if not home and len(ps) >= 1:
        home = ps[0]
    if not away and len(ps) >= 2:
        away = ps[1]
    return home, away

def _current_score(f):
    home = away = None
    for s in f.get("scores") or []:
        if str(s.get("description", "")).upper() == "CURRENT":
            obj = s.get("score") or {}
            loc = str(obj.get("participant", "")).lower()
            goals = obj.get("goals")
            if loc == "home":
                home = goals
            elif loc == "away":
                away = goals
    if home is None or away is None:
        return None
    return int(home), int(away)

def _dt(f):
    raw = f.get("starting_at") or ""
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return datetime.min

def build_history_index(history):
    idx = defaultdict(list)
    for f in history:
        score = _current_score(f)
        home, away = _participants(f)
        if not score or not home or not away:
            continue
        row = {
            "fixture_id": f.get("id"),
            "date": _dt(f),
            "home_id": home.get("id"),
            "away_id": away.get("id"),
            "home_goals": score[0],
            "away_goals": score[1],
        }
        idx[home.get("id")].append(row)
        idx[away.get("id")].append(row)

    for team_id in idx:
        idx[team_id].sort(key=lambda x: x["date"], reverse=True)
    return idx

def _hit(row, market):
    total = row["home_goals"] + row["away_goals"]
    btts = row["home_goals"] > 0 and row["away_goals"] > 0
    if market == "1.5 Üst":
        return total >= 2
    if market == "2.5 Üst":
        return total >= 3
    if market == "3.5 Alt":
        return total <= 3
    if market == "KG Var":
        return btts
    if market == "KG Yok":
        return not btts
    return False

def _smoothed_rate(rows, market, prior_strength=3.0):
    # Beta-benzeri yumuşatma: küçük örneklemde aşırı %0/%100 oluşmasını engeller.
    n = len(rows)
    if n == 0:
        return 0.50, 0
    hits = sum(1 for r in rows if _hit(r, market))
    rate = (hits + 0.5 * prior_strength) / (n + prior_strength)
    return rate, n

def _team_rates(team_id, rows, market, n, venue):
    recent = (rows.get(team_id) or [])[:n]
    overall, no = _smoothed_rate(recent, market)

    venue_rows = []
    for r in recent:
        if venue == "home" and r["home_id"] == team_id:
            venue_rows.append(r)
        elif venue == "away" and r["away_id"] == team_id:
            venue_rows.append(r)
    v_rate, nv = _smoothed_rate(venue_rows, market)
    return overall, no, v_rate, nv

def analyze_fixture(fixture, history_index, market, sample_size=10):
    if market not in MARKETS:
        return None

    home, away = _participants(fixture)
    if not home or not away:
        return None

    hid, aid = home.get("id"), away.get("id")
    h_over, hn, h_home, hhn = _team_rates(hid, history_index, market, sample_size, "home")
    a_over, an, a_away, aan = _team_rates(aid, history_index, market, sample_size, "away")

    if hn < 3 or an < 3:
        return None

    # Ağırlıklar: genel form daha güçlü; saha alt-örneklemleri destekleyici.
    raw = 0.35*h_over + 0.35*a_over + 0.15*h_home + 0.15*a_away

    # Veri azsa %50'ye doğru çek.
    effective = min(hn, sample_size) + min(an, sample_size) + min(hhn, 5) + min(aan, 5)
    confidence = min(1.0, effective / 24.0)
    prob = 0.50 + (raw - 0.50) * (0.55 + 0.45*confidence)
    prob = max(0.05, min(0.95, prob))

    league = (fixture.get("league") or {}).get("name") or f"Lig #{fixture.get('league_id')}"
    kickoff = (fixture.get("starting_at") or "")[:16].replace("T", " ")

    components = {
        f"{home.get('name')} son {hn} maç": round(h_over*100, 1),
        f"{away.get('name')} son {an} maç": round(a_over*100, 1),
        f"{home.get('name')} iç saha ({hhn})": round(h_home*100, 1),
        f"{away.get('name')} deplasman ({aan})": round(a_away*100, 1),
        "örneklem güven katsayısı": round(confidence, 2),
    }

    explanation = (
        f"{home.get('name')} genel %{h_over*100:.0f}, iç saha %{h_home*100:.0f}; "
        f"{away.get('name')} genel %{a_over*100:.0f}, deplasman %{a_away*100:.0f}. "
        "Bu oranlar ağırlıklandırılıp küçük örneklem etkisi azaltıldı."
    )

    return {
        "fixture_id": fixture.get("id"),
        "home": home.get("name", "Ev"),
        "away": away.get("name", "Dep"),
        "league": league,
        "kickoff": kickoff,
        "market": market,
        "probability": prob * 100,
        "sample_count": hn + an,
        "components": components,
        "explanation": explanation,
    }

# ---------------- Demo veri ----------------

def _team(tid, name, loc):
    return {"id": tid, "name": name, "meta": {"location": loc}}

def _score(home, away):
    return [
        {"description":"CURRENT", "score":{"participant":"home","goals":home}},
        {"description":"CURRENT", "score":{"participant":"away","goals":away}},
    ]

def demo_fixtures(day):
    names = [
        ("North London FC","Mersey Blue","Premier League",8),
        ("Birmingham Athletic","Leeds City","Championship",9),
        ("Manchester Red","Brighton Coast","Premier League",8),
        ("Sheffield Town","Norwich Green","Championship",9),
        ("West London FC","Newcastle Black","Premier League",8),
        ("Bristol Cityside","Coventry Sky","Championship",9),
        ("Liverpool Red","London Palace","Premier League",8),
        ("Sunderland North","Derby Countywide","Championship",9),
        ("Fulham Riverside","Wolverhampton","Premier League",8),
        ("Middlesbrough","Blackburn Blue","Championship",9),
        ("Brentford Bee","Nottingham Red","Premier League",8),
        ("Southampton","Millwall","Championship",9),
        ("Everton Blue","Bournemouth","Premier League",8),
        ("Ipswich Town","Watford","Championship",9),
        ("Aston Claret","Burnley","Premier League",8),
    ]
    out=[]
    for i,(h,a,l,lid) in enumerate(names,1):
        out.append({
            "id":10000+i, "league_id":lid, "league":{"name":l},
            "starting_at":f"{day.isoformat()} {12+(i%8):02d}:00:00",
            "participants":[_team(i*2-1,h,"home"),_team(i*2,a,"away")]
        })
    return out

def demo_history(day):
    rng = random.Random(42)
    fixtures = demo_fixtures(day)
    teams=[]
    for f in fixtures:
        teams.extend(f["participants"])

    out=[]
    fid=20000
    for t in teams:
        tid=t["id"]
        for j in range(12):
            fid+=1
            is_home = (j % 2 == 0)
            opp_id = 1000 + tid*20 + j
            # Bazı takımları doğal olarak daha yüksek/düşük gollü yap.
            bias = (tid % 5) * 0.18
            hg = max(0, min(5, int(rng.gauss(1.45+bias, 1.0))))
            ag = max(0, min(5, int(rng.gauss(1.15+bias/2, 0.9))))
            d = day - timedelta(days=3+j*7)
            if is_home:
                ps=[_team(tid,t["name"],"home"), _team(opp_id,f"Rakip {opp_id}","away")]
            else:
                ps=[_team(opp_id,f"Rakip {opp_id}","home"), _team(tid,t["name"],"away")]
            out.append({
                "id":fid, "league_id":8 if tid%2 else 9,
                "starting_at":f"{d.isoformat()} 18:00:00",
                "participants":ps, "scores":_score(hg,ag),
            })
    return out

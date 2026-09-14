from __future__ import annotations

from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from collections import defaultdict
from html import escape
import time
import requests
import unicodedata
import streamlit as st

# =========================
# AYARLAR
# =========================
st.set_page_config(
    page_title="ONUR | Günlük Futbol Tahminleri",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_URL = "https://vd.mackolik.com/livedata"
MARKETS = ["1.5 Üst", "2.5 Üst", "3.5 Üst", "3.5 Alt", "KG Var", "KG Yok"]

# =========================
# TASARIM
# =========================
st.markdown("""
<style>
:root{
  --red:#e31d2b;--red-dark:#bf1420;--ink:#1f2937;--muted:#6b7280;
  --line:#e5e7eb;--soft:#f6f7f9;--green:#16a34a;
}
.block-container{max-width:1180px;padding-top:5.2rem;padding-bottom:3rem}
[data-testid="stSidebar"]{background:#fff;border-right:1px solid var(--line)}
[data-testid="stSidebar"] .block-container{padding-top:1rem}
.topbar{display:flex;align-items:center;justify-content:space-between;gap:18px;min-height:72px;padding:14px 18px;background:#ffffff;border:1px solid #e3e6eb;border-left:5px solid #e31d2b;border-radius:14px;margin:0 0 18px 0;box-shadow:0 5px 18px rgba(17,24,39,.06);position:relative;z-index:2}
.brand-wrap{display:flex;align-items:center;gap:14px}
.brand-mark{width:46px;height:46px;border-radius:14px;display:grid;place-items:center;background:#e31d2b;color:#fff;font-weight:950;font-size:16px;letter-spacing:-.03em;box-shadow:inset 0 -2px 0 rgba(0,0,0,.08)}
.brand-title{font-size:1.35rem;font-weight:950;color:#171a21;line-height:1.02;letter-spacing:-.02em}
.brand-sub{font-size:.75rem;color:#7a8190;margin-top:5px;font-weight:600}
.live-pill{display:inline-flex;align-items:center;gap:6px;padding:7px 10px;border-radius:9px;background:#fff5f5;color:#c41724;border:1px solid #ffd7da;font-size:.69rem;font-weight:900;white-space:nowrap}
.title{font-size:1.1rem;font-weight:900;color:var(--ink);margin:15px 0 4px}
.subtitle{color:var(--muted);font-size:.78rem;margin-bottom:8px}
.match-card{background:#fff;border:1px solid var(--line);border-radius:14px;margin:9px 0;overflow:hidden;box-shadow:0 2px 8px rgba(17,24,39,.035)}
.mc-head{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:9px 13px;background:#fafafa;border-bottom:1px solid var(--line);color:#6b7280;font-size:.73rem}
.rank{background:#fee2e2;color:var(--red-dark);padding:4px 8px;border-radius:8px;font-weight:900}
.mc-body{display:grid;grid-template-columns:1.15fr .85fr;gap:14px;align-items:center;padding:13px 14px 11px}
.teams{display:grid;grid-template-columns:1fr 28px 1fr;gap:8px;align-items:center}
.team{display:flex;align-items:center;gap:8px;min-width:0}
.team.r{justify-content:flex-end;text-align:right}
.badge{width:38px;height:38px;border-radius:10px;background:#f3f4f6;border:1px solid var(--line);display:grid;place-items:center;font-size:.7rem;font-weight:900;color:#4b5563;flex:none}
.tn{font-size:.92rem;font-weight:850;color:var(--ink);line-height:1.1}
.vs{text-align:center;font-weight:900;color:#9ca3af}
.pick{display:grid;grid-template-columns:auto 1fr;gap:6px 12px;align-items:center;padding:10px 12px;border:1px solid #dcfce7;background:#f0fdf4;border-radius:12px}
.prob{font-size:1.7rem;font-weight:950;letter-spacing:-.03em;color:#111827}
.market{font-weight:900;color:#111827}
.conf{justify-self:end;background:#dcfce7;color:#166534;padding:5px 8px;border-radius:8px;font-size:.72rem;font-weight:900}
.bar{grid-column:1/-1;height:6px;background:#d1fae5;border-radius:999px;overflow:hidden}
.bar span{display:block;height:100%;background:var(--green)}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);border-top:1px solid var(--line)}
.stat{background:#fafafa;padding:9px 8px;text-align:center}
.sk{font-size:.65rem;color:#6b7280}.sv{font-weight:900;color:#1f2937;margin-top:2px}
div[data-testid="stMetric"]{border:1px solid var(--line);border-radius:12px;padding:8px 10px;background:#fff;box-shadow:none}
.stButton button{border-radius:10px!important;font-weight:850!important;white-space:nowrap!important}
.stButton button[kind="primary"]{background:var(--red)!important;border-color:var(--red)!important}

.header-meta{display:flex;align-items:center;gap:10px}
.source-text{font-size:.68rem;color:#8a91a0;font-weight:700}


.daily-wrap{margin-top:12px;border:1px solid #e5e7eb;border-radius:14px;overflow:hidden;background:#fff}
.daily-head{display:grid;grid-template-columns:72px 1.65fr repeat(6,.72fr);gap:0;background:#f3f4f6;border-bottom:1px solid #e5e7eb;font-size:.68rem;font-weight:900;color:#596273}
.daily-head div,.daily-row>div{padding:9px 8px;border-right:1px solid #eceff3}
.daily-head div:last-child,.daily-row>div:last-child{border-right:none}
.daily-row{display:grid;grid-template-columns:72px 1.65fr repeat(6,.72fr);gap:0;border-bottom:1px solid #edf0f3;align-items:center;font-size:.76rem}
.daily-row:last-child{border-bottom:none}
.daily-row:hover{background:#fafafa}
.dtime{font-weight:900;color:#4b5563}
.dmatch{font-weight:850;color:#202733;line-height:1.2}
.dleague{display:block;font-size:.62rem;color:#9097a3;font-weight:600;margin-top:3px}
.dpct{text-align:center;font-weight:900}
.good{color:#11844b;background:#effbf4}
.mid{color:#9a6b00;background:#fff9e8}
.low{color:#7b8491;background:#f8f9fa}
@media(max-width:900px){
 .daily-head,.daily-row{grid-template-columns:58px 1.4fr repeat(6,.72fr)}
 .daily-head div,.daily-row>div{padding:7px 5px;font-size:.65rem}
}
</style>
""", unsafe_allow_html=True)

# =========================
# MAÇKOLİK VERİ
# =========================
class MackolikError(Exception):
    pass

def _get(row, idx, default=None):
    try:
        v = row[idx]
        return default if v is None else v
    except Exception:
        return default

def _to_int(v):
    try:
        if v in ("", None, "-", "null"): return None
        return int(v)
    except Exception:
        return None

def _is_football(row):
    try:
        return _get(row, 36, [])[11] != 2
    except Exception:
        return True

def _league_name(row):
    try:
        v = _get(row, 36, [])[1]
        if v:
            return str(v).strip()
    except Exception:
        pass
    return "Diğer"

def _finished_score(row):
    status = str(_get(row, 6, "") or "").strip().casefold()
    finished_values = {"ms", "bitti", "ft", "sona erdi"}
    if status not in finished_values:
        return None
    h = _to_int(_get(row, 12))
    a = _to_int(_get(row, 13))
    if h is not None and a is not None:
        return h, a
    return None

def normalize_match(row, day):
    if not isinstance(row, list) or not _is_football(row):
        return None
    home = str(_get(row,2,"") or "").strip()
    away = str(_get(row,4,"") or "").strip()
    if not home or not away:
        return None

    score = _finished_score(row)
    minute = str(_get(row,6,"") or "").strip()
    live_h = _to_int(_get(row,12))
    live_a = _to_int(_get(row,13))

    finished = score is not None
    status_text = minute.casefold()
    live = (
        not finished
        and (
            minute.isdigit()
            or status_text in {"iy", "i̇y", "devre", "uz", "pen"}
        )
    )
    status = "FINISHED" if finished else ("LIVE" if live else "SCHEDULED")

    return {
        "id": _get(row,0,""),
        "date": str(_get(row,35,"") or day.strftime("%d/%m/%Y")),
        "date_iso": day.isoformat(),
        "time": str(_get(row,16,"") or "").strip(),
        "minute": minute,
        "status": status,
        "league": _league_name(row),
        "home": home,
        "away": away,
        "home_score": score[0] if score else None,
        "away_score": score[1] if score else None,
        "live_home_score": live_h,
        "live_away_score": live_a,
    }

def fetch_day(day):
    headers = {
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/152.0 Safari/537.36",
        "Accept":"application/json,text/plain,*/*",
        "Referer":"https://www.mackolik.com/",
    }
    params = {"date":day.strftime("%d/%m/%Y"), "_":int(time.time()*1000)}
    try:
        r = requests.get(BASE_URL, params=params, headers=headers, timeout=18)
    except requests.RequestException as e:
        raise MackolikError(f"Maçkolik bağlantı hatası: {e}")
    if not r.ok:
        raise MackolikError(f"Maçkolik HTTP {r.status_code}")
    try:
        payload = r.json()
    except Exception:
        raise MackolikError("Maçkolik yanıtı JSON değil.")
    raw = payload.get("m")
    if not isinstance(raw, list):
        raise MackolikError("Maç listesi beklenen formatta gelmedi.")
    out=[]
    for row in raw:
        m = normalize_match(row, day)
        if m: out.append(m)
    return out

@st.cache_data(ttl=120, show_spinner=False)
def load_day(day_iso):
    return fetch_day(datetime.strptime(day_iso,"%Y-%m-%d").date())

@st.cache_data(ttl=3600, show_spinner=False)
def load_history(start_iso, end_iso):
    s = datetime.strptime(start_iso,"%Y-%m-%d").date()
    e = datetime.strptime(end_iso,"%Y-%m-%d").date()
    out=[]; errors=[]
    d=s
    while d<=e:
        try:
            out.extend(fetch_day(d))
        except Exception as exc:
            errors.append(f"{d.isoformat()}: {exc}")
        d += timedelta(days=1)
        if d<=e: time.sleep(.05)
    return out, errors

# =========================
# ANALİZ
# =========================
def _norm(name):
    return " ".join((name or "").casefold().split())

def build_team_history(matches):
    idx = defaultdict(list)
    for m in matches:
        if m.get("status") != "FINISHED":
            continue
        hg, ag = m.get("home_score"), m.get("away_score")
        if hg is None or ag is None:
            continue
        row = {
            "date_iso":m.get("date_iso",""),
            "home":m.get("home",""),
            "away":m.get("away",""),
            "hg":int(hg),"ag":int(ag),
            "league":m.get("league","")
        }
        idx[_norm(row["home"])].append(row)
        idx[_norm(row["away"])].append(row)
    for k in idx:
        idx[k].sort(key=lambda x:x["date_iso"], reverse=True)
    return idx

def _hit(r, market):
    total = r["hg"]+r["ag"]
    btts = r["hg"]>0 and r["ag"]>0
    return {
        "1.5 Üst": total>=2,
        "2.5 Üst": total>=3,
        "3.5 Üst": total>=4,
        "3.5 Alt": total<=3,
        "KG Var": btts,
        "KG Yok": not btts,
    }[market]

def _rate(rows, market, prior=3.0):
    if not rows: return .50,0
    hits=sum(_hit(r,market) for r in rows)
    return (hits+.5*prior)/(len(rows)+prior),len(rows)

def _venue(rows, team, home=True):
    n=_norm(team)
    return [r for r in rows if _norm(r["home"] if home else r["away"])==n]

def _team_goals(rows, team):
    if not rows: return 0,0
    n=_norm(team); gf=ga=0
    for r in rows:
        if _norm(r["home"])==n:
            gf+=r["hg"]; ga+=r["ag"]
        else:
            gf+=r["ag"]; ga+=r["hg"]
    return gf/len(rows), ga/len(rows)

def analyze(fixture, idx, market, sample_size=8):
    home,away=fixture["home"],fixture["away"]
    hr=(idx.get(_norm(home)) or [])[:sample_size]
    ar=(idx.get(_norm(away)) or [])[:sample_size]
    if len(hr)<3 or len(ar)<3: return None

    hh=_venue(hr,home,True); aa=_venue(ar,away,False)
    h_all,hn=_rate(hr,market); a_all,an=_rate(ar,market)
    hv,hhn=_rate(hh,market); av,aan=_rate(aa,market)

    raw=.34*h_all+.34*a_all+.16*hv+.16*av
    evidence=min(hn,sample_size)+min(an,sample_size)+min(hhn,5)+min(aan,5)
    trust=min(1.0,evidence/24.0)
    p=.50+(raw-.50)*(.60+.40*trust)
    p=min(.94,max(.06,p))

    hgf,hga=_team_goals(hr,home); agf,aga=_team_goals(ar,away)
    merged=hr+ar
    btts=sum((r["hg"]>0 and r["ag"]>0) for r in merged)/len(merged)
    over25=sum((r["hg"]+r["ag"]>=3) for r in merged)/len(merged)

    pct=p*100
    label="Çok güçlü" if pct>=82 else "Güçlü" if pct>=75 else "Orta" if pct>=68 else "Sınırda"

    return {
        **fixture,
        "market":market,"probability":pct,"confidence":label,
        "sample_count":hn+an,
        "avg_goals":((hgf+hga)+(agf+aga))/2,
        "btts_rate":btts*100,
        "over25_rate":over25*100,
        "home_rate":h_all*100,"away_rate":a_all*100,
        "details":{
            f"{home} son {hn}":round(h_all*100,1),
            f"{away} son {an}":round(a_all*100,1),
            "Ev sahibi iç saha":round(hv*100,1),
            "Deplasman dış saha":round(av*100,1),
            "Veri güveni":round(trust*100,0),
        }
    }

def strongest(fixture, idx, sample_size=8):
    rows=[analyze(fixture,idx,m,sample_size) for m in MARKETS]
    rows=[x for x in rows if x]
    return max(rows,key=lambda x:x["probability"]) if rows else None

def all_market_scores(fixture, idx, sample_size=8):
    out={}
    for market in MARKETS:
        r=analyze(fixture,idx,market,sample_size)
        out[market]=None if not r else r["probability"]
    return out

def score_cell(value):
    if value is None:
        return '<div class="dpct low">—</div>'
    cls="good" if value>=70 else ("mid" if value>=60 else "low")
    return f'<div class="dpct {cls}">%{value:.0f}</div>'

def initials(name):
    parts=[p for p in (name or "").replace("-"," ").split() if p]
    return "".join(x[0] for x in parts[:2]).upper() or "FC"

# =========================
# UI — MAÇKOLİK TARZI GÜNLÜK LİSTE
# =========================
today = datetime.now(ZoneInfo("Europe/Istanbul")).date()

with st.sidebar:
    st.markdown("## ONUR")
    st.caption("Günlük Futbol Tahminleri")
    st.divider()
    st.markdown('<span class="live-pill">● MAÇKOLİK VERİ MODU</span>', unsafe_allow_html=True)
    st.markdown("### Tahmin Ayarları")
    history_days=st.select_slider("Geçmiş taraması",[14,21,30],value=21,format_func=lambda x:f"{x} gün")
    sample_size=st.select_slider("Takım başına son maç",[5,6,8,10],value=8)
    st.divider()
    st.caption("Maçlar seçilen tarihte otomatik listelenir.")

st.markdown("""
<div class="topbar">
  <div class="brand-wrap">
    <div class="brand-mark">⚽</div>
    <div>
      <div class="brand-title">GÜNLÜK FUTBOL TAHMİNLERİ</div>
      <div class="brand-sub">Seçili üst ligler • günlük maç listesi • gol market tahminleri</div>
    </div>
  </div>
  <div class="header-meta">
    <div class="source-text">Veri Kaynağı</div>
    <div class="live-pill">● MAÇKOLİK</div>
  </div>
</div>
""", unsafe_allow_html=True)

# Date navigation — like a daily fixtures site.
c1,c2,c3,c4 = st.columns([1.25,.85,1.45,3.6])
with c1:
    prev_click = st.button("← Önceki Gün", use_container_width=True)
with c2:
    today_click = st.button("Bugün", use_container_width=True)
with c3:
    chosen = st.date_input("Tarih", value=st.session_state.get("daily_date", today), label_visibility="collapsed")
with c4:
    pass

if "daily_date" not in st.session_state:
    st.session_state.daily_date = today
if prev_click:
    st.session_state.daily_date = st.session_state.daily_date - timedelta(days=1)
    st.rerun()
if today_click:
    st.session_state.daily_date = today
    st.rerun()
if chosen != st.session_state.daily_date:
    st.session_state.daily_date = chosen
    st.rerun()

selected_date = st.session_state.daily_date

# Load selected day's matches.
try:
    selected = load_day(selected_date.isoformat())
except Exception as exc:
    selected = []
    st.error(f"Maçkolik verisi alınamadı: {exc}")

# Sadece kullanıcının istediği erkek A takım ligleri.
# Kadın, U21/U19/U23, rezerv, gençlik ve diğer ligler filtrelenir.
EXCLUDE_WORDS = [
    "kadın", "kadin", "women", "woman", "femin", "female",
    "u21", "u-21", "u19", "u-19", "u23", "u-23", "u18", "u-18",
    "u17", "u-17", "u16", "u-16", "youth", "genç", "genc",
    "reserve", "rezerv", "academy", "akademi",
    "kupa", "cup", "trophy", "play off", "play-off"
]

LEAGUE_GROUPS = [
    ("🇹🇷 Türkiye • Süper Lig", []),
    ("🏴 İngiltere • Premier League", []),
    ("🏴 İngiltere • Championship", []),
    ("🏴 İngiltere • League One", []),
    ("🏴 İngiltere • League Two", []),
    ("🇪🇸 İspanya • La Liga", []),
    ("🇫🇷 Fransa • Ligue 1", []),
    ("🇮🇹 İtalya • Serie A", []),
    ("🇵🇹 Portekiz • Primeira Liga", []),
    ("🇩🇰 Danimarka • Superliga", []),
    ("🇳🇴 Norveç • Eliteserien", []),
    ("🇸🇪 İsveç • Allsvenskan", []),
    ("🇨🇭 İsviçre • Super League", []),
]

def clean_text(text):
    s = (text or "").casefold()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    for ch in ["–","—","-","/","_",".",":","(",")"]:
        s = s.replace(ch, " ")
    return " ".join(s.split())

def wanted_league_group(league_name):
    n = clean_text(league_name)

    blocked = [
        "kadin","women","woman","female","femin",
        "u21","u 21","u19","u 19","u23","u 23","u18","u 18",
        "u17","u 17","u16","u 16","youth","genc","reserve",
        "rezerv","academy","akademi"
    ]
    if any(x in n for x in blocked):
        return None

    # 1) Türkiye Süper Lig — sponsor adıyla da gelebilir.
    if "trendyol super lig" in n or n == "super lig" or ("turkiye" in n and "super lig" in n):
        return "🇹🇷 Türkiye • Süper Lig"

    # 2) İngiltere
    if "championship" in n:
        return "🏴 İngiltere • Championship"
    if "league one" in n:
        return "🏴 İngiltere • League One"
    if "league two" in n:
        return "🏴 İngiltere • League Two"
    if "premier league" in n or "premier lig" in n:
        # Portekiz adı açıkça yazıyorsa İngiltere sayma.
        if "portekiz" not in n and "portugal" not in n:
            return "🏴 İngiltere • Premier League"

    # 3) İspanya
    if "laliga" in n or "la liga" in n or "primera division" in n:
        return "🇪🇸 İspanya • La Liga"

    # 4) Fransa
    if "ligue 1" in n:
        return "🇫🇷 Fransa • Ligue 1"

    # 5) İtalya
    if "serie a" in n:
        # Brezilya Serie A'yı alma.
        if "brezilya" not in n and "brazil" not in n:
            return "🇮🇹 İtalya • Serie A"

    # 6) Portekiz
    if "primeira liga" in n or "liga portugal" in n or (
        ("portekiz" in n or "portugal" in n) and ("premier" in n or "1 lig" in n)
    ):
        return "🇵🇹 Portekiz • Primeira Liga"

    # 7) Danimarka
    if "superligaen" in n or (
        ("danimarka" in n or "denmark" in n) and ("superliga" in n or "super lig" in n)
    ):
        return "🇩🇰 Danimarka • Superliga"

    # 8) Norveç
    if "eliteserien" in n:
        return "🇳🇴 Norveç • Eliteserien"

    # 9) İsveç
    if "allsvenskan" in n:
        return "🇸🇪 İsveç • Allsvenskan"

    # 10) İsviçre
    if "swiss super league" in n or (
        ("isvicre" in n or "switzerland" in n or "swiss" in n) and
        ("super league" in n or "super lig" in n)
    ):
        return "🇨🇭 İsviçre • Super League"

    return None

# Matchleri yalnızca whitelist liglerde tut.
raw_selected = list(selected)
filtered_selected = []
for m in raw_selected:
    group = wanted_league_group(m.get("league") or "")
    if group:
        m = dict(m)
        m["display_league"] = group
        filtered_selected.append(m)
selected = filtered_selected

# Güvenli fallback: filtre adı değişirse uygulama boş kalmasın.
if not selected and raw_selected:
    fallback = []
    for m in raw_selected:
        lname = clean_text(m.get("league") or "")
        if not any(x in lname for x in ["kadin","women","u21","u 21","u19","u 19","u23","u 23","youth","genc","reserve","rezerv"]):
            mm = dict(m)
            mm["display_league"] = m.get("league") or "Diğer"
            fallback.append(mm)
    selected = fallback

# Always show every football match for the selected date.
league_order = {label:i for i,(label,_) in enumerate(LEAGUE_GROUPS)}
selected = sorted(
    selected,
    key=lambda m: (
        league_order.get(m.get("display_league"), 999),
        m.get("time") or "99:99",
        (m.get("home") or "").casefold()
    )
)

# History is loaded automatically, so the user does not have to press an Analyse button.
hist_end = selected_date - timedelta(days=1)
hist_start = hist_end - timedelta(days=history_days-1)

with st.spinner("Günün maçları ve tahmin yüzdeleri hazırlanıyor..."):
    history, history_errors = load_history(hist_start.isoformat(), hist_end.isoformat())
    history_idx = build_team_history(history)

# Compute predictions for every scheduled/live fixture. Completed games stay visible with result.
daily_rows = []
for fixture in selected:
    scores = all_market_scores(fixture, history_idx, sample_size)
    daily_rows.append({**fixture, "scores": scores})

leagues = []
for label, _ in LEAGUE_GROUPS:
    if any(m.get("display_league") == label for m in daily_rows):
        leagues.append(label)

st.markdown(
    f'<div class="title">⚽ {selected_date.strftime("%d.%m.%Y")} GÜNÜN MAÇLARI</div>',
    unsafe_allow_html=True
)
st.markdown(
    f'<div class="subtitle">{len(daily_rows)} seçili lig maçı • {len(leagues)} lig • tahminler otomatik hesaplandı</div>',
    unsafe_allow_html=True
)

st.caption(f"Maçkolik ham futbol maçı: {len(raw_selected)} • Ekranda gösterilen: {len(daily_rows)}")

if history_errors:
    st.caption(f"Not: Geçmiş veride {len(history_errors)} gün alınamadı; mevcut verilerle tahmin üretildi.")

# Optional compact league filter, but default remains ALL matches.
filter_options = ["🌍 Tüm Maçlar"] + leagues
league_choice = st.selectbox("Lig filtresi", filter_options)

if league_choice == "🌍 Tüm Maçlar":
    visible_rows = daily_rows
else:
    visible_rows = [m for m in daily_rows if m.get("display_league") == league_choice]

def pct_html(v):
    if v is None:
        return '<span class="pred pred-none">—</span>'
    cls = "pred-strong" if v >= 70 else ("pred-mid" if v >= 60 else "pred-low")
    return f'<span class="pred {cls}">%{v:.0f}</span>'

# Extra CSS for Mackolik-like grouped fixture list.
st.markdown("""
<style>
.fixture-league{
  margin-top:22px;
  padding:13px 15px;
  background:linear-gradient(180deg,#ffffff 0%,#f6f7f9 100%);
  border:1px solid #dde2e8;
  border-left:5px solid #e31d2b;
  border-bottom:none;
  border-radius:14px 14px 0 0;
  font-size:1.02rem;
  font-weight:950;
  letter-spacing:-.015em;
  color:#171a21;
  box-shadow:0 6px 18px rgba(17,24,39,.04);
}
.fixture-head,.fixture-row{
  display:grid;
  grid-template-columns:64px minmax(260px,1.8fr) repeat(6,minmax(70px,.62fr));
  align-items:stretch;
}
.fixture-head{
  background:#f2f4f7;
  border:1px solid #dde2e8;
  font-size:.67rem;
  font-weight:950;
  color:#596273;
  text-transform:uppercase;
  letter-spacing:.02em;
}
.fixture-head>div,.fixture-row>div{
  padding:8px 7px;
  border-right:1px solid #edf0f3;
}
.fixture-head>div:last-child,.fixture-row>div:last-child{border-right:none}
.fixture-row{
  border-left:1px solid #e1e5ea;
  border-right:1px solid #e1e5ea;
  border-bottom:1px solid #e8ebef;
  background:#fff;
  font-size:.78rem;
  min-height:44px;
}
.fixture-row:last-child{border-radius:0 0 10px 10px}
.fixture-row:hover{background:#fbfbfc}
.fx-time{font-weight:900;color:#5b6473;text-align:center}
.fx-match{font-weight:850;color:#202733}
.fx-score{font-weight:950;color:#111827;margin-left:7px}
.fx-market{text-align:center}
.pred{display:inline-block;min-width:44px;padding:3px 5px;border-radius:6px;font-weight:900;text-align:center}
.pred-strong{background:#e9f9ef;color:#08783e}
.pred-mid{background:#fff5d9;color:#9a6700}
.pred-low{background:#f4f5f7;color:#707988}
.pred-none{background:#f7f7f8;color:#a0a6af}
@media(max-width:1000px){
  .fixture-head,.fixture-row{grid-template-columns:55px minmax(190px,1.5fr) repeat(6,62px)}
}
</style>
""", unsafe_allow_html=True)

if not visible_rows:
    st.info("Bu tarihte seçili liglerde eşleşen maç bulunamadı.")
    raw_leagues = sorted({m.get("league") for m in raw_selected if m.get("league")})
    with st.expander("Maçkolikten gelen gerçek lig adlarını göster"):
        st.write(f"Toplam ham futbol maçı: {len(raw_selected)}")
        for rl in raw_leagues:
            st.write("•", rl)
else:
    # Group matches by league, exactly like a fixture/results page.
    grouped = {}
    for m in visible_rows:
        grouped.setdefault(m.get("display_league") or "Diğer", []).append(m)

    for league_name, matches in grouped.items():
        st.markdown(f'<div class="fixture-league">🌐 {escape(league_name)}</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="fixture-head">
          <div>Saat</div>
          <div>Maç</div>
          <div>1.5 Üst</div>
          <div>2.5 Üst</div>
          <div>3.5 Üst</div>
          <div>3.5 Alt</div>
          <div>KG Var</div>
          <div>KG Yok</div>
        </div>
        """, unsafe_allow_html=True)

        for m in matches:
            s = m["scores"]
            if m.get("status") == "FINISHED":
                status_text = f'{m.get("home_score","")}-{m.get("away_score","")}'
            elif m.get("status") == "LIVE":
                status_text = f'{m.get("live_home_score","")}-{m.get("live_away_score","")}'
            else:
                status_text = ""

            row_html = f"""
            <div class="fixture-row">
              <div class="fx-time">{escape(str(m.get("time") or "—"))}</div>
              <div class="fx-match">{escape(m.get("home",""))} <span style="color:#a1a7b1">-</span> {escape(m.get("away",""))}
                <span class="fx-score">{escape(status_text)}</span>
              </div>
              <div class="fx-market">{pct_html(s.get("1.5 Üst"))}</div>
              <div class="fx-market">{pct_html(s.get("2.5 Üst"))}</div>
              <div class="fx-market">{pct_html(s.get("3.5 Üst"))}</div>
              <div class="fx-market">{pct_html(s.get("3.5 Alt"))}</div>
              <div class="fx-market">{pct_html(s.get("KG Var"))}</div>
              <div class="fx-market">{pct_html(s.get("KG Yok"))}</div>
            </div>
            """
            st.markdown(row_html, unsafe_allow_html=True)

st.caption("Tahmin yüzdeleri geçmiş maç istatistiklerinden üretilen model skorlarıdır; kesin sonuç veya bahis garantisi değildir.")

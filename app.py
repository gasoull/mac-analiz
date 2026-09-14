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

.premium-match-hero{
  margin-top:18px;
  border-radius:18px;
  overflow:hidden;
  background:
    radial-gradient(circle at 50% 0%, rgba(64,122,190,.26), transparent 35%),
    linear-gradient(135deg,#101925,#17283a 55%,#0e1723);
  color:#fff;
  box-shadow:0 14px 34px rgba(15,23,42,.16);
  border:1px solid #25384c;
}
.pmh-top{
  display:flex;
  justify-content:space-between;
  align-items:center;
  padding:13px 16px;
  font-size:.74rem;
  color:#cbd5e1;
  border-bottom:1px solid rgba(255,255,255,.08);
}
.pmh-main{
  display:grid;
  grid-template-columns:1fr 90px 1fr;
  gap:18px;
  align-items:center;
  padding:24px 22px 26px;
}
.pmh-team{
  display:flex;
  flex-direction:column;
  align-items:center;
  text-align:center;
  gap:8px;
}
.pmh-badge{
  width:66px;height:66px;border-radius:18px;
  display:grid;place-items:center;
  background:rgba(255,255,255,.10);
  border:1px solid rgba(255,255,255,.15);
  font-size:1.05rem;font-weight:950;
  backdrop-filter:blur(6px);
}
.pmh-name{font-size:1.08rem;font-weight:950}
.pmh-center{text-align:center}
.pmh-time{font-size:1.72rem;font-weight:950;letter-spacing:-.03em}
.pmh-vs{font-size:.7rem;color:#94a3b8;font-weight:900;margin-bottom:3px}
.pmh-form{
  display:flex;gap:4px;justify-content:center;margin-top:3px
}
.form-dot{
  width:22px;height:22px;border-radius:6px;display:grid;place-items:center;
  font-size:.62rem;font-weight:950;color:white
}
.form-g{background:#20b26b}.form-b{background:#94a3b8}.form-m{background:#e34b5a}
.premium-grid{
  display:grid;
  grid-template-columns:repeat(4,1fr);
  gap:12px;
  margin:14px 0;
}
.premium-card{
  background:#fff;border:1px solid #e3e8ef;border-radius:16px;
  padding:15px 16px;box-shadow:0 6px 20px rgba(15,23,42,.04);
}
.premium-card.strong{
  background:linear-gradient(135deg,#f0fff7,#e8fbf0);
  border-color:#c9f0d9;
}
.pc-label{
  font-size:.68rem;font-weight:950;color:#64748b;text-transform:uppercase;
  letter-spacing:.02em;margin-bottom:10px
}
.pc-value{
  font-size:1.55rem;font-weight:950;color:#111827;letter-spacing:-.03em
}
.pc-sub{font-size:.74rem;color:#64748b;margin-top:4px}
.pbar{height:7px;border-radius:999px;background:#e8edf2;overflow:hidden;margin-top:11px}
.pbar span{display:block;height:100%;background:linear-gradient(90deg,#2aa96b,#57d89a)}
.premium-section{
  background:#fff;border:1px solid #e3e8ef;border-radius:16px;
  padding:16px;margin-top:12px;box-shadow:0 6px 20px rgba(15,23,42,.035)
}
.premium-section-title{font-weight:950;color:#172033;margin-bottom:12px}
.premium-two{
  display:grid;grid-template-columns:1fr 1fr;gap:14px
}
.team-form-card{
  background:#f8fafc;border:1px solid #edf1f5;border-radius:13px;padding:13px
}
.team-form-name{font-weight:950;color:#172033;margin-bottom:8px}
.stat-line{
  display:flex;justify-content:space-between;gap:12px;
  padding:7px 0;border-bottom:1px dashed #e5e7eb;font-size:.76rem
}
.stat-line:last-child{border-bottom:none}
.conf-pill{
  display:inline-block;padding:5px 9px;border-radius:999px;
  background:#e8faf1;color:#0c8a4c;font-size:.69rem;font-weight:950
}
@media(max-width:900px){
  .premium-grid{grid-template-columns:1fr 1fr}
  .premium-two{grid-template-columns:1fr}
  .pmh-main{grid-template-columns:1fr 70px 1fr;padding:18px 10px}
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
    return _get(row, 23) in (1, "1")


def _league_name(row):
    meta = _get(row, 36, []) or []
    try:
        country = str(meta[1] or "").strip()
    except Exception:
        country = ""
    try:
        division = str(meta[3] or "").strip()
    except Exception:
        division = ""
    if country and division:
        return f"{country} • {division}"
    return division or country or "Diğer"

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

    meta = _get(row,36,[]) or []
    try:
        league_group_id = meta[0]
    except Exception:
        league_group_id = None
    try:
        country_raw = str(meta[1] or "").strip()
    except Exception:
        country_raw = ""
    try:
        division_raw = str(meta[3] or "").strip()
    except Exception:
        division_raw = ""
    try:
        league_code = str(meta[9] or "").strip()
    except Exception:
        league_code = ""
    league_raw = " • ".join(x for x in [country_raw, division_raw] if x) or _league_name(row)

    return {
        "id": _get(row,0,""),
        "date": str(_get(row,35,"") or day.strftime("%d/%m/%Y")),
        "date_iso": day.isoformat(),
        "time": str(_get(row,16,"") or "").strip(),
        "minute": minute,
        "status": status,
        "league": league_raw or _league_name(row),
        "country": country_raw,
        "division": division_raw,
        "league_code": league_code,
        "league_group_id": league_group_id,
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
def load_day_v103(day_iso, cache_version="v10.3"):
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


def best_market_detail(fixture, idx, sample_size=8):
    rows=[]
    for market in MARKETS:
        r=analyze(fixture, idx, market, sample_size)
        if r:
            rows.append(r)
    if not rows:
        return None
    rows.sort(key=lambda x:x["probability"], reverse=True)
    return rows[0]

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
      <div class="brand-sub">Seçili liglerin günlük maçları • gol market tahminleri</div>
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
    selected = load_day_v103(selected_date.isoformat(), "v10.3-u21-final-filter")
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
    "🇹🇷 Türkiye • Süper Lig",
    "🏴 İngiltere • Premier League",
    "🏴 İngiltere • Championship",
    "🏴 İngiltere • League One",
    "🏴 İngiltere • League Two",
    "🇪🇸 İspanya • La Liga",
    "🇫🇷 Fransa • Ligue 1",
    "🇮🇹 İtalya • Serie A",
    "🇵🇹 Portekiz • Primeira Liga",
    "🇩🇰 Danimarka • Superliga",
    "🇳🇴 Norveç • Eliteserien",
    "🇸🇪 İsveç • Allsvenskan",
    "🇨🇭 İsviçre • Super League",
]

def clean_text(text):
    s = (text or "").casefold()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    for ch in ["–","—","-","/","_",".",":","(",")","[","]"]:
        s = s.replace(ch, " ")
    return " ".join(s.split())

BLOCKED_TERMS = [
    "kadin","women","woman","female","femin",
    "u21","u 21","u19","u 19","u23","u 23","u18","u 18",
    "u17","u 17","u16","u 16","youth","genc","reserve",
    "rezerv","academy","akademi"
]

def classify_league(match):
    # Backward-compatible: accept either a normalized match dict or a league-name string.
    if isinstance(match, dict):
        country = clean_text(match.get("country") or "")
        division = clean_text(match.get("division") or "")
        code = clean_text(match.get("league_code") or "")
        whole = clean_text(match.get("league") or "")
    else:
        country = ""
        division = ""
        code = ""
        whole = clean_text(str(match or ""))
        # Parse our normalized "Country • Division" representation when present.
        if " • " in str(match or ""):
            parts = str(match).split(" • ", 1)
            country = clean_text(parts[0])
            division = clean_text(parts[1])

    if any(x in division for x in BLOCKED_TERMS) or any(x in whole for x in BLOCKED_TERMS):
        return None

    # Türkiye
    if country in {"turkiye", "turkey"}:
        if "super lig" in division or code == "ssl":
            return "🇹🇷 Türkiye • Süper Lig"
        return None

    # İngiltere
    if country in {"ingiltere", "england"}:
        if "premier" in division:
            return "🏴 İngiltere • Premier League"
        if "championship" in division:
            return "🏴 İngiltere • Championship"
        if "league one" in division or division in {"1 lig", "1lig"}:
            return "🏴 İngiltere • League One"
        if "league two" in division or division in {"2 lig", "2lig"}:
            return "🏴 İngiltere • League Two"
        return None

    # İspanya
    if country in {"ispanya", "spain"}:
        if "laliga" in division or "la liga" in division or "primera division" in division:
            return "🇪🇸 İspanya • La Liga"
        return None

    # Fransa
    if country in {"fransa", "france"}:
        if "ligue 1" in division:
            return "🇫🇷 Fransa • Ligue 1"
        return None

    # İtalya
    if country in {"italya", "italy"}:
        if "serie a" in division:
            return "🇮🇹 İtalya • Serie A"
        return None

    # Portekiz
    if country in {"portekiz", "portugal"}:
        if "primeira" in division or "liga portugal" in division or "premier" in division:
            return "🇵🇹 Portekiz • Primeira Liga"
        return None

    # Danimarka
    if country in {"danimarka", "denmark"}:
        if "superliga" in division or "super lig" in division:
            return "🇩🇰 Danimarka • Superliga"
        return None

    # Norveç
    if country in {"norvec", "norway"}:
        if "eliteserien" in division:
            return "🇳🇴 Norveç • Eliteserien"
        return None

    # İsveç
    if country in {"isvec", "sweden"}:
        if "allsvenskan" in division:
            return "🇸🇪 İsveç • Allsvenskan"
        return None

    # İsviçre
    if country in {"isvicre", "switzerland"}:
        if "super league" in division or "super lig" in division:
            return "🇨🇭 İsviçre • Super League"
        return None

    return None

# Ham Maçkolik maçlarını sadece istenen lig gruplarına eşle.
raw_selected = list(selected)
selected = []
for m in raw_selected:
    label = classify_league(m)
    if label:
        mm = dict(m)
        mm["display_league"] = label
        selected.append(mm)

# Always show every football match for the selected date.
league_order = {label:i for i,label in enumerate(LEAGUE_GROUPS)}
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
# U21/U23/U19/U18/U17/U16, youth, academy and reserve matches
# must never reach the visible daily list.
def is_senior_match(fixture):
    text = clean_text(" ".join([
        str(fixture.get("home") or ""),
        str(fixture.get("away") or ""),
        str(fixture.get("league") or ""),
        str(fixture.get("division") or ""),
    ]))
    forbidden = [
        "u21", "u 21", "under 21", "under21",
        "u23", "u 23", "under 23", "under23",
        "u19", "u 19", "under 19", "under19",
        "u18", "u 18", "u17", "u 17", "u16", "u 16",
        "youth", "academy", "akademi",
        "reserve", "rezerv", "development",
        "premier league 2"
    ]
    return not any(term in text for term in forbidden)

selected = [m for m in selected if is_senior_match(m)]

daily_rows = []
for fixture in selected:
    scores = all_market_scores(fixture, history_idx, sample_size)
    daily_rows.append({**fixture, "scores": scores})

available_leagues = {
    m.get("display_league") for m in daily_rows if m.get("display_league")
}
leagues = [label for label in LEAGUE_GROUPS if label in available_leagues]

st.markdown(
    f'<div class="title">⚽ {selected_date.strftime("%d.%m.%Y")} GÜNÜN MAÇLARI</div>',
    unsafe_allow_html=True
)
st.markdown(
    f'<div class="subtitle">{len(daily_rows)} seçili lig maçı • {len(leagues)} lig • tahminler otomatik hesaplandı</div>',
    unsafe_allow_html=True
)

st.caption(f"Maçkolik ham futbol maçı: {len(raw_selected)} • Seçili liglerde gösterilen: {len(daily_rows)}")

if history_errors:
    st.caption(f"Not: Geçmiş veride {len(history_errors)} gün alınamadı; mevcut verilerle tahmin üretildi.")

# Sabit lig menüsü: sadece kullanıcının istediği ligler.
filter_options = ["⭐ Tüm Seçili Ligler"] + LEAGUE_GROUPS
league_choice = st.selectbox("Lig filtresi", filter_options)

if league_choice == "⭐ Tüm Seçili Ligler":
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
  margin-top:24px;
  padding:15px 17px;
  background:linear-gradient(135deg,#ffffff 0%,#f6f7f9 100%);
  border:1px solid #dce1e7;
  border-left:6px solid #e31d2b;
  border-bottom:none;
  border-radius:15px 15px 0 0;
  font-size:1.16rem;
  font-weight:950;
  letter-spacing:-.02em;
  color:#151922;
  box-shadow:0 7px 22px rgba(17,24,39,.055);
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
    st.info("Seçtiğin ligde bu tarihte maç bulunmuyor. Üst menüden başka bir lig veya Tüm Seçili Ligler seçebilirsin.")
    raw_leagues = sorted({m.get("league") for m in raw_selected if m.get("league")})
    with st.expander("Teknik kontrol • Maçkolik lig adları"):
        st.write(f"Toplam ham futbol maçı: {len(raw_selected)}")
        seen=set()
        for mm in raw_selected:
            key=(mm.get("country"), mm.get("division"), mm.get("league_code"))
            if key in seen:
                continue
            seen.add(key)
            st.write(f"• {key[0]} — {key[1]} — Kod: {key[2]}")
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


# =========================
# PREMIUM MAÇ DETAYI
# =========================
if visible_rows:
    st.markdown('<div class="title">📊 Premium Maç Analizi</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Maçı seç; güçlü tahmin, olasılıklar ve form verileri tek ekranda.</div>', unsafe_allow_html=True)

    match_labels = [
        f'{m.get("time") or "—"} • {m.get("home","")} - {m.get("away","")} • {m.get("display_league","")}'
        for m in visible_rows
    ]
    selected_match_label = st.selectbox("Maç seç", match_labels)
    selected_match = visible_rows[match_labels.index(selected_match_label)]

    detail = best_market_detail(selected_match, history_idx, sample_size)
    market_scores = all_market_scores(selected_match, history_idx, sample_size)

    home = selected_match.get("home","")
    away = selected_match.get("away","")
    league = selected_match.get("display_league","")
    tm = selected_match.get("time") or "—"

    st.markdown(f"""
    <div class="premium-match-hero">
      <div class="pmh-top">
        <div>{escape(league)}</div>
        <div>{selected_date.strftime("%d.%m.%Y")} • {escape(str(tm))}</div>
      </div>
      <div class="pmh-main">
        <div class="pmh-team">
          <div class="pmh-badge">{escape(initials(home))}</div>
          <div class="pmh-name">{escape(home)}</div>
          <div class="pmh-form">
            <div class="form-dot form-g">G</div><div class="form-dot form-g">G</div><div class="form-dot form-b">B</div><div class="form-dot form-m">M</div><div class="form-dot form-g">G</div>
          </div>
        </div>
        <div class="pmh-center">
          <div class="pmh-vs">VS</div>
          <div class="pmh-time">{escape(str(tm))}</div>
        </div>
        <div class="pmh-team">
          <div class="pmh-badge">{escape(initials(away))}</div>
          <div class="pmh-name">{escape(away)}</div>
          <div class="pmh-form">
            <div class="form-dot form-g">G</div><div class="form-dot form-b">B</div><div class="form-dot form-m">M</div><div class="form-dot form-g">G</div><div class="form-dot form-b">B</div>
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if detail:
        best_pct = detail["probability"]
        kg_pct = market_scores.get("KG Var")
        over15 = market_scores.get("1.5 Üst")
        over25 = market_scores.get("2.5 Üst")

        def safe_pct(v):
            return 0 if v is None else max(0,min(100,v))

        st.markdown(f"""
        <div class="premium-grid">
          <div class="premium-card strong">
            <div class="pc-label">🏆 En Güçlü Tahmin</div>
            <div class="pc-value">{escape(detail["market"])}</div>
            <div class="pc-sub">%{best_pct:.0f} olasılık • <span class="conf-pill">{escape(detail["confidence"])}</span></div>
            <div class="pbar"><span style="width:{safe_pct(best_pct):.0f}%"></span></div>
          </div>
          <div class="premium-card">
            <div class="pc-label">⚽ 1.5 Üst</div>
            <div class="pc-value">%{safe_pct(over15):.0f}</div>
            <div class="pc-sub">Gol market olasılığı</div>
            <div class="pbar"><span style="width:{safe_pct(over15):.0f}%"></span></div>
          </div>
          <div class="premium-card">
            <div class="pc-label">🔥 2.5 Üst</div>
            <div class="pc-value">%{safe_pct(over25):.0f}</div>
            <div class="pc-sub">Gol market olasılığı</div>
            <div class="pbar"><span style="width:{safe_pct(over25):.0f}%"></span></div>
          </div>
          <div class="premium-card">
            <div class="pc-label">🤝 KG Var</div>
            <div class="pc-value">%{safe_pct(kg_pct):.0f}</div>
            <div class="pc-sub">İki takım da gol bulur</div>
            <div class="pbar"><span style="width:{safe_pct(kg_pct):.0f}%"></span></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="premium-section">
          <div class="premium-section-title">📈 Takım Formu ve Model Detayı</div>
          <div class="premium-two">
            <div class="team-form-card">
              <div class="team-form-name">{escape(home)}</div>
              <div class="stat-line"><span>Form skoru</span><b>%{detail["home_rate"]:.0f}</b></div>
              <div class="stat-line"><span>Ortalama toplam gol</span><b>{detail["avg_goals"]:.2f}</b></div>
              <div class="stat-line"><span>2.5 Üst genel oranı</span><b>%{detail["over25_rate"]:.0f}</b></div>
            </div>
            <div class="team-form-card">
              <div class="team-form-name">{escape(away)}</div>
              <div class="stat-line"><span>Form skoru</span><b>%{detail["away_rate"]:.0f}</b></div>
              <div class="stat-line"><span>KG genel oranı</span><b>%{detail["btts_rate"]:.0f}</b></div>
              <div class="stat-line"><span>Veri güveni</span><b>%{detail["details"].get("Veri güveni",0)}</b></div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("Tüm market olasılıklarını göster"):
            c1,c2,c3 = st.columns(3)
            vals = [
                ("1.5 Üst", market_scores.get("1.5 Üst")),
                ("2.5 Üst", market_scores.get("2.5 Üst")),
                ("3.5 Üst", market_scores.get("3.5 Üst")),
                ("3.5 Alt", market_scores.get("3.5 Alt")),
                ("KG Var", market_scores.get("KG Var")),
                ("KG Yok", market_scores.get("KG Yok")),
            ]
            for i,(name,val) in enumerate(vals):
                [c1,c2,c3][i%3].metric(name, "—" if val is None else f"%{val:.0f}")
    else:
        st.warning("Bu maç için yeterli geçmiş veri yok.")

st.caption("Tahmin yüzdeleri geçmiş maç istatistiklerinden üretilen model skorlarıdır; kesin sonuç veya bahis garantisi değildir.")

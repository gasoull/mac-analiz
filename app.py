from __future__ import annotations

from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from collections import defaultdict
from html import escape
import time
import requests
import streamlit as st

# =========================
# AYARLAR
# =========================
st.set_page_config(
    page_title="ONUR By Tahmin | İddaa Analiz Programı",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_URL = "https://vd.mackolik.com/livedata"
MARKETS = ["1.5 Üst", "2.5 Üst", "3.5 Alt", "KG Var", "KG Yok"]

# =========================
# TASARIM
# =========================
st.markdown("""
<style>
:root{
  --red:#e31d2b;--red-dark:#bf1420;--ink:#1f2937;--muted:#6b7280;
  --line:#e5e7eb;--soft:#f6f7f9;--green:#16a34a;
}
.block-container{max-width:1180px;padding-top:.8rem;padding-bottom:3rem}
[data-testid="stSidebar"]{background:#fff;border-right:1px solid var(--line)}
[data-testid="stSidebar"] .block-container{padding-top:1rem}
.topbar{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:16px 18px;background:linear-gradient(180deg,#ffffff 0%,#fbfbfc 100%);border:1px solid #e7e9ee;border-radius:16px;margin-bottom:16px;box-shadow:0 8px 24px rgba(17,24,39,.045)}
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
.stButton button{border-radius:10px!important;font-weight:850!important}
.stButton button[kind="primary"]{background:var(--red)!important;border-color:var(--red)!important}

.header-meta{display:flex;align-items:center;gap:10px}
.source-text{font-size:.68rem;color:#8a91a0;font-weight:700}

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

def initials(name):
    parts=[p for p in (name or "").replace("-"," ").split() if p]
    return "".join(x[0] for x in parts[:2]).upper() or "FC"

# =========================
# UI
# =========================
today = datetime.now(ZoneInfo("Europe/Istanbul")).date()

with st.sidebar:
    st.markdown("## ONUR By Tahmin")
    st.caption("İddaa Analiz Programı")
    st.divider()
    st.markdown('<span class="live-pill">● MAÇKOLİK VERİ MODU</span>', unsafe_allow_html=True)
    st.caption("Tek dosya sürümü")
    st.markdown("### Analiz Ayarları")
    history_days=st.select_slider("Geçmiş taraması",[14,21,30],value=21,format_func=lambda x:f"{x} gün")
    sample_size=st.select_slider("Takım başına son maç",[5,6,8,10],value=8)
    min_sample=st.select_slider("Minimum takım örneği",[3,4,5],value=3)

st.markdown("""
<div class="topbar">
  <div class="brand-wrap">
    <div class="brand-mark">ON</div>
    <div>
      <div class="brand-title">ONUR By Tahmin</div>
      <div class="brand-sub">Futbol maç ve gol marketi analiz ekranı</div>
    </div>
  </div>
  <div class="header-meta">
    <div class="source-text">Veri Kaynağı</div>
    <div class="live-pill">● MAÇKOLİK</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="title">Maç Tarayıcı</div>', unsafe_allow_html=True)

a,b,c,d=st.columns([1.35,1.35,.9,1.1])
with a:
    date_mode=st.selectbox("Tarih",["Bugün","Yarın","Önümüzdeki 3 Gün","Önümüzdeki 7 Gün","Özel Tarih"])
with b:
    analysis_mode=st.selectbox("Analiz",["En Güçlü Market"]+MARKETS)
with c:
    top_n=st.selectbox("Göster",[5,10,15],index=1)
with d:
    min_prob=st.slider("Min. olasılık",50,90,60)

if date_mode=="Bugün":
    start=end=today
elif date_mode=="Yarın":
    start=end=today+timedelta(days=1)
elif date_mode=="Önümüzdeki 3 Gün":
    start,end=today,today+timedelta(days=2)
elif date_mode=="Önümüzdeki 7 Gün":
    start,end=today,today+timedelta(days=6)
else:
    x=st.date_input("Özel tarih",value=today)
    start=end=x

selected=[]
errors=[]
cur=start
while cur<=end:
    try:
        selected.extend(load_day(cur.isoformat()))
    except Exception as exc:
        errors.append(str(exc))
    cur += timedelta(days=1)

leagues=sorted({m["league"] for m in selected if m.get("league")},key=str.casefold)
league_filter=st.selectbox("Lig",["Tüm Ligler"]+leagues)

if league_filter=="Tüm Ligler":
    filtered=selected
else:
    filtered=[m for m in selected if m["league"]==league_filter]

fixtures=[m for m in filtered if m["status"]!="FINISHED"]

run=st.button("⚡ Maçları Analiz Et",type="primary")

m1,m2,m3,m4=st.columns(4)
m1.metric("Maçkolik maçları",len(selected))
m2.metric("Lig sayısı",len(leagues))
m3.metric("Analiz adayı",len(fixtures))
m4.metric("Türkiye saati",datetime.now(ZoneInfo("Europe/Istanbul")).strftime("%H:%M"))

if errors and not selected:
    st.error(errors[0])

if run:
    hist_end=start-timedelta(days=1)
    hist_start=hist_end-timedelta(days=history_days-1)

    with st.spinner(f"Geçmiş {history_days} gün taranıyor..."):
        history,h_errors=load_history(hist_start.isoformat(),hist_end.isoformat())

    idx=build_team_history(history)
    finished_history = sum(1 for m in history if m.get("status") == "FINISHED")
    st.caption(f"Geçmiş veri: {len(history)} futbol maçı • {finished_history} tamamlanmış maç • {len(idx)} takım")
    rows=[]
    for fixture in fixtures:
        r=strongest(fixture,idx,sample_size) if analysis_mode=="En Güçlü Market" else analyze(fixture,idx,analysis_mode,sample_size)
        if not r: continue
        if r["sample_count"]<min_sample*2: continue
        if r["probability"]<min_prob: continue
        rows.append(r)
    rows.sort(key=lambda x:x["probability"],reverse=True)
    st.session_state["v52"]={"rows":rows[:top_n],"all":rows,"history":history,"h_errors":h_errors}

data=st.session_state.get("v52")
if data:
    st.markdown('<div class="title">⭐ En Güçlü Marketler</div>', unsafe_allow_html=True)
    if data["h_errors"]:
        st.warning(f"Geçmiş taramasında {len(data['h_errors'])} gün alınamadı.")
    if not data["rows"]:
        st.warning("Maçlar geldi fakat filtreyi geçen tahmin yok. Minimum olasılığı 55 yapıp tekrar dene.")
    for i,r in enumerate(data["rows"],1):
        pct=max(0,min(100,r["probability"]))
        status="CANLI" if r["status"]=="LIVE" else r["time"]
        st.markdown(f"""
        <div class="match-card">
          <div class="mc-head"><div>#{i} • <b>{escape(r["league"])}</b> • {escape(r["date"])} • {escape(str(status))}</div><div class="rank">#{i}</div></div>
          <div class="mc-body">
            <div class="teams">
              <div class="team"><div class="badge">{escape(initials(r["home"]))}</div><div class="tn">{escape(r["home"])}</div></div>
              <div class="vs">VS</div>
              <div class="team r"><div class="tn">{escape(r["away"])}</div><div class="badge">{escape(initials(r["away"]))}</div></div>
            </div>
            <div class="pick">
              <div><div style="font-size:.68rem;color:#738092;font-weight:850">TAHMİN</div><div class="prob">%{r["probability"]:.0f}</div><div class="market">{escape(r["market"])}</div></div>
              <div class="conf">{escape(r["confidence"])}</div>
              <div class="bar"><span style="width:{pct:.0f}%"></span></div>
            </div>
          </div>
          <div class="stats">
            <div class="stat"><div class="sk">Takım-maç örneği</div><div class="sv">{r["sample_count"]}</div></div>
            <div class="stat"><div class="sk">Ort. toplam gol</div><div class="sv">{r["avg_goals"]:.2f}</div></div>
            <div class="stat"><div class="sk">KG oranı</div><div class="sv">%{r["btts_rate"]:.0f}</div></div>
            <div class="stat"><div class="sk">2.5 Üst oranı</div><div class="sv">%{r["over25_rate"]:.0f}</div></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander(f"Analiz detayı • {r['home']} - {r['away']}"):
            st.json(r["details"])

with st.expander(f"🌍 Seçili tarihte gelen tüm ligler ({len(leagues)})"):
    cols=st.columns(3)
    for i,name in enumerate(leagues):
        cols[i%3].write("• "+name)

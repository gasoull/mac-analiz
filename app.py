from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from html import escape

import streamlit as st

from mackolik import MackolikClient, MackolikError
from analyzer import MARKETS, build_team_history, analyze, strongest

st.set_page_config(
    page_title="ONUR By Tahmin | İddaa Analiz Programı",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
:root{
  --red:#e31d2b;
  --red-dark:#bf1420;
  --ink:#1f2937;
  --muted:#6b7280;
  --line:#e5e7eb;
  --soft:#f6f7f9;
  --green:#16a34a;
}
.block-container{
  max-width:1180px;
  padding-top:.8rem;
  padding-bottom:3rem;
}
[data-testid="stSidebar"]{
  background:#ffffff;
  border-right:1px solid var(--line);
}
[data-testid="stSidebar"] .block-container{
  padding-top:1rem;
}
.topbar{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:16px;
  padding:12px 16px;
  background:white;
  border:1px solid var(--line);
  border-radius:14px;
  margin-bottom:14px;
}
.brand-wrap{
  display:flex;
  align-items:center;
  gap:12px;
}
.brand-mark{
  width:42px;
  height:42px;
  border-radius:12px;
  display:grid;
  place-items:center;
  background:var(--red);
  color:#fff;
  font-weight:900;
  font-size:20px;
}
.brand-title{
  font-size:1.28rem;
  font-weight:900;
  color:var(--ink);
  line-height:1.05;
}
.brand-sub{
  font-size:.76rem;
  color:var(--muted);
  margin-top:3px;
}
.live-pill{
  display:inline-block;
  padding:6px 10px;
  border-radius:999px;
  background:#fff1f2;
  color:var(--red-dark);
  border:1px solid #fecdd3;
  font-size:.72rem;
  font-weight:850;
}
.title{
  font-size:1.1rem;
  font-weight:900;
  color:var(--ink);
  margin:15px 0 4px;
}
.subtitle{
  color:var(--muted);
  font-size:.78rem;
  margin-bottom:8px;
}
.match-card{
  background:#fff;
  border:1px solid var(--line);
  border-radius:14px;
  margin:9px 0;
  overflow:hidden;
  box-shadow:0 2px 8px rgba(17,24,39,.035);
}
.mc-head{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:10px;
  padding:9px 13px;
  background:#fafafa;
  border-bottom:1px solid var(--line);
  color:#6b7280;
  font-size:.73rem;
}
.rank{
  background:#fee2e2;
  color:var(--red-dark);
  padding:4px 8px;
  border-radius:8px;
  font-weight:900;
}
.mc-body{
  display:grid;
  grid-template-columns:1.15fr .85fr;
  gap:14px;
  align-items:center;
  padding:13px 14px 11px;
}
.teams{
  display:grid;
  grid-template-columns:1fr 28px 1fr;
  gap:8px;
  align-items:center;
}
.team{
  display:flex;
  align-items:center;
  gap:8px;
  min-width:0;
}
.team.r{
  justify-content:flex-end;
  text-align:right;
}
.badge{
  width:38px;
  height:38px;
  border-radius:10px;
  background:#f3f4f6;
  border:1px solid var(--line);
  display:grid;
  place-items:center;
  font-size:.7rem;
  font-weight:900;
  color:#4b5563;
  flex:none;
}
.tn{
  font-size:.92rem;
  font-weight:850;
  color:var(--ink);
  line-height:1.1;
}
.vs{
  text-align:center;
  font-weight:900;
  color:#9ca3af;
}
.pick{
  display:grid;
  grid-template-columns:auto 1fr;
  gap:6px 12px;
  align-items:center;
  padding:10px 12px;
  border:1px solid #dcfce7;
  background:#f0fdf4;
  border-radius:12px;
}
.prob{
  font-size:1.7rem;
  font-weight:950;
  letter-spacing:-.03em;
  color:#111827;
}
.market{
  font-weight:900;
  color:#111827;
}
.conf{
  justify-self:end;
  background:#dcfce7;
  color:#166534;
  padding:5px 8px;
  border-radius:8px;
  font-size:.72rem;
  font-weight:900;
}
.bar{
  grid-column:1/-1;
  height:6px;
  background:#d1fae5;
  border-radius:999px;
  overflow:hidden;
}
.bar span{
  display:block;
  height:100%;
  background:var(--green);
}
.stats{
  display:grid;
  grid-template-columns:repeat(4,1fr);
  gap:1px;
  background:var(--line);
  border-top:1px solid var(--line);
}
.stat{
  background:#fafafa;
  padding:9px 8px;
  text-align:center;
}
.sk{
  font-size:.65rem;
  color:#6b7280;
}
.sv{
  font-weight:900;
  color:#1f2937;
  margin-top:2px;
}
div[data-testid="stMetric"]{
  border:1px solid var(--line);
  border-radius:12px;
  padding:8px 10px;
  background:#fff;
  box-shadow:none;
}
.stButton button{
  border-radius:10px!important;
  font-weight:850!important;
}
.stButton button[kind="primary"]{
  background:var(--red)!important;
  border-color:var(--red)!important;
}
</style>
""", unsafe_allow_html=True)


def initials(name):
    parts = [p for p in (name or "").replace("-"," ").split() if p]
    return "".join(x[0] for x in parts[:2]).upper() or "FC"


@st.cache_data(ttl=120, show_spinner=False)
def load_day(day_iso):
    d = datetime.strptime(day_iso, "%Y-%m-%d").date()
    return MackolikClient().day(d)


@st.cache_data(ttl=3600, show_spinner=False)
def load_history(start_iso, end_iso):
    s = datetime.strptime(start_iso, "%Y-%m-%d").date()
    e = datetime.strptime(end_iso, "%Y-%m-%d").date()
    return MackolikClient().range(s, e, delay=.05)


today = datetime.now(ZoneInfo("Europe/Istanbul")).date()

with st.sidebar:
    st.markdown("## ONUR By Tahmin")
    st.caption("İddaa Analiz Programı")
    st.divider()
    st.markdown('<span class="live-pill">● MAÇKOLİK VERİ MODU</span>', unsafe_allow_html=True)
    st.caption("API anahtarı gerektirmez")
    st.markdown("### Analiz Ayarları")
    history_days = st.select_slider("Geçmiş taraması", [14,21,30,45], value=21, format_func=lambda x:f"{x} gün")
    sample_size = st.select_slider("Takım başına son maç", [5,6,8,10,12], value=8)
    min_sample = st.select_slider("Minimum takım örneği", [3,4,5,6], value=3)
    st.divider()
    st.caption("Kaynak: Maçkolik livedata")
    st.caption("Model yüzdeleri istatistiksel skordur; garanti değildir.")



st.markdown("""
<div class="topbar">
  <div class="brand-wrap">
    <div class="brand-mark">OB</div>
    <div>
      <div class="brand-title">ONUR By Tahmin</div>
      <div class="brand-sub">İddaa Analiz Programı</div>
    </div>
  </div>
  <div class="live-pill">● MAÇKOLİK VERİ MODU</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="title">Maç Tarayıcı</div>', unsafe_allow_html=True)

a,b,c,d = st.columns([1.35,1.35,.9,1.1])
with a:
    date_mode = st.selectbox("Tarih", ["Bugün","Yarın","Önümüzdeki 3 Gün","Önümüzdeki 7 Gün","Özel Tarih"])
with b:
    analysis_mode = st.selectbox("Analiz", ["En Güçlü Market"] + MARKETS)
with c:
    top_n = st.selectbox("Göster", [5,10,15], index=1)
with d:
    min_prob = st.slider("Min. olasılık", 50,90,60)

if date_mode == "Bugün":
    start = end = today
elif date_mode == "Yarın":
    start = end = today + timedelta(days=1)
elif date_mode == "Önümüzdeki 3 Gün":
    start, end = today, today + timedelta(days=2)
elif date_mode == "Önümüzdeki 7 Gün":
    start, end = today, today + timedelta(days=6)
else:
    x = st.date_input("Özel tarih", value=today)
    start = end = x

# Load selected days first, so leagues are populated from real Mackolik data.
selected_matches = []
load_errors = []
cur = start
while cur <= end:
    try:
        selected_matches.extend(load_day(cur.isoformat()))
    except MackolikError as exc:
        load_errors.append(str(exc))
    cur += timedelta(days=1)

leagues = sorted({m["league"] for m in selected_matches if m.get("league")}, key=str.casefold)
league_filter = st.selectbox("Lig", ["Tüm Ligler"] + leagues)

if league_filter != "Tüm Ligler":
    filtered_fixtures = [m for m in selected_matches if m["league"] == league_filter]
else:
    filtered_fixtures = selected_matches

# Show football fixtures only; finished matches are not prediction targets.
prediction_fixtures = [m for m in filtered_fixtures if m["status"] != "FINISHED"]

run = st.button("⚡ Maçları Analiz Et", type="primary")

if load_errors and not selected_matches:
    st.error(load_errors[0])

if run:
    hist_end = start - timedelta(days=1)
    hist_start = hist_end - timedelta(days=history_days-1)

    with st.spinner(f"Maçkolik geçmiş verisi taranıyor ({history_days} gün)..."):
        history, history_errors = load_history(hist_start.isoformat(), hist_end.isoformat())

    idx = build_team_history(history)

    rows = []
    for fixture in prediction_fixtures:
        r = strongest(fixture, idx, sample_size) if analysis_mode == "En Güçlü Market" else analyze(fixture, idx, analysis_mode, sample_size)
        if not r:
            continue
        if r["sample_count"] < min_sample*2:
            continue
        if r["probability"] < min_prob:
            continue
        rows.append(r)

    rows.sort(key=lambda x:x["probability"], reverse=True)
    st.session_state["macko_v5"] = {
        "rows": rows[:top_n],
        "all_rows": rows,
        "fixtures": prediction_fixtures,
        "selected": selected_matches,
        "history": history,
        "history_errors": history_errors,
        "leagues": leagues,
        "range": f"{start.strftime('%d.%m.%Y')} - {end.strftime('%d.%m.%Y')}",
    }

data = st.session_state.get("macko_v5")

# Always show source availability.
m1,m2,m3,m4 = st.columns(4)
m1.metric("Maçkolik maçları", len(selected_matches))
m2.metric("Lig sayısı", len(leagues))
m3.metric("Analiz adayı", len(prediction_fixtures))
m4.metric("Türkiye saati", datetime.now(ZoneInfo("Europe/Istanbul")).strftime("%H:%M"))

if leagues:
    st.caption("Ligler Maçkolik'in seçili tarihte döndürdüğü gerçek lig adlarından oluşturulur.")

if data:
    st.markdown('<div class="title">⭐ En Güçlü Marketler</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="subtitle">{escape(data["range"])} • Olasılık yüksekten düşüğe • Takım ve lig adları Maçkolik verisinden</div>',
        unsafe_allow_html=True
    )

    if data["history_errors"]:
        st.warning(f"Geçmiş taramasında {len(data['history_errors'])} gün alınamadı; mevcut verilerle analiz yapıldı.")

    if not data["rows"]:
        st.warning(
            "Maçlar geldi ancak seçilen filtreyi geçen analiz oluşmadı. "
            "Minimum olasılığı 55'e ve minimum takım örneğini 3'e indirerek tekrar dene."
        )
    else:
        for i,r in enumerate(data["rows"],1):
            pct = max(0,min(100,r["probability"]))
            status = "CANLI" if r["status"]=="LIVE" else r["time"]
            st.markdown(f"""
            <div class="match-card">
              <div class="mc-head">
                <div>#{i} • <b>{escape(r["league"])}</b> • {escape(r["date"])} • {escape(str(status))}</div>
                <div class="rank">#{i}</div>
              </div>
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
                x1,x2,x3 = st.columns(3)
                x1.metric("Ev sahibi form", f"%{r['home_rate']:.0f}")
                x2.metric("Deplasman form", f"%{r['away_rate']:.0f}")
                x3.metric("Model skoru", f"%{r['probability']:.0f}")
                st.json(r["details"])

    with st.expander(f"🌍 Seçili tarihteki tüm ligler ({len(data['leagues'])})"):
        cols = st.columns(3)
        for i,name in enumerate(data["leagues"]):
            cols[i%3].write("• " + name)

    with st.expander(f"📋 Maçkolik'ten gelen tüm maçlar ({len(data['selected'])})"):
        for m in data["selected"]:
            score = ""
            if m["status"] == "FINISHED":
                score = f" — {m['home_score']}:{m['away_score']}"
            elif m["status"] == "LIVE":
                score = f" — {m['live_home_score']}:{m['live_away_score']} ({m['minute']})"
            st.write(f"**{m['league']}** • {m['time']} • {m['home']} - {m['away']}{score}")
else:
    st.info("Lig listesinin Maçkolik'ten dolduğunu kontrol et; sonra **Maçları Analiz Et** butonuna bas.")

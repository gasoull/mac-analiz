from __future__ import annotations

from datetime import date, timedelta
from html import escape

import streamlit as st

from football_data import FootballDataClient, FootballDataError
from analyzer import MARKETS, build_history_index, analyze_fixture, strongest_market


st.set_page_config(
    page_title="ONUR Tahmin Programı",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
:root{
  --ink:#162033;
  --muted:#758195;
  --line:#e6eaf0;
  --soft:#f7f9fc;
  --green:#13b76a;
  --green2:#e9fbf2;
  --gold:#d8a83b;
}
.block-container{max-width:1250px;padding-top:1.25rem;padding-bottom:3rem}
[data-testid="stSidebar"]{background:#fbfcfe;border-right:1px solid #edf0f4}
[data-testid="stSidebar"] .block-container{padding-top:1.2rem}
.hero{
  background:linear-gradient(135deg,#111827 0%,#1c2940 62%,#0d1524 100%);
  color:white;border-radius:22px;padding:20px 24px;margin-bottom:18px;
  box-shadow:0 12px 34px rgba(20,31,50,.16);
}
.logo-row{display:flex;align-items:center;gap:14px}
.logo-ball{
  width:52px;height:52px;border-radius:18px;display:grid;place-items:center;
  background:linear-gradient(145deg,#f7d477,#b98018);font-size:28px;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.45),0 8px 24px rgba(216,168,59,.25)
}
.hero h1{font-size:2rem;line-height:1;margin:0;font-weight:900;letter-spacing:-.035em}
.hero p{margin:.45rem 0 0;color:#bfc8d6;font-size:.93rem}
.section-title{font-size:1.22rem;font-weight:850;color:var(--ink);margin:18px 0 8px}
.live-pill{
  display:inline-block;padding:6px 10px;border-radius:999px;background:#eafaf2;
  color:#07884a;font-size:.78rem;font-weight:800;border:1px solid #ccefdc
}
.league-strip{
  display:flex;gap:8px;flex-wrap:wrap;margin:4px 0 14px
}
.league-chip{
  border:1px solid var(--line);background:white;padding:7px 10px;border-radius:10px;
  color:#475569;font-size:.78rem;font-weight:700
}
.match-card{
  background:#fff;border:1px solid #e3e8ef;border-radius:20px;margin:12px 0;
  box-shadow:0 6px 22px rgba(32,45,66,.055);overflow:hidden
}
.mc-top{
  display:flex;align-items:center;justify-content:space-between;padding:11px 16px;
  border-bottom:1px solid #eef1f5;background:#fbfcfe;color:#7c8799;font-size:.78rem
}
.mc-rank{
  background:#e9fbf2;color:#09884a;border-radius:10px;padding:5px 9px;font-weight:900
}
.mc-main{
  display:grid;grid-template-columns:1fr 1.05fr;gap:16px;padding:17px 18px 14px;
  align-items:center
}
.teams{
  display:grid;grid-template-columns:1fr 34px 1fr;align-items:center;gap:10px
}
.team{display:flex;align-items:center;gap:10px;min-width:0}
.team.right{justify-content:flex-end;text-align:right}
.crest{
  width:46px;height:46px;object-fit:contain;border:1px solid #edf0f4;
  border-radius:13px;padding:6px;background:white;flex:none
}
.crest-placeholder{
  width:46px;height:46px;border-radius:13px;background:#f2f5f9;
  display:grid;place-items:center;font-weight:900;color:#8b97a8;flex:none
}
.team-name{font-weight:850;color:#172033;font-size:.98rem;line-height:1.15}
.team-country{font-size:.72rem;color:#8993a3;margin-top:3px}
.vs{text-align:center;font-weight:900;color:#a1a9b6}
.pickbox{
  border:1px solid #d9f2e6;background:linear-gradient(135deg,#f3fff9,#eafbf3);
  border-radius:16px;padding:14px 16px;display:grid;grid-template-columns:auto 1fr;
  gap:8px 15px;align-items:center
}
.prob{font-size:2rem;font-weight:950;letter-spacing:-.04em;color:#152033}
.market{font-size:1rem;font-weight:900;color:#142034}
.conf{justify-self:end;background:#d9f8e8;color:#078648;padding:6px 9px;border-radius:10px;font-weight:850;font-size:.78rem}
.bar{height:8px;border-radius:999px;background:#dce5ea;overflow:hidden;grid-column:1/-1}
.bar>span{display:block;height:100%;border-radius:999px;background:linear-gradient(90deg,#13b76a,#55dfa0)}
.stats{
  display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:#e9edf2;
  border-top:1px solid #eef1f5
}
.stat{background:#f8fafc;padding:11px 14px;text-align:center}
.stat .k{font-size:.7rem;color:#7f8999}
.stat .v{font-weight:900;color:#1a2334;margin-top:2px}
.card-note{padding:10px 16px;color:#7c8796;font-size:.75rem;border-top:1px solid #eef1f5}
div[data-testid="stMetric"]{
  border:1px solid #e7ebf0;border-radius:16px;padding:11px 13px;background:#fff;
  box-shadow:0 4px 14px rgba(28,42,60,.035)
}
.stButton button{border-radius:12px!important;font-weight:800!important}
</style>
""", unsafe_allow_html=True)


def crest_html(url, alt):
    if url:
        return f'<img class="crest" src="{escape(url, quote=True)}" alt="{escape(alt)}">'
    initials = "".join(x[:1] for x in alt.split()[:2]).upper()
    return f'<div class="crest-placeholder">{escape(initials)}</div>'


@st.cache_data(ttl=1800, show_spinner=False)
def cached_competitions(token):
    return FootballDataClient(token).competitions()


@st.cache_data(ttl=300, show_spinner=False)
def cached_day_matches(token, day_iso):
    return FootballDataClient(token).matches_by_date(day_iso)


@st.cache_data(ttl=900, show_spinner=False)
def cached_history(token, start_iso, end_iso, comp_ids):
    ids = list(comp_ids) if comp_ids else None
    return FootballDataClient(token).matches_between(
        start_iso, end_iso, ids, status="FINISHED"
    )


token = ""
try:
    token = st.secrets.get("FOOTBALL_DATA_API_TOKEN", "")
except Exception:
    pass

with st.sidebar:
    st.markdown("## ⚽ ONUR Tahmin")
    st.caption("Canlı futbol analiz paneli")
    st.divider()

    if token:
        st.markdown('<span class="live-pill">● CANLI MOD</span>', unsafe_allow_html=True)
        st.caption("football-data.org bağlı")
    else:
        st.error("API anahtarı bulunamadı.")
        st.code('FOOTBALL_DATA_API_TOKEN = "..."', language="toml")
        st.stop()

    st.markdown("### Model Ayarları")
    history_days = st.select_slider(
        "Geçmiş veri",
        options=[45,60,90,120],
        value=90,
        format_func=lambda x: f"{x} gün"
    )
    sample_size = st.select_slider(
        "Takım başına son maç",
        options=[5,8,10,12,15],
        value=10
    )
    min_team_sample = st.select_slider(
        "Minimum takım örneği",
        options=[3,4,5,6,8],
        value=4
    )

    st.divider()
    st.caption("Veri: football-data.org API v4")
    st.caption("Yalnızca istatistiksel sıralamadır; garanti tahmin değildir.")



# Competition coverage
try:
    competitions = cached_competitions(token)
except FootballDataError as e:
    st.error(str(e))
    st.stop()

comp_by_code = {
    (c.get("code") or str(c.get("id"))): c
    for c in competitions
    if c.get("name")
}
competition_names = sorted(
    [c.get("name") for c in competitions if c.get("name")],
    key=str.casefold
)

st.markdown('<div class="section-title">Maç Tarayıcı</div>', unsafe_allow_html=True)

c1,c2,c3,c4 = st.columns([1.25,1.4,1.05,1.15])
with c1:
    date_mode = st.radio("Tarih", ["Bugün","Yarın","Özel"], horizontal=True)
    if date_mode == "Bugün":
        target = date.today()
    elif date_mode == "Yarın":
        target = date.today() + timedelta(days=1)
    else:
        target = st.date_input("Özel tarih", value=date.today())

with c2:
    analysis_type = st.selectbox("Analiz türü", ["En Güçlü Market"] + MARKETS)
with c3:
    top_n = st.selectbox("Gösterilecek", [5,10,15], index=1)
with c4:
    min_prob = st.slider("Min. olasılık", 50,90,65)

league_filter = st.selectbox(
    "Lig",
    ["Tüm Erişilebilir Ligler"] + competition_names,
    index=0
)

run = st.button("⚡ Canlı Analizi Başlat", type="primary")

if not run and "results_v4" not in st.session_state:
    st.info("Tarihi ve marketi seçip **Canlı Analizi Başlat** butonuna bas.")

if run:
    try:
        with st.spinner("Canlı fikstür ve geçmiş maçlar yükleniyor..."):
            day_matches = cached_day_matches(token, target.isoformat())

            if league_filter != "Tüm Erişilebilir Ligler":
                day_matches = [
                    m for m in day_matches
                    if (m.get("competition") or {}).get("name") == league_filter
                ]

            comp_ids = sorted({
                (m.get("competition") or {}).get("id")
                for m in day_matches
                if (m.get("competition") or {}).get("id") is not None
            })

            hist_start = target - timedelta(days=history_days)
            hist_end = target - timedelta(days=1)

            history = []
            if comp_ids:
                history = cached_history(
                    token,
                    hist_start.isoformat(),
                    hist_end.isoformat(),
                    tuple(comp_ids)
                )

            idx = build_history_index(history)
            rows = []

            for m in day_matches:
                if analysis_type == "En Güçlü Market":
                    r = strongest_market(m, idx, sample_size)
                else:
                    r = analyze_fixture(m, idx, analysis_type, sample_size)

                if not r:
                    continue
                if r["sample_count"] < min_team_sample * 2:
                    continue
                if r["probability"] < min_prob:
                    continue
                rows.append(r)

            rows.sort(key=lambda x: x["probability"], reverse=True)

            st.session_state["results_v4"] = {
                "target": target.isoformat(),
                "matches": day_matches,
                "history": history,
                "rows": rows[:top_n],
                "all_rows": rows,
                "league_filter": league_filter,
                "analysis_type": analysis_type,
            }

    except FootballDataError as e:
        st.error(str(e))
        st.stop()

data = st.session_state.get("results_v4")
if data:
    rows = data["rows"]
    day_matches = data["matches"]
    history = data["history"]

    a,b,c,d = st.columns(4)
    a.metric("Günün maçı", len(day_matches))
    b.metric("API lig kapsamı", len(competitions))
    c.metric("Geçmiş maç", len(history))
    d.metric("Uygun aday", len(data["all_rows"]))

    # Compact league chips
    visible_leagues = []
    for m in day_matches:
        name = (m.get("competition") or {}).get("name")
        if name and name not in visible_leagues:
            visible_leagues.append(name)
    if visible_leagues:
        chips = "".join(f'<span class="league-chip">{escape(x)}</span>' for x in visible_leagues[:12])
        st.markdown(f'<div class="league-strip">{chips}</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">⭐ En Güçlü Marketler</div>', unsafe_allow_html=True)
    st.caption("Olasılık yüksekten düşüğe sıralanır. Takım adları ve armalar doğrudan canlı API’den gelir.")

    if not rows:
        st.warning(
            "Bu filtrelerle yeterli veri/olasılık bulunamadı. "
            "Minimum olasılığı düşürmeyi veya takım örneğini azaltmayı dene."
        )
    else:
        for i,r in enumerate(rows,1):
            pct = max(0, min(100, r["probability"]))
            hc = crest_html(r["home_crest"], r["home"])
            ac = crest_html(r["away_crest"], r["away"])

            st.markdown(f"""
            <div class="match-card">
              <div class="mc-top">
                <div>#{i} • <b>{escape(r["league"])}</b> • {escape(r["kickoff"])}</div>
                <div class="mc-rank">#{i}</div>
              </div>

              <div class="mc-main">
                <div class="teams">
                  <div class="team">
                    {hc}
                    <div>
                      <div class="team-name">{escape(r["home_short"])}</div>
                      <div class="team-country">{escape(r["country"])}</div>
                    </div>
                  </div>
                  <div class="vs">VS</div>
                  <div class="team right">
                    <div>
                      <div class="team-name">{escape(r["away_short"])}</div>
                      <div class="team-country">{escape(r["country"])}</div>
                    </div>
                    {ac}
                  </div>
                </div>

                <div class="pickbox">
                  <div>
                    <div style="font-size:.7rem;color:#708092;font-weight:800">TAHMİN</div>
                    <div class="prob">%{r["probability"]:.0f}</div>
                    <div class="market">{escape(r["market"])}</div>
                  </div>
                  <div class="conf">{escape(r["confidence"])}</div>
                  <div class="bar"><span style="width:{pct:.0f}%"></span></div>
                </div>
              </div>

              <div class="stats">
                <div class="stat"><div class="k">Takım-maç örneği</div><div class="v">{r["sample_count"]}</div></div>
                <div class="stat"><div class="k">Ort. toplam gol</div><div class="v">{r["avg_goals"]:.2f}</div></div>
                <div class="stat"><div class="k">KG oranı</div><div class="v">%{r["btts_rate"]:.0f}</div></div>
                <div class="stat"><div class="k">2.5 Üst oranı</div><div class="v">%{r["over25_rate"]:.0f}</div></div>
              </div>

              <div class="card-note">Veri: son maç formu + ev/deplasman eğilimi + örneklem güveni</div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander(f"Analiz detayı • {r['home_short']} - {r['away_short']}"):
                x1,x2,x3 = st.columns(3)
                x1.metric("Ev sahibi market formu", f"%{r['home_form']:.0f}")
                x2.metric("Deplasman market formu", f"%{r['away_form']:.0f}")
                x3.metric("Model sonucu", f"%{r['probability']:.0f}")
                st.json(r["components"])

    st.divider()
    with st.expander(f"🌍 API hesabında görünen tüm ligler ({len(competitions)})"):
        cols = st.columns(3)
        for n,name in enumerate(competition_names):
            cols[n % 3].write("• " + name)

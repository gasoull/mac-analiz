import streamlit as st
from datetime import date, timedelta
from zoneinfo import ZoneInfo

from sportmonks import SportmonksClient, SportmonksError
from analyzer import (
    build_history_index,
    analyze_fixture,
    demo_fixtures,
    demo_history,
)

st.set_page_config(page_title="Maç Analiz", page_icon="⚽", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.3rem; max-width: 1180px;}
div[data-testid="stMetric"] {
    background: rgba(127,127,127,.08);
    border: 1px solid rgba(127,127,127,.18);
    border-radius: 14px;
    padding: 10px 14px;
}
.match-card {
    border: 1px solid rgba(127,127,127,.20);
    border-radius: 14px;
    padding: 14px 16px;
    margin: 9px 0;
    background: rgba(127,127,127,.06);
}
.small {opacity:.72; font-size:.88rem;}
.score-high {font-weight:800; font-size:1.35rem;}
</style>
""", unsafe_allow_html=True)

st.title("⚽ Maç Analiz")
st.caption("Gol marketleri için veri tabanlı sıralama • Tarayıcıdan çalışır • Tahminler garanti değildir.")

with st.sidebar:
    st.header("Veri Kaynağı")

    cloud_token = ""
    try:
        cloud_token = st.secrets.get("SPORTMONKS_API_TOKEN", "")
    except Exception:
        cloud_token = ""

    manual_token = ""
    if not cloud_token:
        manual_token = st.text_input(
            "Sportmonks API Token",
            type="password",
            help="Web yayınına alınca token Streamlit Secrets içinde saklanabilir."
        )

    token = cloud_token or manual_token
    demo = st.toggle("Demo Modu", value=not bool(token))

    if token and not demo:
        st.success("Canlı veri açık")
    elif demo:
        st.info("Demo verisi kullanılıyor")
    else:
        st.warning("API token gerekli")

    history_days = st.slider("Geçmiş veri penceresi", 60, 240, 120, 30)
    sample_size = st.slider("Takım başına son maç", 5, 20, 10)
    st.divider()
    st.caption("Canlı kaynak: Sportmonks Football API v3")

tz = ZoneInfo("Europe/Istanbul")
today = date.today()

c1, c2, c3, c4 = st.columns([1.4, 1.8, 1.2, 1.2])
with c1:
    target_date = st.date_input("Tarih", value=today)
with c2:
    market = st.selectbox("Analiz türü", [
        "1.5 Üst", "2.5 Üst", "3.5 Alt", "KG Var", "KG Yok"
    ])
with c3:
    top_n = st.selectbox("Kaç maç?", [5, 10, 15], index=1)
with c4:
    min_prob = st.slider("Min. olasılık", 50, 90, 60, 1)

if "raw_fixtures" not in st.session_state:
    st.session_state.raw_fixtures = []
if "raw_history" not in st.session_state:
    st.session_state.raw_history = []
if "last_date" not in st.session_state:
    st.session_state.last_date = None

load_col, _ = st.columns([1, 4])
with load_col:
    load = st.button("Verileri Getir", type="primary", use_container_width=True)

if load:
    if demo:
        st.session_state.raw_fixtures = demo_fixtures(target_date)
        st.session_state.raw_history = demo_history(target_date)
        st.session_state.last_date = str(target_date)
    else:
        if not token:
            st.error("Canlı veri için Sportmonks API token gerekli.")
            st.stop()

        client = SportmonksClient(token)
        start = target_date - timedelta(days=history_days)
        end = target_date - timedelta(days=1)

        try:
            with st.spinner("Fikstür ve geçmiş maçlar alınıyor..."):
                st.session_state.raw_fixtures = client.fixtures_by_date(target_date)
                st.session_state.raw_history = client.fixtures_between(start, end)
                st.session_state.last_date = str(target_date)
        except SportmonksError as e:
            st.error(str(e))
            st.stop()

fixtures = st.session_state.raw_fixtures
history = st.session_state.raw_history

if fixtures:
    league_map = {"Tüm Ligler": None}
    for f in fixtures:
        lid = f.get("league_id")
        lname = (f.get("league") or {}).get("name") or f"Lig #{lid}"
        league_map[lname] = lid

    league_name = st.selectbox("Lig filtresi", list(league_map.keys()))
    selected_league = league_map[league_name]

    filtered = [f for f in fixtures if selected_league is None or f.get("league_id") == selected_league]
    idx = build_history_index(history)

    rows = []
    for f in filtered:
        result = analyze_fixture(f, idx, market, sample_size)
        if result and result["probability"] >= min_prob:
            rows.append(result)

    rows.sort(key=lambda x: x["probability"], reverse=True)
    rows = rows[:top_n]

    m1, m2, m3 = st.columns(3)
    m1.metric("O günkü maç", len(fixtures))
    m2.metric("Filtrelenen maç", len(filtered))
    m3.metric("Gösterilen aday", len(rows))

    st.subheader(f"{market} • En güçlü {top_n} aday")

    if not rows:
        st.info("Bu filtrelerde yeterli geçmiş veriye sahip aday çıkmadı. Minimum olasılığı düşürmeyi veya Tüm Ligler'i seçmeyi deneyebilirsin.")
    else:
        for i, r in enumerate(rows, 1):
            conf = "Yüksek" if r["sample_count"] >= 16 else ("Orta" if r["sample_count"] >= 10 else "Sınırlı")
            st.markdown(
                f"""
                <div class="match-card">
                  <div class="small">#{i} • {r['league']} • {r['kickoff']}</div>
                  <div style="font-size:1.10rem;font-weight:700;margin-top:4px">{r['home']} — {r['away']}</div>
                  <div class="score-high">%{r['probability']:.0f} <span class="small">{r['market']}</span></div>
                  <div class="small">Veri güveni: {conf} • Kullanılan takım-maç örneği: {r['sample_count']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            with st.expander("Neden bu yüzde?"):
                st.write(r["explanation"])
                st.json(r["components"])

    st.divider()
    st.caption(
        "Yüzde; iki takımın son maçlarındaki market gerçekleşme oranları, "
        "ev/deplasman performansı ve örneklem güveni birleştirilerek hesaplanır. "
        "Küçük örneklemler %50'ye doğru yumuşatılır."
    )

elif st.session_state.last_date:
    st.warning("Seçilen tarihte veri kaynağından maç gelmedi.")
else:
    st.info("Önce **Verileri Getir** butonuna bas. Token yoksa Demo Modu ile arayüzü hemen deneyebilirsin.")

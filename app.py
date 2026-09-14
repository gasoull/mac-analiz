import streamlit as st
from datetime import date, timedelta
from zoneinfo import ZoneInfo

from sportmonks import SportmonksClient, SportmonksError
from analyzer import build_history_index, analyze_fixture, demo_fixtures, demo_history

st.set_page_config(
    page_title="ONUR Tahmin",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
:root{
    --card-radius:18px;
}
.block-container{
    padding-top:1.15rem;
    padding-bottom:2rem;
    max-width:1280px;
}
[data-testid="stSidebar"]{
    border-right:1px solid rgba(120,120,120,.18);
}
.hero{
    padding:18px 22px;
    border-radius:22px;
    background:linear-gradient(135deg, rgba(22,22,26,.98), rgba(45,45,54,.96));
    color:white;
    margin-bottom:18px;
    box-shadow:0 10px 30px rgba(0,0,0,.16);
}
.hero-title{
    font-size:2.15rem;
    font-weight:850;
    letter-spacing:-0.04em;
    margin:0;
}
.hero-sub{
    margin-top:5px;
    opacity:.72;
    font-size:.95rem;
}
.panel{
    border:1px solid rgba(127,127,127,.18);
    border-radius:18px;
    padding:16px 17px;
    background:rgba(127,127,127,.045);
}
.match-card{
    border:1px solid rgba(127,127,127,.17);
    border-radius:18px;
    padding:16px 18px;
    margin:10px 0;
    background:rgba(127,127,127,.045);
    transition:.15s ease;
}
.match-card:hover{
    border-color:rgba(127,127,127,.35);
    transform:translateY(-1px);
}
.small{
    opacity:.68;
    font-size:.84rem;
}
.match-name{
    font-size:1.08rem;
    font-weight:750;
    margin-top:3px;
}
.prob{
    font-size:1.55rem;
    font-weight:850;
    letter-spacing:-.03em;
    margin-top:3px;
}
.badge{
    display:inline-block;
    padding:4px 9px;
    border-radius:999px;
    background:rgba(127,127,127,.12);
    font-size:.78rem;
    margin-left:6px;
}
.section-title{
    font-size:1.28rem;
    font-weight:800;
    margin:4px 0 8px;
}
div[data-testid="stMetric"]{
    border:1px solid rgba(127,127,127,.18);
    border-radius:16px;
    padding:10px 14px;
    background:rgba(127,127,127,.045);
}
.stButton button{
    border-radius:12px!important;
    font-weight:750!important;
}
</style>
""", unsafe_allow_html=True)

tz = ZoneInfo("Europe/Istanbul")
today = date.today()

# Secrets / token
cloud_token = ""
try:
    cloud_token = st.secrets.get("SPORTMONKS_API_TOKEN", "")
except Exception:
    cloud_token = ""

with st.sidebar:
    st.markdown("## ⚽ ONUR Tahmin")
    st.caption("Veri tabanlı maç tarama paneli")
    st.divider()

    if cloud_token:
        token = cloud_token
        st.success("Canlı veri bağlı")
        demo = st.toggle("Demo modu", value=False)
    else:
        token = st.text_input("Sportmonks API Token", type="password")
        demo = st.toggle("Demo modu", value=not bool(token))
        if token and not demo:
            st.success("Canlı veri açık")
        elif demo:
            st.info("Demo verisi kullanılıyor")

    st.markdown("### Veri Derinliği")
    history_mode = st.selectbox(
        "Geçmiş veri",
        ["Akıllı (120 gün)", "60 gün", "90 gün", "120 gün", "180 gün"],
        index=0
    )
    history_map = {
        "Akıllı (120 gün)": 120,
        "60 gün": 60,
        "90 gün": 90,
        "120 gün": 120,
        "180 gün": 180
    }
    history_days = history_map[history_mode]

    sample_size = st.select_slider(
        "Takım başına son maç",
        options=[5, 8, 10, 12, 15, 20],
        value=10
    )

    st.markdown("### Model Hassasiyeti")
    min_data = st.select_slider(
        "Minimum örnek",
        options=[3, 5, 6, 8, 10],
        value=5,
        help="Daha yüksek değer = daha az maç, daha güvenli veri."
    )

    st.divider()
    st.caption("Canlı kaynak: Sportmonks Football API v3")
    st.caption("Model: takım formu + iç/deplasman market oranları")

st.markdown("""
<div class="hero">
    <div class="hero-title">ONUR Tahmin</div>
    <div class="hero-sub">Gol marketleri için profesyonel maç tarama ve olasılık paneli</div>
</div>
""", unsafe_allow_html=True)

# Filters
st.markdown('<div class="section-title">Maç Tarayıcı</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns([1.15, 1.55, 1, 1])
with c1:
    target_date = st.date_input("Tarih", value=today)
with c2:
    market = st.selectbox("Analiz türü", ["1.5 Üst", "2.5 Üst", "3.5 Alt", "KG Var", "KG Yok"])
with c3:
    top_n = st.selectbox("Gösterilecek maç", [5, 10, 15], index=1)
with c4:
    min_prob = st.slider("Min. olasılık", 50, 90, 65, 1)

b1, b2 = st.columns([1,4])
with b1:
    load = st.button("⚡ Analizi Başlat", type="primary", use_container_width=True)

if "raw_fixtures" not in st.session_state:
    st.session_state.raw_fixtures = []
if "raw_history" not in st.session_state:
    st.session_state.raw_history = []
if "last_date" not in st.session_state:
    st.session_state.last_date = None

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
            with st.spinner(f"{history_days} günlük geçmiş veri ve fikstür taranıyor..."):
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

    lc1, lc2 = st.columns([1.7, 2.3])
    with lc1:
        league_name = st.selectbox("Lig filtresi", list(league_map.keys()))
    with lc2:
        st.caption(
            f"Veri kapsamı: **{history_days} gün** • takım başına **son {sample_size} maç** • "
            f"minimum örnek **{min_data}**"
        )

    selected_league = league_map[league_name]
    filtered = [f for f in fixtures if selected_league is None or f.get("league_id") == selected_league]
    idx = build_history_index(history)

    rows = []
    for f in filtered:
        result = analyze_fixture(f, idx, market, sample_size)
        if result and result["sample_count"] >= min_data * 2 and result["probability"] >= min_prob:
            rows.append(result)

    rows.sort(key=lambda x: x["probability"], reverse=True)
    rows = rows[:top_n]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Günün maçı", len(fixtures))
    m2.metric("Lig filtresi", len(filtered))
    m3.metric("Geçmiş maç", len(history))
    m4.metric("Uygun aday", len(rows))

    st.markdown(f'<div class="section-title">{market} • En Güçlü Adaylar</div>', unsafe_allow_html=True)

    if not rows:
        st.info("Bu filtrelerde yeterli veri kalmadı. Minimum olasılığı veya minimum örnek değerini düşürebilirsin.")
    else:
        for i, r in enumerate(rows, 1):
            if r["probability"] >= 80:
                risk = "Yüksek güven"
            elif r["probability"] >= 70:
                risk = "Orta-yüksek"
            else:
                risk = "Seçilebilir"

            st.markdown(
                f"""
                <div class="match-card">
                    <div class="small">#{i} • {r['league']} • {r['kickoff']}</div>
                    <div class="match-name">{r['home']} — {r['away']}</div>
                    <div class="prob">%{r['probability']:.0f}
                        <span class="badge">{r['market']}</span>
                        <span class="badge">{risk}</span>
                    </div>
                    <div class="small">Kullanılan takım-maç örneği: {r['sample_count']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            with st.expander("Detaylı model açıklaması"):
                st.write(r["explanation"])
                st.json(r["components"])

    st.divider()
    st.caption(
        "ONUR Tahmin yüzdeleri; iki takımın son maç market gerçekleşmeleri, "
        "ev/deplasman performansı ve örneklem güveni birleştirilerek hesaplanır. "
        "Bu ekran istatistiksel sıralama aracıdır; garanti sonuç anlamına gelmez."
    )

elif st.session_state.last_date:
    st.warning("Seçilen tarihte veri kaynağından maç gelmedi.")
else:
    st.info("Filtreleri seçip **Analizi Başlat** butonuna bas.")

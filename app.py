import streamlit as st
from datetime import date, timedelta

from sportmonks import SportmonksClient, SportmonksError
from analyzer import build_history_index, analyze_fixture, demo_fixtures, demo_history

st.set_page_config(
    page_title="ONUR Tahmin",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

MARKETS = ["1.5 Üst", "2.5 Üst", "3.5 Alt", "KG Var", "KG Yok"]

st.markdown("""
<style>
.block-container{padding-top:1rem;padding-bottom:2rem;max-width:1280px}
[data-testid="stSidebar"]{border-right:1px solid rgba(127,127,127,.16)}
.hero{
    padding:20px 24px;border-radius:22px;
    background:linear-gradient(135deg,#111217,#252731);
    color:#fff;margin-bottom:18px;box-shadow:0 10px 28px rgba(0,0,0,.14)
}
.hero h1{font-size:2.15rem;margin:0;font-weight:850;letter-spacing:-.04em}
.hero p{margin:.35rem 0 0;opacity:.7}
.section{font-size:1.18rem;font-weight:800;margin:.2rem 0 .65rem}
.match-card{
    border:1px solid rgba(127,127,127,.18);border-radius:18px;padding:15px 17px;
    margin:9px 0;background:rgba(127,127,127,.045)
}
.rank{font-size:.78rem;opacity:.62}
.match{font-size:1.08rem;font-weight:780;margin-top:3px}
.prob{font-size:1.55rem;font-weight:880;letter-spacing:-.03em;margin-top:3px}
.badge{
    display:inline-block;padding:4px 9px;margin-left:6px;border-radius:999px;
    background:rgba(127,127,127,.13);font-size:.76rem;font-weight:650
}
.meta{opacity:.64;font-size:.82rem;margin-top:4px}
div[data-testid="stMetric"]{
    border:1px solid rgba(127,127,127,.16);border-radius:16px;padding:10px 13px;
    background:rgba(127,127,127,.04)
}
.stButton button{border-radius:12px!important;font-weight:760!important}
.notice{
    padding:10px 12px;border-radius:12px;background:rgba(127,127,127,.07);
    border:1px solid rgba(127,127,127,.13);font-size:.86rem
}
</style>
""", unsafe_allow_html=True)

# API token
cloud_token = ""
try:
    cloud_token = st.secrets.get("SPORTMONKS_API_TOKEN", "")
except Exception:
    pass

with st.sidebar:
    st.markdown("## ⚽ ONUR Tahmin")
    st.caption("Maç tarama ve olasılık paneli")
    st.divider()

    if cloud_token:
        token = cloud_token
        demo = st.toggle("Demo modu", value=False)
        if not demo:
            st.success("Canlı veri bağlı")
    else:
        token = st.text_input("Sportmonks API Token", type="password")
        demo = st.toggle("Demo modu", value=not bool(token))
        if token and not demo:
            st.success("Canlı veri açık")
        elif demo:
            st.info("Demo verisi")

    st.markdown("### Veri Ayarları")
    history_label = st.selectbox(
        "Geçmiş veri",
        ["Akıllı (120 gün)", "60 gün", "90 gün", "120 gün", "180 gün"],
        index=0
    )
    history_days = {
        "Akıllı (120 gün)":120, "60 gün":60, "90 gün":90,
        "120 gün":120, "180 gün":180
    }[history_label]

    sample_size = st.select_slider(
        "Takım başına son maç",
        options=[5,8,10,12,15,20],
        value=10
    )

    min_data = st.select_slider(
        "Minimum takım örneği",
        options=[3,5,6,8,10],
        value=5
    )

    st.divider()
    st.caption("Kaynak: Sportmonks Football API v3")
    st.caption("Free plan: Danish Superliga + Scottish Premiership")

st.markdown("""
<div class="hero">
  <h1>ONUR Tahmin</h1>
  <p>Günün maçlarını gol marketlerine göre tarar, olasılık ve veri güvenine göre sıralar.</p>
</div>
""", unsafe_allow_html=True)

today = date.today()

st.markdown('<div class="section">Maç Tarayıcı</div>', unsafe_allow_html=True)

d1, d2, d3, d4 = st.columns([1.25,1.55,1,1])
with d1:
    day_mode = st.radio("Tarih", ["Bugün","Yarın","Özel"], horizontal=True)
    if day_mode == "Bugün":
        target_date = today
    elif day_mode == "Yarın":
        target_date = today + timedelta(days=1)
    else:
        target_date = st.date_input("Özel tarih", value=today)

with d2:
    market_choice = st.selectbox(
        "Analiz türü",
        ["En Güçlü Market"] + MARKETS
    )
with d3:
    top_n = st.selectbox("Kaç aday?", [5,10,15], index=1)
with d4:
    min_prob = st.slider("Min. olasılık", 50,90,65,1)

b1, b2 = st.columns([1.05,4])
with b1:
    load = st.button("⚡ Taramayı Başlat", type="primary", use_container_width=True)

for key, default in {
    "raw_fixtures":[],
    "raw_history":[],
    "last_date":None
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

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
            with st.spinner(f"{target_date} fikstürü ve {history_days} günlük geçmiş veri taranıyor..."):
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
        lname = (f.get("league") or {}).get("name") or f"Lig #{f.get('league_id')}"
        league_map[lname] = f.get("league_id")

    f1, f2 = st.columns([1.4,2.6])
    with f1:
        league_name = st.selectbox("Lig filtresi", list(league_map.keys()))
    with f2:
        st.markdown(
            f'<div class="notice">Kapsam: <b>{history_days} gün</b> • '
            f'takım başına <b>{sample_size}</b> maç • minimum takım örneği <b>{min_data}</b></div>',
            unsafe_allow_html=True
        )

    selected_league = league_map[league_name]
    filtered = [
        f for f in fixtures
        if selected_league is None or f.get("league_id") == selected_league
    ]

    idx = build_history_index(history)
    rows = []

    for f in filtered:
        if market_choice == "En Güçlü Market":
            candidates = []
            for m in MARKETS:
                r = analyze_fixture(f, idx, m, sample_size)
                if r and r["sample_count"] >= min_data * 2:
                    candidates.append(r)
            if candidates:
                best = max(candidates, key=lambda x: x["probability"])
                if best["probability"] >= min_prob:
                    rows.append(best)
        else:
            r = analyze_fixture(f, idx, market_choice, sample_size)
            if r and r["sample_count"] >= min_data * 2 and r["probability"] >= min_prob:
                rows.append(r)

    rows.sort(key=lambda x: x["probability"], reverse=True)
    rows = rows[:top_n]

    m1,m2,m3,m4 = st.columns(4)
    m1.metric("Günün maçı", len(fixtures))
    m2.metric("Filtrelenen", len(filtered))
    m3.metric("Geçmiş maç", len(history))
    m4.metric("Uygun aday", len(rows))

    title = "En Güçlü Marketler" if market_choice == "En Güçlü Market" else f"{market_choice} Adayları"
    st.markdown(f'<div class="section">{title}</div>', unsafe_allow_html=True)

    if not rows:
        st.info("Bu filtrelerde yeterli aday bulunamadı. Minimum olasılığı veya minimum örnek değerini düşürebilirsin.")
    else:
        for i,r in enumerate(rows,1):
            if r["probability"] >= 82:
                conf = "Çok güçlü"
            elif r["probability"] >= 75:
                conf = "Güçlü"
            elif r["probability"] >= 68:
                conf = "Orta"
            else:
                conf = "Sınırda"

            st.markdown(
                f"""
                <div class="match-card">
                    <div class="rank">#{i} • {r['league']} • {r['kickoff']}</div>
                    <div class="match">{r['home']} — {r['away']}</div>
                    <div class="prob">%{r['probability']:.0f}
                        <span class="badge">{r['market']}</span>
                        <span class="badge">{conf}</span>
                    </div>
                    <div class="meta">Takım-maç örneği: {r['sample_count']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            with st.expander("Analiz detayı"):
                st.write(r["explanation"])
                st.json(r["components"])

    st.divider()
    st.caption(
        "Model; son maç market gerçekleşmeleri, iç/deplasman davranışı ve örneklem güvenini "
        "birleştirir. Yüzdeler istatistiksel olasılık tahminidir, garanti sonuç değildir."
    )

elif st.session_state.last_date:
    st.warning("Seçilen tarihte erişilebilir liglerde maç bulunamadı.")
else:
    st.info("Bugün / Yarın seç, analiz türünü belirle ve **Taramayı Başlat**.")

st.markdown(
    '<div class="notice" style="margin-top:18px">'
    '<b>Veri kapsamı notu:</b> Sportmonks Free plan yalnızca Danish Superliga ve '
    'Scottish Premiership sunar. Premier League, Championship, Süper Lig vb. için '
    'ücretli lig erişimi gerekir.'
    '</div>',
    unsafe_allow_html=True
)

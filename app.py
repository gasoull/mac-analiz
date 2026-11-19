from __future__ import annotations
from collections import defaultdict
from datetime import datetime,timedelta
from html import escape
from zoneinfo import ZoneInfo
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from data_sources import get_matches

st.set_page_config(page_title='ONUR ANALİZ | Canlı Maç Merkezi',page_icon='⚽',layout='wide',initial_sidebar_state='collapsed')
TR=ZoneInfo('Europe/Istanbul')
now=datetime.now(TR)

CSS='''
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Outfit:wght@500;600;700;800&display=swap');
:root{color-scheme:dark}
html,body,[data-testid="stAppViewContainer"],.stApp{background:#080d17!important;color:#eaf0fb!important;font-family:'DM Sans',sans-serif!important}
[data-testid="stHeader"]{background:transparent!important}
[data-testid="stToolbar"],#MainMenu,footer{visibility:hidden}
.block-container{padding-top:1.35rem!important;padding-bottom:3.5rem!important;max-width:1200px!important}
[data-testid="stVerticalBlock"]{gap:.7rem}
h1,h2,h3{font-family:'Outfit',sans-serif;color:#f7f9ff!important}
p,span,label{font-family:'DM Sans',sans-serif}
.brand{display:flex;align-items:center;gap:13px;margin:4px 0 15px}
.brandmark{display:grid;place-items:center;background:linear-gradient(145deg,#4b7cff,#9a6aff);width:43px;height:43px;border-radius:13px;box-shadow:0 6px 28px #3a65f54b;font-size:22px}
.brandname{font:800 23px 'Outfit',sans-serif;letter-spacing:-.9px;color:#f4f7ff}
.brandname span{color:#719bff}
.sub{font-size:12px;color:#8796b5;margin-top:1px}
.hero{padding:24px 28px;border:1px solid #263550;border-radius:20px;background:radial-gradient(circle at 92% 15%,#283a70 0%,transparent 33%),linear-gradient(120deg,#14223a,#0c1424 80%);margin:9px 0 17px}
.eyebrow{font-size:11px;color:#86a6fa;font-weight:800;letter-spacing:2.5px}
.hero-title{font:800 clamp(25px,3.2vw,37px) 'Outfit',sans-serif;letter-spacing:-1px;margin:7px 0 5px}
.hero-desc{color:#9caccc;font-size:13px;line-height:1.6}
.stats{display:flex;gap:13px;margin:10px 0 17px;flex-wrap:wrap}
.metric{flex:1;min-width:125px;background:#111a2b;border:1px solid #25324b;border-radius:13px;padding:13px 17px}
.metric .k{font-size:11px;color:#8e9dba;font-weight:600}.metric .v{font:800 27px 'Outfit',sans-serif;letter-spacing:-.6px;margin-top:4px}.metric.live .v{color:#fa7386}.metric .d{font-size:10px;color:#6f83a5}
.sec-title{font:700 17px 'Outfit',sans-serif;color:#eaf0ff;margin:23px 0 11px}
.league{background:#142037;border:1px solid #263651;border-bottom:none;padding:13px 18px;border-radius:13px 13px 0 0;color:#d7e4ff;font-size:12px;font-weight:800;display:flex;justify-content:space-between}
.league .count{color:#889abc;font-weight:600}
.match{display:grid;grid-template-columns:78px minmax(0,1fr) 72px 105px;gap:8px;align-items:center;padding:14px 17px;background:#101827;border:1px solid #233049;border-top:none;min-height:64px}
.match:last-child{border-radius:0 0 13px 13px}
.match .time{font-size:12px;color:#9caccc;font-weight:700}
.match .teams{display:flex;flex-direction:column;gap:3px;min-width:0}
.match .team{font-size:13px;font-weight:700;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#e7edfa}
.match .score{text-align:center;font:800 19px 'Outfit',sans-serif;color:#fff;white-space:nowrap}
.match .badge{border-radius:7px;padding:6px 8px;text-align:center;font-size:10px;color:#aabbd6;background:#202d43;font-weight:800}
.match .badge.live{color:#ffa6b3;background:#542433}
.match .badge.finished{color:#94b0d7;background:#1a2b41}
.match .badge.upcoming{color:#9eb3d8;background:#243450}
.smallnote{color:#8395b6;font-size:12px;line-height:1.7;padding:9px 0}
.empty{border:1px dashed #30415e;border-radius:16px;padding:33px 23px;text-align:center;background:#101829;color:#aabada;font-size:13px;line-height:1.8}
[data-testid="stButton"] button{background:#192842!important;color:#dce7fc!important;border:1px solid #2a3d5c!important;border-radius:10px!important;font-weight:750!important;min-height:41px!important;box-shadow:none!important}
[data-testid="stButton"] button:hover{border-color:#6389f6!important;background:#21385c!important;color:white!important}
[data-testid="stButton"] button[kind="primary"]{background:linear-gradient(100deg,#3568ff,#6e70ff)!important;color:white!important;border:0!important}
[data-baseweb="select"]>div,[data-testid="stDateInput"] [data-baseweb="input"]>div,[data-testid="stTextInput"] [data-baseweb="input"]>div{background:#121c2f!important;color:#f5f7ff!important;border:1px solid #2b3a54!important;border-radius:10px!important}
[data-baseweb="input"] input{color:#edf3ff!important}
[data-testid="stDateInput"] label,[data-testid="stTextInput"] label,[data-testid="stSelectbox"] label{color:#8f9fbc!important;font-size:12px!important}
[data-testid="stAlert"]{background:#1c2740!important;border:1px solid #354467!important;color:#e5ebf8!important;border-radius:12px!important}
[data-testid="stExpander"]{border:1px solid #2d3c55!important;background:#101827!important;border-radius:10px!important}
hr{border-color:#1e2e47!important}
@media(max-width:680px){.block-container{padding:12px 12px 40px!important}.hero{padding:18px}.stats{gap:7px}.metric{min-width:90px;padding:11px}.match{grid-template-columns:51px minmax(0,1fr) 53px 67px;padding:11px 8px;gap:4px}.match .team{font-size:11px}.match .score{font-size:15px}.match .badge{font-size:9px;padding:5px 3px}.brandname{font-size:20px}}
</style>'''
st.markdown(CSS,unsafe_allow_html=True)
# Refresh the page once per minute to keep live scores current.
st_autorefresh(interval=75_000, key='onur_live_refresh')
st.markdown('<div class="brand"><div class="brandmark">⚽</div><div><div class="brandname">ONUR<span>ANALİZ</span></div><div class="sub">Futbol skorları • Fikstür • Maç merkezi</div></div></div>',unsafe_allow_html=True)
st.markdown('<div class="hero"><div class="eyebrow">MAÇ MERKEZİ / 2026</div><div class="hero-title">Maçın nabzı burada.</div><div class="hero-desc">Canlı skorlar, güncel karşılaşmalar ve ligler tek ekranda. Türkiye saatine göre görüntülenir.</div></div>',unsafe_allow_html=True)

if 'day' not in st.session_state:st.session_state.day=now.date()
c1,c2,c3,c4=st.columns([1,1,1,2])
with c1:
    if st.button('← Dün',use_container_width=True):st.session_state.day-=timedelta(days=1);st.rerun()
with c2:
    if st.button('Bugün',use_container_width=True,type='primary' if st.session_state.day==now.date() else 'secondary'):st.session_state.day=now.date();st.rerun()
with c3:
    if st.button('Yarın →',use_container_width=True):st.session_state.day+=timedelta(days=1);st.rerun()
with c4:
    chosen=st.date_input('Tarih seç',value=st.session_state.day,format='DD.MM.YYYY',label_visibility='collapsed')
    if chosen!=st.session_state.day:st.session_state.day=chosen;st.rerun()

@st.cache_data(ttl=65,show_spinner=False)
def load(day):return get_matches(day)
with st.spinner('Gerçek maç verileri getiriliyor…'):
    try:matches,providers,errors=load(st.session_state.day)
    except Exception as exc:matches,providers,errors=[],[],[f'Beklenmeyen hata: {type(exc).__name__}: {exc}']

count_live=sum(m['status']=='live' for m in matches)
count_done=sum(m['status']=='finished' for m in matches)
league_count=len(set(m['league'] for m in matches))
st.markdown(f'''<div class="stats"><div class="metric"><div class="k">TOPLAM MAÇ</div><div class="v">{len(matches)}</div><div class="d">Seçili gün</div></div><div class="metric live"><div class="k">● CANLI</div><div class="v">{count_live}</div><div class="d">Devam eden</div></div><div class="metric"><div class="k">BİTEN</div><div class="v">{count_done}</div><div class="d">Sonuçlanan</div></div><div class="metric"><div class="k">LİG SAYISI</div><div class="v">{league_count}</div><div class="d">Mevcut veri</div></div></div>''',unsafe_allow_html=True)

f1,f2,f3=st.columns([2.1,1.6,1])
with f1: search=st.text_input('Takım veya lig ara',placeholder='🔎  Takım veya lig ara...',label_visibility='collapsed')
with f2:
    opts=['Tüm ligler']+sorted({m['league'] for m in matches})
    league=st.selectbox('Ligler',opts,label_visibility='collapsed')
with f3:
    status=st.selectbox('Durum',['Tüm maçlar','🔴 Canlı','Biten','Yaklaşan'],label_visibility='collapsed')

filtered=[]
for m in matches:
    if search and search.casefold() not in ' '.join([m['home'],m['away'],m['league'],m['country']]).casefold():continue
    if league!='Tüm ligler' and m['league']!=league:continue
    if status=='🔴 Canlı' and m['status']!='live':continue
    if status=='Biten' and m['status']!='finished':continue
    if status=='Yaklaşan' and m['status']!='upcoming':continue
    filtered.append(m)

rh,rb=st.columns([3,1])
with rh:st.markdown(f'<div class="sec-title">{st.session_state.day.strftime("%d.%m.%Y")} • Karşılaşmalar <span style="font:500 12px DM Sans;color:#7f91ae">({len(filtered)})</span></div>',unsafe_allow_html=True)
with rb:
    if st.button('↻ Yenile',use_container_width=True):load.clear();st.rerun()

if filtered:
    grouped=defaultdict(list)
    for m in filtered:grouped[(m['country'],m['league'])].append(m)
    for (country,lg),rows in grouped.items():
        st.markdown(f'<div class="league"><span>🏆 {escape(lg)}{(" · "+escape(country)) if country else ""}</span><span class="count">{len(rows)} maç</span></div>',unsafe_allow_html=True)
        for m in rows:
            time=m['kickoff'].strftime('%H:%M') if m['kickoff'] else '—'
            score=f"{m['home_score']} : {m['away_score']}" if m['home_score'] is not None and m['away_score'] is not None else '– : –'
            state=m['status']
            badge='● CANLI' if state=='live' else 'MS' if state=='finished' else 'ERTELENDİ' if state=='cancelled' else 'PLANLI'
            info=(m['status_text'] or '').strip()
            label=escape(info[:17]) if state=='live' and info else badge
            st.markdown(f'<div class="match"><div class="time">{time}</div><div class="teams"><div class="team">{escape(m["home"])}</div><div class="team">{escape(m["away"])}</div></div><div class="score">{score}</div><div class="badge {state}">{escape(label)}</div></div>',unsafe_allow_html=True)
else:
    st.markdown('<div class="empty">⚽<br><b>Bu seçimde maç görünmüyor.</b><br>Başka tarih veya filtre deneyin. Veri hizmeti erişilemiyorsa aşağıdaki durum bilgisini kontrol edin.</div>',unsafe_allow_html=True)

source=', '.join(providers) or 'Veri alınamadı'
st.markdown(f'<div class="smallnote">Görüntülenen kaynak: {escape(source)} · Son sorgu: {datetime.now(TR).strftime("%H:%M:%S")} (TSİ) · Veriler yaklaşık 65 saniye önbellekte tutulur. Kaynakların kapsadığı lig ve güncellik değişebilir.</div>',unsafe_allow_html=True)
if errors:
    with st.expander(f'Bağlantı durumu • {len(errors)} uyarı'):
        for err in errors:st.code(err,language='text')
        st.caption('API erişimi kesildiğinde ya da kaynak boş yanıt verdiğinde uydurma skor gösterilmez. Yalnızca kaynaktan alınan maçlar listelenir.')
st.markdown('<div class="smallnote" style="margin-top:14px;border-top:1px solid #24334c;padding-top:16px">Veri hizmeti: <a href="https://sportscore.com/" rel="dofollow" target="_blank" style="color:#8fb1ff">Powered by SportScore</a> · Alternatif kaynak: <a href="https://www.thesportsdb.com/" target="_blank" style="color:#8fb1ff">TheSportsDB</a>. Bu uygulama bahis garantisi veya resmi skor sağlayıcısı değildir.</div>',unsafe_allow_html=True)

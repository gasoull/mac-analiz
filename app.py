import concurrent.futures
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import requests
import streamlit as st

st.set_page_config(page_title='ONUR ANALİZ | Canlı Maç Merkezi', page_icon='⚽', layout='wide', initial_sidebar_state='collapsed')
TZ = ZoneInfo('Europe/Istanbul')
LEAGUES = {
    '🇹🇷 Türkiye Süper Lig': 'tur.1',
    '🏆 UEFA Şampiyonlar Ligi': 'uefa.champions',
    '🏆 UEFA Avrupa Ligi': 'uefa.europa',
    '🏆 UEFA Konferans Ligi': 'uefa.europa.conf',
    '🏴 İngiltere Premier League': 'eng.1',
    '🇪🇸 İspanya LaLiga': 'esp.1',
    '🇩🇪 Almanya Bundesliga': 'ger.1',
    '🇮🇹 İtalya Serie A': 'ita.1',
    '🇫🇷 Fransa Ligue 1': 'fra.1',
    '🇳🇱 Hollanda Eredivisie': 'ned.1',
    '🇵🇹 Portekiz Primeira Liga': 'por.1',
    '🇧🇪 Belçika Pro League': 'bel.1',
    '🇺🇸 ABD MLS': 'usa.1',
    '🌍 Dünya Kupası': 'fifa.world',
}

st.markdown('''<style>
#MainMenu,footer,header {visibility:hidden} .block-container{max-width:1080px;padding-top:1.8rem;padding-bottom:3rem}
.stApp{background:#f4f6fa;color:#1c293d}.brand{font-size:27px;letter-spacing:-.8px;font-weight:900;margin:0}.brand span{color:#236de3}
.subtitle{color:#788498;font-size:13px;margin-top:2px;margin-bottom:17px}.league-head{background:#eaf0f7;color:#24354d;font-weight:800;font-size:13px;padding:11px 15px;border-radius:10px;margin:17px 0 7px}
.rowmatch{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:13px 15px;background:#fff;border:1px solid #e8edf4;border-radius:10px;margin:5px 0}
.teams{font-weight:750;font-size:14px;line-height:1.65;min-width:0}.score{font-size:18px;font-weight:900;color:#17283d;white-space:nowrap}.kick{font-size:12px;color:#758197;min-width:60px}.live{color:#d92447;font-weight:800}.pill{font-size:11px;background:#edf4ff;color:#276bd5;border-radius:6px;padding:6px 9px;font-weight:800}
.meta{color:#64758a;font-size:12px}.empty{padding:25px;border-radius:12px;background:#fff;color:#6a798a;border:1px solid #e7ecf3}
div[data-testid='stVerticalBlockBorderWrapper']{border-radius:13px!important;background:white}
@media(max-width:600px){.block-container{padding:1rem .7rem}.rowmatch{gap:6px;padding:11px 9px}.teams{font-size:12px}.score{font-size:15px}.kick{min-width:42px}}
</style>''', unsafe_allow_html=True)

def clean(s):
    import html
    return html.escape(str(s or ''), quote=True)

@st.cache_data(ttl=55, show_spinner=False)
def get_scores(day_iso):
    day = datetime.strptime(day_iso,'%Y-%m-%d').date()
    # Match windows near midnight in Türkiye; the API returns event UTC date.
    date_strings = sorted({(day + timedelta(days=o)).strftime('%Y%m%d') for o in (-1,0,1)})
    params = {'dates': '-'.join((date_strings[0], date_strings[-1])), 'limit': 250}
    def one(item):
        label, code = item
        url = f'https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard'
        try:
            r = requests.get(url, params=params, timeout=12, headers={'User-Agent':'Mozilla/5.0'})
            r.raise_for_status()
            return label, (r.json().get('events') or []), None
        except (requests.RequestException, ValueError) as e:
            return label, [], str(e)
    out, problems, seen = [], [], set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for label, events, error in pool.map(one, LEAGUES.items()):
            if error:
                problems.append(f'{label}: {error}')
                continue
            for event in events:
                eid = event.get('id')
                if eid in seen: continue
                try:
                    start = datetime.fromisoformat(event['date'].replace('Z','+00:00')).astimezone(TZ)
                except (KeyError, ValueError): continue
                if start.date() != day: continue
                comps = (event.get('competitions') or [{}])[0]
                contestants = comps.get('competitors') or []
                home = next((x for x in contestants if x.get('homeAway')=='home'), None)
                away = next((x for x in contestants if x.get('homeAway')=='away'), None)
                if not home or not away: continue
                status = event.get('status') or {}
                typ = status.get('type') or {}
                state = typ.get('state') or 'pre'
                display_clock = status.get('displayClock') or ''
                long_status = typ.get('shortDetail') or typ.get('description') or ''
                if state=='in': label_status = f"🔴 {display_clock or long_status or 'CANLI'}"
                elif state=='post': label_status='MS'
                else: label_status=start.strftime('%H:%M')
                out.append({
                    'id':str(eid), 'league':label, 'home':home.get('team',{}).get('displayName') or home.get('team',{}).get('name') or 'Ev sahibi',
                    'away':away.get('team',{}).get('displayName') or away.get('team',{}).get('name') or 'Deplasman',
                    'home_score':home.get('score') if state!='pre' else None,
                    'away_score':away.get('score') if state!='pre' else None,
                    'state':state,'status':label_status,'start':start.isoformat(),
                    'venue':(comps.get('venue') or {}).get('fullName') or '', 'detail':long_status,
                    'url':f'https://www.espn.com/soccer/match/_/gameId/{eid}'})
                seen.add(eid)
    order={'in':0,'pre':1,'post':2}
    out.sort(key=lambda m:(order.get(m['state'],3),m['league'],m['start']))
    return out, problems

st.markdown('<div class="brand">⚽ ONUR<span>ANALİZ</span></div><div class="subtitle">Canlı skorlar, fikstür ve maç detayları • Saat dilimi: Türkiye</div>',unsafe_allow_html=True)
now = datetime.now(TZ)
col1,col2,col3=st.columns([1.4,1.3,1])
with col1:
    selected_day = st.date_input('Tarih seç', value=now.date(), format='DD.MM.YYYY')
with col2:
    view = st.selectbox('Göster', ['Tüm maçlar','🔴 Canlı','Başlayacak','Biten'],index=0)
with col3:
    st.write('')
    if st.button('↻ Yenile', use_container_width=True):
        get_scores.clear()
        st.rerun()

search = st.text_input('Takım / lig ara',placeholder='Örn: Galatasaray, Premier League...',label_visibility='collapsed')

@st.fragment(run_every='60s')
def match_center():
    matches, errors = get_scores(selected_day.isoformat())
    all_count=len(matches)
    live_count=sum(m['state']=='in' for m in matches)
    ended_count=sum(m['state']=='post' for m in matches)
    a,b,c=st.columns(3)
    a.metric('Toplam maç',all_count)
    b.metric('🔴 Canlı',live_count)
    c.metric('Biten',ended_count)
    if errors:
        st.warning(f'{len(errors)} ligden veri alınamadı. Başarılı ligler gösteriliyor. API bağlantısı veya kapsam sorunlu olabilir.')
        with st.expander('Bağlantı hataları'):
            st.code('\n'.join(errors))
    if view=='🔴 Canlı': matches=[m for m in matches if m['state']=='in']
    elif view=='Başlayacak': matches=[m for m in matches if m['state']=='pre']
    elif view=='Biten': matches=[m for m in matches if m['state']=='post']
    if search.strip():
        q=search.casefold().strip()
        matches=[m for m in matches if q in (m['home']+' '+m['away']+' '+m['league']).casefold()]
    if not matches:
        st.markdown('<div class="empty">Bu tarih ve filtreler için maç bulunamadı. Başka tarih seçebilir veya filtreyi kaldırabilirsin.</div>',unsafe_allow_html=True)
        return
    byleague={}
    for m in matches: byleague.setdefault(m['league'],[]).append(m)
    for league, games in byleague.items():
        st.markdown(f'<div class="league-head">{clean(league)} · {len(games)} maç</div>',unsafe_allow_html=True)
        for m in games:
            score = f"{clean(m['home_score'])} – {clean(m['away_score'])}" if m['home_score'] is not None else '–'
            timing_class='live' if m['state']=='in' else 'kick'
            st.markdown(f'''<div class="rowmatch"><div class="{timing_class}">{clean(m['status'])}</div>
                <div class="teams" style="flex:1">{clean(m['home'])}<br>{clean(m['away'])}</div>
                <div class="score">{score}</div></div>''',unsafe_allow_html=True)
            with st.expander(f"📊 {m['home']} – {m['away']} · Maç detayı"):
                st.write(f"**Durum:** {m['detail'] or m['status']}")
                st.write(f"**Başlangıç:** {datetime.fromisoformat(m['start']).strftime('%d.%m.%Y %H:%M')} (TSİ)")
                if m['venue']: st.write(f"**Stadyum:** {m['venue']}")
                st.link_button('Maçın istatistiklerine git',m['url'])
                st.caption('Tahmin yüzdesi gösterilmiyor: canlı skor tek başına güvenilir tahmin üretmek için yeterli değildir.')

match_center()
st.caption('Veri kaynağı: ESPN herkese açık skor uç noktaları (resmî / garantili servis değildir). Veriler yaklaşık 60 saniyede bir yenilenir. Lig kapsamı ve gecikme kaynağa bağlıdır. Maçkolik ile birebir kapsam garanti edilmez.')

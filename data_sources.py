"""Public football data adapters. No fabricated matches or scores."""
from __future__ import annotations
from datetime import datetime, date, timezone
from zoneinfo import ZoneInfo
import requests

TR = ZoneInfo('Europe/Istanbul')
HEADERS = {'User-Agent':'ONUR-Analiz/2.0 (+https://onurtahmin.streamlit.app/)', 'Accept':'application/json'}
SPORTSCORE = 'https://sportscore.com/api/v1/fixtures/'
SPORTSCORE_LIVE = 'https://sportscore.com/api/widget/matches/'
SPORTSDB = 'https://www.thesportsdb.com/api/v1/json/123/eventsday.php'

class DataSourceError(Exception):
    pass

def _get(url, params):
    try:
        r=requests.get(url, params=params, headers=HEADERS, timeout=16)
        r.raise_for_status()
        data=r.json()
        if not isinstance(data,(dict,list)):
            raise ValueError('Beklenmeyen JSON yanıtı')
        return data
    except (requests.RequestException, ValueError) as e:
        raise DataSourceError(f'{url.split("/")[2]}: {type(e).__name__}: {str(e)[:180]}') from e

def _dt(raw):
    if not raw:
        return None
    s=str(raw).strip()
    try:
        d=datetime.fromisoformat(s.replace('Z','+00:00'))
        if d.tzinfo is None:
            d=d.replace(tzinfo=timezone.utc)
        return d.astimezone(TR)
    except ValueError:
        return None

def _status(s):
    text=str(s or '').lower().strip()
    if any(x in text for x in ('live','inprogress','in_progress','1st half','2nd half','half time','halftime','ht','playing','extra time','penalty')):
        return 'live'
    if any(x in text for x in ('finished','full time','fulltime','ended','complete','ft','after penalties')):
        return 'finished'
    if any(x in text for x in ('postponed','cancelled','abandoned','suspended')):
        return 'cancelled'
    return 'upcoming'

def _text(v, default=''):
    if isinstance(v,dict):
        return str(v.get('name') or v.get('short_name') or v.get('display_name') or v.get('title') or default)
    return str(v or default)

def _score(v):
    if v is None or v=='':
        return None
    try:
        return int(v)
    except (TypeError,ValueError):
        return None

def _unwrap(payload):
    if isinstance(payload,list): return payload
    for k in ('fixtures','matches','events','data','results'):
        value=payload.get(k)
        if isinstance(value,list): return value
        if isinstance(value,dict):
            for sub in ('matches','fixtures','events','results','data'):
                if isinstance(value.get(sub),list):return value[sub]
    return []

def _normal_sportscore(m):
    if not isinstance(m,dict): return None
    home=m.get('home') or m.get('home_team') or m.get('homeTeam') or m.get('team_home')
    away=m.get('away') or m.get('away_team') or m.get('awayTeam') or m.get('team_away')
    if not home or not away:return None
    comp=m.get('competition') or m.get('league') or m.get('tournament') or 'Diğer Ligler'
    country=m.get('country') or (comp.get('country') if isinstance(comp,dict) else '')
    raw_time=m.get('time') or m.get('start_time') or m.get('kickoff') or m.get('date') or m.get('startTime')
    score_obj=m.get('score') if isinstance(m.get('score'),dict) else {}
    hs=m.get('home_score',m.get('homeScore',score_obj.get('home')))
    aws=m.get('away_score',m.get('awayScore',score_obj.get('away')))
    stat=m.get('status') or m.get('status_text') or m.get('state')
    if isinstance(stat,dict):stat=stat.get('name') or stat.get('type') or stat.get('description')
    return dict(id=str(m.get('id') or m.get('slug') or f'{home}-{away}-{raw_time}'),home=_text(home),away=_text(away),league=_text(comp,'Diğer Ligler'),country=_text(country),kickoff=_dt(raw_time),home_score=_score(hs),away_score=_score(aws),status=_status(stat),status_text=_text(m.get('status_text') or stat),slug=_text(m.get('slug')),source='SportScore',home_logo=_text(m.get('home_logo')),away_logo=_text(m.get('away_logo')))

def fetch_sportscore_day(day:date):
    # The API's day boundary is UTC. Query adjacent dates to cover Istanbul's UTC+3 edge.
    days=[day]
    rows=[]; errors=[]
    for d in days:
        try:
            data=_get(SPORTSCORE,{'sport':'football','date':d.isoformat(),'limit':200})
            rows.extend(x for item in _unwrap(data) if (x:=_normal_sportscore(item)))
        except DataSourceError as e: errors.append(str(e))
    if not rows and errors: raise DataSourceError('; '.join(errors))
    return rows

def fetch_sportscore_live():
    data=_get(SPORTSCORE_LIVE,{'sport':'football','limit':50})
    return [x for item in _unwrap(data) if (x:=_normal_sportscore(item))]

def _normal_sportsdb(m):
    if not isinstance(m,dict):return None
    if m.get('strSport') and m['strSport'] != 'Soccer':return None
    home=m.get('strHomeTeam'); away=m.get('strAwayTeam')
    if not home or not away:return None
    utc=m.get('strTimestamp')
    if not utc and m.get('dateEvent'):
        utc=f"{m['dateEvent']}T{m.get('strTime') or '00:00:00'}+00:00"
    hs=_score(m.get('intHomeScore')); aws=_score(m.get('intAwayScore'))
    st=_status(m.get('strStatus'))
    if st=='upcoming' and hs is not None and aws is not None: st='finished'
    return dict(id=str(m.get('idEvent') or f'{home}-{away}-{utc}'),home=home,away=away,league=m.get('strLeague') or 'Diğer Ligler',country=m.get('strCountry') or '',kickoff=_dt(utc),home_score=hs,away_score=aws,status=st,status_text=str(m.get('strStatus') or ''),slug='',source='TheSportsDB',home_logo=m.get('strHomeTeamBadge') or '',away_logo=m.get('strAwayTeamBadge') or '')

def fetch_sportsdb_day(day:date):
    data=_get(SPORTSDB,{'d':day.isoformat(),'s':'Soccer'})
    return [x for item in _unwrap(data) if (x:=_normal_sportsdb(item))]

def get_matches(day:date):
    """Returns (items, providers, errors). Primary first; fallback only on error/zero data."""
    errors=[]; providers=[]
    try:
        items=fetch_sportscore_day(day)
        if items:providers.append('SportScore')
    except DataSourceError as e:
        items=[];errors.append(str(e))
    if not items:
        try:
            items=fetch_sportsdb_day(day)
            if items:providers.append('TheSportsDB')
        except DataSourceError as e:errors.append(str(e))
    if day==datetime.now(TR).date():
        try:
            live=fetch_sportscore_live()
            seen={(m['home'].casefold(),m['away'].casefold()) for m in items}
            for m in live:
                if m['kickoff'] and m['kickoff'].date()!=day:continue
                key=(m['home'].casefold(),m['away'].casefold())
                if key in seen:
                    for i,existing in enumerate(items):
                        if (existing['home'].casefold(),existing['away'].casefold())==key:
                            if m['status']=='live' or (m['status']=='finished' and existing['status']!='finished'):
                                items[i]=m
                            break
                else:
                    items.append(m);seen.add(key)
            if live and 'SportScore' not in providers:providers.append('SportScore')
        except DataSourceError as e:errors.append(str(e))
    # Never erase matches lacking a kickoff; the provider might not supply it.
    items=[m for m in items if m['kickoff'] is None or m['kickoff'].date()==day]
    items.sort(key=lambda m:(0 if m['status']=='live' else 1, m['kickoff'] or datetime.max.replace(tzinfo=TR),m['league'],m['home']))
    return items,providers,errors

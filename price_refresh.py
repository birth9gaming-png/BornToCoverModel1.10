"""Lightweight near-kickoff quotes; keep statistics on their normal schedule."""
from __future__ import annotations
import copy
from datetime import datetime,timezone,timedelta
from matchup_history import timestamp


def near_games(data,now):
    out=[]
    for g in data.get('games',[]):
        try:
            if not g.get('completed') and timedelta(0)<timestamp(g['kickoff'])-now<=timedelta(minutes=90):out.append(g)
        except (KeyError,ValueError,TypeError):continue
    return out


def due(data,now=None):
    now=now or datetime.now(timezone.utc)
    if data.get('mode')!='connected' or data.get('app_preferences',{}).get('bet_timing')!='near_kickoff' or not data.get('app_preferences',{}).get('auto_refresh',True) or not near_games(data,now):return False
    try:return now-timestamp(data.get('market_price_checked_at'))>=timedelta(minutes=15)
    except (ValueError,TypeError):return True


def team_aliases(data,games,league):
    """Resolve to the slate's IDs, even if a backup retains legacy duplicates."""
    from data_pipeline import normal_name
    teams=data.get('teams',{})
    active={g[side] for g in games for side in ('away','home')}
    choices={}
    for tid in active:
        for name in (teams.get(tid,{}).get('name',tid),tid.split(':')[-1]):
            choices.setdefault(normal_name(name),set()).add(tid)
    aliases={name:next(iter(ids)) for name,ids in choices.items() if len(ids)==1}
    supplied={**data.get('odds_aliases',{}),**data.get('odds_alias_overrides',{}).get(league,{})}
    for name,tid in supplied.items():
        if not isinstance(tid,str):continue
        canonical=tid if tid in active else league+':'+tid.split(':')[-1]
        if canonical in active:aliases[normal_name(name)]=canonical
    return aliases


def refresh(data,key,now=None,fetch=None):
    from data_pipeline import request_json,request_bytes,attach_odds
    from nfl_feeds import fetch_attd_quotes
    from nfl_layers import settings
    now=now or datetime.now(timezone.utc);out=copy.deepcopy(data)
    out['market_price_checked_at']=now.isoformat()
    out['market_price_notes']=[]
    fetch=fetch or request_json
    for league,sport in (('NFL','americanfootball_nfl'),('CFB','americanfootball_ncaaf')):
        selected=[copy.deepcopy(g) for g in near_games(data,now) if g['league']==league]
        if not selected:continue
        aliases=team_aliases(data,selected,league)
        try:
            params=dict(apiKey=key,regions=data.get('app_preferences',{}).get('regions','us'),markets='spreads,totals',oddsFormat='american',
                        commenceTimeFrom=now.strftime('%Y-%m-%dT%H:%M:%SZ'),commenceTimeTo=(now+timedelta(minutes=90)).strftime('%Y-%m-%dT%H:%M:%SZ'))
            events=fetch('https://api.the-odds-api.com/v4/sports/'+sport+'/odds',params,ttl=120)
            for g in selected:g['quotes']=[]
            attach_odds(selected,events,aliases)
            matched={str(g['id']):g for g in selected if g.get('quotes')}
            out['games']=[matched.get(str(g['id']),g) if g['league']==league else g for g in out['games']]
            if league=='NFL' and matched and fetch is request_json:
                quotes,notes=fetch_attd_quotes(list(matched.values()),data.get('nfl_player_candidates',[]),key,params['regions'],request_bytes,settings(data),now.isoformat())
                if quotes:
                    ids=set(matched);out['nfl_attd_quotes']=[q for q in out.get('nfl_attd_quotes',[]) if str(q.get('game_id')) not in ids]+quotes
                out['market_price_notes'].extend(notes)
        except (RuntimeError,ValueError,TypeError,KeyError,OSError):
            out['market_price_notes'].append(league+' near-kickoff quote refresh unavailable; previous dated quotes retained.')
    return out,True

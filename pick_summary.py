"""Small, deterministic selection/display helpers shared by the UI and ledger."""
from __future__ import annotations
import math
from datetime import datetime, timezone, timedelta
from statistics import median
from zoneinfo import ZoneInfo
from matchup_history import timestamp
from cfb_preferences import flags

CANDIDATE_EV=.05


def supported_candidate(q):
    return bool(q and min(q['conditional_ev'],q.get('without_live_prior_ev',q['conditional_ev']))>=CANDIDATE_EV)


def market_status(q,upcoming=True):
    if not q:return 'No current price'
    if q['conditional_ev']<=0:return 'Pass'
    if upcoming and supported_candidate(q):return 'Candidate'
    if q.get('scenario_dependent') or q.get('without_live_prior_ev',q['conditional_ev'])<=0 or q['conditional_ev']>=CANDIDATE_EV and not supported_candidate(q):return 'Review assumptions'
    return 'Lean'


def model_direction_options(options):
    """Direction follows point advantage; odds choose a price within that side."""
    edged=[q for q in options if isinstance(q.get('edge'),(int,float)) and math.isfinite(q['edge'])]
    if not edged:return options
    strongest=max(edged,key=lambda q:(q['edge'],q['conditional_ev']))
    directed=[q for q in edged if q['selection']==strongest['selection']]
    positive=[q for q in directed if q['edge']>0]
    if positive:return positive
    # Do not buy a worse line solely because it has a larger payout. When no
    # price offers point advantage, show the closest line as a comparison.
    return [q for q in directed if math.isclose(q['edge'],strongest['edge'])]


def current_quote(q, game, now):
    try:
        age=now-timestamp(q.get('updated_at'))
        return (not game.get('completed') and timestamp(game['kickoff'])>now
                and timedelta(0)<=age<=timedelta(hours=6)
                and bool(q.get('book')) and q['book']!='Manual scenario'
                and math.isfinite(float(q['conditional_ev'])))
    except (ValueError,TypeError,KeyError):return False


def selections(result, live=True, now=None, avoid_spots=False):
    """Show both best-priced markets even if negative; never call negative EV a bet.

    Direction follows the model's point advantage. Compare quoted EV within
    that direction, not preference bonuses. Stale and post-kickoff
    live quotes are withheld rather than promoted into current selections.
    """
    now=now or datetime.now(timezone.utc)
    qs=[q for q in result.get('markets',[]) if q.get('recommendation_eligible',True) and (not live or current_quote(q,result['game'],now))]
    try:upcoming=timestamp(result['game']['kickoff'])>now and not result['game'].get('completed')
    except (ValueError,TypeError,KeyError):upcoming=False
    chosen={};comparisons={}
    for kind in ('spread','total'):
        all_options=[q for q in qs if q['kind']==kind]
        comparisons[kind]=max(all_options,key=lambda q:q['conditional_ev'],default=None)
        options=model_direction_options(all_options)
        supported=[q for q in options if upcoming and supported_candidate(q)]
        # An unsupported higher estimate must not hide a qualified quote.
        chosen[kind]=max(supported or options,key=lambda q:q['conditional_ev'],default=None)
    best=max((q for q in chosen.values() if q is not None),key=lambda q:q['conditional_ev'],default=None)
    candidate=max((q for q in chosen.values() if upcoming and supported_candidate(q)),key=lambda q:q['conditional_ev'],default=None)
    lean=max((q for q in chosen.values() if market_status(q,upcoming)=='Lean'),key=lambda q:q['conditional_ev'],default=None)
    chosen['higher']=best['kind'] if best else None
    chosen['candidate_kind']=candidate['kind'] if candidate else None
    chosen['qualified']=bool(candidate)
    chosen['better']=candidate['kind'] if candidate else lean['kind'] if lean else best['kind'] if best and best['conditional_ev']>0 else None
    chosen['status']='Positive model EV' if chosen['better'] else 'Pass' if best else 'No current price'
    chosen['market_status']={kind:market_status(chosen[kind],upcoming) for kind in ('spread','total')}
    chosen['price_comparisons']=comparisons
    if not candidate and not lean and best and chosen['market_status'][best['kind']]=='Review assumptions':chosen['status']='Review assumptions'
    if avoid_spots and any(flags(result,side) for side in ('away','home')):
        chosen['better']=None;chosen['status']='Avoid — situational spot'
        chosen['qualified']=False
        chosen['candidate_kind']=None
        chosen['market_status']={kind:'Avoid — situational spot' for kind in ('spread','total')}
    return chosen


def value_rank(picks):
    """Supported Candidates, supported Leans, scenario reviews, then passes."""
    tier=3 if picks['qualified'] else 2 if picks['better'] and picks['status']!='Review assumptions' else 1 if picks['status']=='Review assumptions' else 0 if picks['higher'] else -1
    q=picks.get(picks['better'] or picks['higher'])
    return tier,q['conditional_ev'] if q else -99.


def reference_quotes(result, now):
    qs=[q for q in result.get('markets',[]) if current_quote(q,result['game'],now)]
    spreads=[-float(q['line']) if q['selection']=='away' else float(q['line'])
             for q in qs if q['kind']=='spread']
    totals=[float(q['line']) for q in qs if q['kind']=='total']
    return dict(margin=median(spreads) if spreads else None,total=median(totals) if totals else None)


def nfl_week_games(data, games=None, now=None):
    """Default NFL view: the current Tuesday–Monday slate, not rolling 7 days.

    Use official schedule week IDs when available, including postponed games.
    A frozen example remains inspectable. This is a display filter only; CFB
    loading, team histories, and automatic refresh keep their existing behavior.
    """
    games=list(data.get('games',[]) if games is None else games)
    if data.get('mode')!='connected' or data.get('app_preferences',{}).get('nfl_view','This week')=='All loaded':return games
    now=now or datetime.now(timezone.utc);today=now.astimezone(ZoneInfo('America/New_York')).date()
    first=today-timedelta(days=(today.weekday()-1)%7);last=first+timedelta(days=6)
    anchors=[]
    for g in data.get('schedule',[])+data.get('games',[]):
        if g.get('league')!='NFL':continue
        try:day=timestamp(g['kickoff']).astimezone(ZoneInfo('America/New_York')).date()
        except (ValueError,TypeError,KeyError):continue
        if first<=day<=last and g.get('week') is not None:
            anchors.append((g.get('season'),g['week']))
    official=set(anchors)
    visible=[]
    for g in games:
        if g.get('league')!='NFL':visible.append(g);continue
        try:day=timestamp(g['kickoff']).astimezone(ZoneInfo('America/New_York')).date()
        except (ValueError,TypeError,KeyError):continue
        if ((g.get('season'),g.get('week')) in official if official and g.get('week') is not None else first<=day<=last):visible.append(g)
    return visible


def summary_rows(data, results, now=None):
    rows=[];live=data.get('mode')=='connected'
    for r in results:
        g=r['game'];avoid=(r['league']=='CFB' and data['parameters']['CFB'].get('selection_style')=='avoid_spots')
        picks=selections(r,live,now,avoid)
        names=lambda side:data['teams'].get(g[side],{}).get('name',g[side])
        row={'Matchup':names('away')+' @ '+names('home')}
        for kind,label in [('spread','Spread'),('total','Total')]:
            q=picks[kind]
            if q:
                text=(names(q['selection'])+f" {q['line']:+g}" if kind=='spread' else q['label'])
                suffix=' · Pass at this price' if picks['market_status'][kind]=='Pass' else ''
                row[label+' pick']=text+f" · {100*q['conditional_ev']:+.1f}% EV"+suffix
            else:row[label+' pick']='No current price' if live else 'No price'
        better=picks['better']
        row['Better EV']='★ '+better.title()+(' · Candidate' if picks['qualified'] else ' · Review' if picks['status']=='Review assumptions' else ' · Lean') if better else picks['status']
        row['Candidate']=picks['candidate_kind'].title() if picks['qualified'] else 'No'
        row['Spread status']=picks['market_status']['spread'];row['Total status']=picks['market_status']['total']
        row['Model spread']=(g['away']+f" {r['fair_line_away']:+.1f}") if 'away' in r else None
        row['Model total']=round(r['fair_total'],1) if 'away' in r else None
        row['Kickoff']=g.get('kickoff');row['Status']=r.get('status')
        rows.append(row)
    return rows

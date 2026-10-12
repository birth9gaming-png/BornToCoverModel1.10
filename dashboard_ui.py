"""Dark, responsive game cards. HTML helpers are pure and escape all input."""
from __future__ import annotations
import html
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st
from book_policy import moment
from matchup_history import timestamp
from pick_summary import selections,summary_rows
from market_watch import alerts


def esc(value):return html.escape(str(value),quote=True)


def name(data,key):return data.get('teams',{}).get(key,{}).get('name',str(key).split(':')[-1])


def short(key):
    raw=str(key).split(':')[-1]
    if len(raw)<=4:return raw
    return ''.join(p[0] for p in raw.split()[:3]).upper() or raw[:3].upper()


def number(value,suffix='',signed=False):
    if value is None:return '—'
    return (f'{float(value):+.1f}' if signed else f'{float(value):.1f}')+suffix


def local_time(value):
    try:return timestamp(value).astimezone(ZoneInfo('America/New_York')).strftime('%a %b %-d · %-I:%M %p ET')
    except (ValueError,TypeError,KeyError):return 'Kickoff unavailable'


def theme():
    st.markdown('<style>'+Path(__file__).with_name('dashboard.css').read_text()+'</style>',unsafe_allow_html=True)


def quote_label(data,result,q):
    if not q:return 'Price unavailable'
    return name(data,result['game'][q['selection']])+f" {q['line']:+g}" if q['kind']=='spread' else q['label']


def pick_html(data,result,q,kind,higher,status):
    best=kind==higher and status not in ('Pass','No current price')
    label='Spread pick' if kind=='spread' else 'Total pick'
    tag='<span class="pick-star">'+('REVIEW' if status=='Review assumptions' else '★ SUPPORTED PICK' if status=='Candidate' else '★ BETTER EV')+'</span>' if best else '<span class="pick-state">'+esc('Pass at this price' if status=='Pass' else status)+'</span>'
    css='pick-tile review-tile' if best and status=='Review assumptions' else 'pick-tile best-tile' if best else 'pick-tile'
    comparison=''
    if q:
        quote_title=quote_label(data,result,q)
        title=quote_title
        if status=='Pass':comparison='<div class="pick-comparison">Model direction · no positive EV at this price</div>'
        price=f"{q['odds']:+g} · {q['book']}"
        ev=f"{100*q['conditional_ev']:+.1f}%"
        probability=f"{100*q['p_win']:.1f}% win · {100*q['p_push']:.1f}% push"
    else:
        title='Refresh this price';price='DraftKings / FanDuel';ev='—';probability='Projection remains available below'
    return '<div class="'+css+'"><div class="pick-label">'+label+tag+'</div><div class="pick-choice">'+esc(title)+'</div>'+comparison+'<div class="pick-price">'+esc(price)+'</div><div class="pick-footer"><span class="ev-value">'+ev+'</span><span>estimated EV</span></div><div class="pick-prob">'+esc(probability)+'</div></div>'


def game_html(data,result,now=None):
    g=result['game'];picks=selections(result,data.get('mode')=='connected',now or moment(data))
    context=result.get('market_context',{});cases=context.get('cases',[])
    flags,_=alerts(data,result,now or moment(data));tags=[]
    if cases:tags.append('<span class="tag tag-blue">MARKET ANGLE</span>')
    for flag in flags[:3]:tags.append('<span class="tag">'+esc(flag)+'</span>')
    team_lines=[]
    for side in ('away','home'):
        profile=context.get('sides',{}).get(side,{})
        detail=(('#'+str(profile['rank'])+' · ') if profile.get('rank') else '')+(profile.get('record') or 'Record unavailable')
        team_lines.append('<div class="team-line"><span class="team-mark">'+esc(short(g[side]))+'</span><div><div class="team-name">'+esc(name(data,g[side]))+'</div><div class="team-record">'+esc(detail)+(' · home' if side=='home' else ' · away')+'</div></div></div>')
    if 'away' in result:
        fav='away' if result['margin_away']>=0 else 'home'
        fair=name(data,g[fav])+f" {-abs(result['margin_away']):+.1f}"
        total=number(result['fair_total'])
    else:fair='Unavailable';total='—'
    state='Candidate' if picks['qualified'] else 'Review assumptions' if picks['status']=='Review assumptions' else 'Lean' if picks['better'] else 'Pass' if picks['higher'] else 'Refresh price'
    badge='status-good' if picks['qualified'] else 'status-muted'
    angle=''
    if cases:
        first=max(cases,key=lambda c:(c['model_agrees'],c.get('quote',{}).get('conditional_ev',-99) if c.get('quote') else -99))
        angle='<div class="angle-inline"><span>↗ '+esc(first['title'])+'</span><strong>'+esc(name(data,g[first['side']]))+'</strong><small>'+esc(first['status'])+'</small></div>'
    return '<article class="game-card"><div class="game-top"><span>'+esc(local_time(g.get('kickoff')))+'</span><span class="status '+badge+'">'+esc(state)+'</span></div><div class="matchup-teams">'+''.join(team_lines)+'</div><div class="pick-pair">'+pick_html(data,result,picks['spread'],'spread',picks['better'],picks['market_status']['spread'])+pick_html(data,result,picks['total'],'total',picks['better'],picks['market_status']['total'])+'</div><div class="fair-row"><span>Model spread <strong>'+esc(fair)+'</strong></span><span>Model total <strong>'+esc(total)+'</strong></span></div>'+angle+'<div class="tags">'+''.join(tags)+'</div></article>'


def angles_html(data,results):
    found=[]
    for r in results:
        # One featured angle per side/game; duplicate record/streak signals can
        # describe the same case without filling the board with duplicates.
        seen=set()
        for c in r.get('market_context',{}).get('cases',[]):
            if c['side'] in seen:continue
            seen.add(c['side']);found.append((r,c))
    found.sort(key=lambda p:(p[1]['model_agrees'],p[1]['quote']['conditional_ev'] if p[1].get('quote') else -99),reverse=True)
    items=[]
    for r,c in found[:6]:
        q=c.get('quote');line=quote_label(data,r,q) if q else name(data,r['game'][c['side']])
        price=f"{q['odds']:+g} · {q['book']} · {100*q['conditional_ev']:+.1f}% estimated EV" if q else 'Refresh an eligible price'
        items.append('<article class="angle-card"><div class="angle-title">'+esc(c['title'])+'</div><h3>'+esc(line)+'</h3><p>'+esc(c['reason'])+'</p><div class="angle-price">'+esc(price)+'</div><div class="angle-status">'+esc(c['status'])+'</div></article>')
    return '<div class="angle-grid">'+''.join(items)+'</div>' if items else ''


def picks_panel(data,results,league):
    now=moment(data)
    st.markdown('### Your game board')
    st.caption('Picks follow the model’s point advantage. Pass at this price means that direction has no positive EV at the quoted odds. Supported Candidates take priority over larger scenario estimates; both EV checks must reach +5%.')
    if not results:st.info('No upcoming games match this view. Live schedules populate automatically when the existing keys are connected.');return
    decisions=[selections(r,data.get('mode')=='connected',now) for r in results]
    counts={state:sum(p['qualified'] if state=='Candidate' else not p['qualified'] and ('Lean' if p['better'] and p['status']!='Review assumptions' else p['status'])==state for p in decisions) for state in ('Candidate','Lean','Pass','Review assumptions','No current price')}
    st.caption(' · '.join(str(n)+' '+('Candidates' if state=='Candidate' else 'Leans' if state=='Lean' else state) for state,n in counts.items() if n))
    cards=''.join(game_html(data,r,now) for r in results)
    st.markdown('<div class="game-grid">'+cards+'</div>',unsafe_allow_html=True)
    angles=angles_html(data,results)
    if angles:
        st.markdown('### Market angles to investigate')
        st.caption('Candidate wagers on the unexpected side: rank/record contradictions, vulnerable opponents, and verified observed movement. The displayed EV stays tied to its actual price.')
        st.markdown(angles,unsafe_allow_html=True)
    rows=summary_rows(data,results,now)
    for row,r in zip(rows,results):
        p=selections(r,data.get('mode')=='connected',now)
        for kind in ('spread','total'):
            q=p[kind];row[kind.title()+' book']=q['book'] if q else None;row[kind.title()+' odds']=q['odds'] if q else None
        row['Market angles']='; '.join(c['title']+' → '+name(data,r['game'][c['side']]) for c in r.get('market_context',{}).get('cases',[]))
    with st.expander('Full projection table and CSV'):
        df=pd.DataFrame(rows);st.dataframe(df,hide_index=True,width='stretch')
        st.download_button('Download this board',df.to_csv(index=False),file_name=league.lower()+'_projections.csv',mime='text/csv',key='projections_download_'+league)
    from projection_audit import audit_rows,model_status
    with st.expander('Check projections, Candidate decisions and historical models'):
        st.dataframe(pd.DataFrame([row for row in model_status(data,results) if row['League']==league]),hide_index=True,width='stretch')
        audit=pd.DataFrame(audit_rows(data,results,now))
        st.dataframe(audit,hide_index=True,width='stretch')
        st.caption('Model lean and price value are separate. Historical models remain fitted through 2025. New weekly coefficients require settled pregame records; preloaded history does not prove a betting edge.')
        st.download_button('Download projection audit',audit.to_csv(index=False),file_name=league.lower()+'_projection_audit.csv',mime='text/csv',key='audit_'+league)
    with st.expander('Matchup reasons, availability and market history'):
        index=st.selectbox('Inspect game',range(len(results)),format_func=lambda i:name(data,results[i]['game']['away'])+' @ '+name(data,results[i]['game']['home']),key='details_'+league)
        r=results[index]
        for c in r.get('market_context',{}).get('cases',[]):st.write('**'+c['title']+' — '+name(data,r['game'][c['side']])+'**');st.caption(c['reason']+' '+c['status'])
        st.caption(r.get('gradient_boosting',{}).get('status',''))
        if 'away' in r:st.dataframe(pd.DataFrame({side:r[side]['score_parts'] for side in ('away','home')}),width='stretch')
        info=r.get('market_context',{}).get('movement',{})
        st.write({'Observed movement toward away':info.get('spread_move'),'Late movement toward away':info.get('late_spread_move'),'Favorite flip':info.get('favorite_flip'),'Reported public lean':info.get('public_lean'),'Public source':info.get('public_source'),'Reverse movement':info.get('reverse_line_movement')})
        st.caption(info.get('status','Public / sharp coverage unknown.'))
        if 'away' in r:
            st.markdown('**Check an alternate spread and price**')
            st.caption('Enter the actual offered odds when buying points. This comparison does not change the model, place a wager or enter the forecast ledger.')
            chosen=selections(r,data.get('mode')=='connected',now)['spread']
            side=st.selectbox('Team for this price check',['away','home'],index=0 if not chosen or chosen['selection']=='away' else 1,format_func=lambda side:name(data,r['game'][side]),key='buy_side_'+league)
            available=[q for q in r['markets'] if q['kind']=='spread' and q['selection']==side and q.get('recommendation_eligible',True)]
            default=chosen if chosen and chosen['selection']==side else max(available,key=lambda q:(q['edge'],q['conditional_ev']),default=None)
            columns=st.columns(2)
            line=columns[0].number_input('Offered spread',value=float(default['line']) if default else round(2*(r['fair_line_away'] if side=='away' else -r['fair_line_away']))/2,step=.5,key='buy_line_'+league+'_'+str(r['game']['id'])+'_'+side)
            odds=columns[1].number_input('Offered American odds',value=float(default['odds']) if default else -110.,step=1.,key='buy_odds_'+league+'_'+str(r['game']['id'])+'_'+side)
            if st.button('Check this line and price',key='buy_check_'+league):
                try:
                    from projection_audit import check_price
                    checked=check_price(data,r,side,line,odds)
                    st.write({'Win chance':f"{100*checked['p_win']:.1f}%",'Push chance':f"{100*checked['p_push']:.1f}%",'Estimated EV':f"{100*checked['conditional_ev']:+.1f}%",'Decision':'Positive estimated EV' if checked['conditional_ev']>0 else 'Pass at this price'})
                except (ValueError,TypeError,KeyError) as exc:st.error(str(exc))


def attd_cards(ranked):
    items=[]
    for _,r in ranked.head(24).iterrows():
        quote=pd.notna(r.get('odds'))
        price=f"{r['odds']:+g} · {r['book']}" if quote else 'No current DraftKings / FanDuel price'
        ev=number(100*r['conditional_ev'],'%',True) if quote else '—'
        items.append('<article class="prop-card"><div class="prop-role">'+esc(r['team'])+' · '+esc(r['position'])+'</div><h3>'+esc(r['player'])+'</h3><div class="prop-main"><strong>'+number(100*r['attd_probability'],'%')+'</strong><span>scoring scenario</span></div><div class="prop-price">'+esc(price)+'</div><div class="prop-ev">'+ev+' estimated EV if active</div><div class="prop-history">Last active week '+esc(r['prior_active_week'])+' · '+esc(r['prior_active_tds'])+' TDs</div><div class="prop-rule">'+esc(r['recency_rule'])+' · '+number(r['opportunities_per_game'])+' opportunities/game</div></article>')
    st.markdown('<div class="prop-grid">'+''.join(items)+'</div>',unsafe_allow_html=True)

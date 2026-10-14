#!/usr/bin/env python3
"""Dependency-free GitHub contribution city. --demo is explicitly synthetic."""
import argparse, datetime as dt, html, json, math, os, random, sys
from pathlib import Path
from urllib.request import Request, urlopen

def fetch_days(username):
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        raise ValueError('GITHUB_TOKEN is required. Run this through the included GitHub workflow.')
    query = '''query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}'''
    req = Request('https://api.github.com/graphql', data=json.dumps({'query':query,'variables':{'login':username}}).encode(), headers={'Authorization':'Bearer '+token,'Content-Type':'application/json','User-Agent':'contribution-city'})
    with urlopen(req, timeout=60) as response:
        body = json.load(response)
    if body.get('errors'):
        raise ValueError('GitHub GraphQL returned errors: '+json.dumps(body['errors']))
    user = body.get('data',{}).get('user')
    if not user:
        raise ValueError('GitHub user not found')
    days = [d for w in user['contributionsCollection']['contributionCalendar']['weeks'] for d in w['contributionDays']]
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    days = sorted((d for d in days if d['date'] <= today), key=lambda d:d['date'])[-365:]
    if not days:
        raise ValueError('GitHub returned an empty calendar; keeping previous SVG unchanged.')
    return days

def metrics(days):
    total = active = streak = best = 0
    previous = None
    for d in days:
        date = dt.date.fromisoformat(d['date'])
        n = d['contributionCount']
        total += n
        active += n > 0
        if previous is not None and (date-previous).days != 1:
            streak = 0
        streak = streak+1 if n else 0
        best = max(best,streak)
        previous = date
    return total,active,best

def render(days, username, demo=False):
    total,active,best = metrics(days)
    maximum = max((d['contributionCount'] for d in days), default=0)
    out = []
    def add(s): out.append(s)
    def point(x,y,z=0): return (450+(x-y)*17,278+(x+y)*8.5-z)
    def poly(points,fill,stroke='none',extra=''):
        add('<polygon points="'+ ' '.join(f'{x:.2f},{y:.2f}' for x,y in points)+f'" fill="{fill}" stroke="{stroke}" stroke-width="0.6" {extra}/>')
    def text(x,y,value,size=12,color='#99a0aa',extra=''):
        add(f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" {extra}>{html.escape(str(value))}</text>')
    add('''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="900" viewBox="0 0 900 900" role="img" aria-labelledby="title desc">
<title id="title">Contribution City</title><desc id="desc">Isometric city of daily GitHub contributions. Each lot represents one day in chronological row order; taller buildings mean more contributions on a logarithmic scale. Empty days are flat lots. Animation is decorative.</desc>
<defs><radialGradient id="bg"><stop stop-color="#1a2028"/><stop offset="1" stop-color="#0c1016"/></radialGradient><linearGradient id="line"><stop stop-color="#d2b478"/><stop offset="1" stop-color="#d2b478" stop-opacity="0"/></linearGradient></defs>
<style>text{font-family:Arial,Helvetica,sans-serif}.mono{font-family:monospace}.city{animation:arrive 1.6s ease-out both}.glimmer{animation:glimmer 6s ease-in-out infinite}@keyframes arrive{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}@keyframes glimmer{0%,100%{opacity:.85}50%{opacity:.35}}@media(prefers-reduced-motion:reduce){.city,.glimmer{animation:none}.traffic{display:none}}</style>
<rect width="900" height="900" rx="24" fill="url(#bg)"/>
<rect x=".5" y=".5" width="899" height="899" rx="24" fill="none" stroke="#2a3039"/>
''')
    text(52,59,'FIELDNOTES / '+username.upper(),11,'#cbb27d','letter-spacing="2.5" class="mono"')
    text(52,108,'Contribution City',34,'#f0eee8','font-weight="700" letter-spacing="-1"')
    text(52,137,'Small steps. A growing city.',14)
    text(848,58,'DESIGN PREVIEW' if demo else 'ACTIVITY / 365D',10,'#cbb27d','text-anchor="end" letter-spacing="1.4" class="mono"')
    if demo: text(848,78,'SYNTHETIC DATA',10,'#b0a58e','text-anchor="end" class="mono"')
    add('<path d="M52 162H848" stroke="#2b3139"/>')
    # Streets split the compact, chronological grid into sixteen neighbourhoods.
    extent_x,extent_y = 21.8,20.8
    poly([point(-.7,-.7, -11),point(extent_x,-.7,-11),point(extent_x,extent_y,-11),point(-.7,extent_y,-11)],'#070b0f')
    poly([point(-.7,-.7),point(extent_x,-.7),point(extent_x,extent_y),point(-.7,extent_y)],'#171d24','#343c45')
    for axis in [0,1]:
        for k in [4.9,10.25,15.6]:
            a,b = (point(k,-.5),point(k,extent_y)) if axis==0 else (point(-.5,k),point(extent_x,k))
            add(f'<path d="M{a[0]} {a[1]}L{b[0]} {b[1]}" stroke="#747266" stroke-opacity=".35" stroke-width=".7" stroke-dasharray="3 7"/>')
    add('<g class="city">')
    buildings=[]
    for i,d in enumerate(days):
        row,col = divmod(i,20)
        x,y = col+(col//5)*.45, row+(row//5)*.45
        buildings.append((x+y,i,x,y,d))
    for _,i,x,y,d in sorted(buildings):
        n=d['contributionCount']; w=.73
        corners=[(x,y),(x+w,y),(x+w,y+w),(x,y+w)]
        h=0 if not n else 8+100*math.log1p(n)/math.log1p(maximum)
        add('<g><title>'+html.escape(f"{d['date']}: {n} contributions")+'</title>')
        if n:
            poly([point(x+.2,y+.3),point(x+w+1,y+.3),point(x+w+1,y+w+.7),point(x+.2,y+w+.7)],'#0c1117',extra='opacity=".7"')
            # Visible west and east facades, then roof.
            poly([point(x,y+w),point(x+w,y+w),point(x+w,y+w,h),point(x,y+w,h)],'#363d46','#454c53')
            poly([point(x+w,y),point(x+w,y+w),point(x+w,y+w,h),point(x+w,y,h)],'#202831','#343c46')
            roof='#bfa578' if n==maximum else '#687078' if h>55 else '#505963'
            poly([point(a,b,h) for a,b in corners],roof,'#858a89')
            # Window slits follow the isometric faces, not the canvas axes.
            for floor in range(9,int(h)-3,12):
                for col in [0.17,0.47]:
                    lit = (i*7+floor+int(col*100))%5 != 0
                    fill='#dbc995' if lit else '#59616a'
                    extra='class="glimmer"' if lit and i%13==0 else ''
                    poly([point(x+col,y+w,floor),point(x+col+.11,y+w,floor),point(x+col+.11,y+w,floor+3),point(x+col,y+w,floor+3)],fill,extra=extra)
                    if (i+floor)%3:
                        poly([point(x+w,y+col,floor),point(x+w,y+col+.11,floor),point(x+w,y+col+.11,floor+3),point(x+w,y+col,floor+3)],'#b5a77f')
        else:
            poly([point(a,b) for a,b in corners],'#212831','#303842')
        add('</g>')
    add('</g>')
    # Two quiet points move along streets. No JavaScript or external resources.
    for k,delay in [(4.9,'0s'),(15.6,'-6s')]:
        a,b=point(k,-.4),point(k,extent_y)
        add(f'<circle class="traffic" r="1.6" fill="#ead8a7"><animate attributeName="cx" values="{a[0]};{b[0]}" dur="18s" begin="{delay}" repeatCount="indefinite"/><animate attributeName="cy" values="{a[1]};{b[1]}" dur="18s" begin="{delay}" repeatCount="indefinite"/></circle>')
    text(52,706,'ONE LOT / ONE DAY',10,'#aeb5bc','letter-spacing="1.6" class="mono"')
    text(848,706,'HEIGHT / CONTRIBUTIONS',10,'#aeb5bc','text-anchor="end" letter-spacing="1.6" class="mono"')
    add('<path d="M52 730H848" stroke="#303740"/>')
    for x,v,label in [(52,total,'CONTRIBUTIONS'),(338,active,'ACTIVE DAYS'),(622,best,'LONGEST STREAK')]:
        text(x,781,f'{v:,}'+('d' if label=='LONGEST STREAK' else ''),32,'#eee8dc','font-weight="600"')
        text(x,806,label,10,'#a6a8ac','letter-spacing="1.6" class="mono"')
    add('<path d="M302 751V810M586 751V810" stroke="#303740"/>')
    text(52,859,days[0]['date']+' / '+days[-1]['date'],11,'#8d969f','class="mono"')
    text(848,859,'Sample activity, not your statistics' if demo else 'Built from GitHub activity',11,'#8d969f','text-anchor="end"')
    add('</svg>')
    return ''.join(out)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--username',default=os.environ.get('GITHUB_USERNAME','jeffyoh312'))
    parser.add_argument('--output',default='assets/contribution-city.svg')
    parser.add_argument('--demo',action='store_true',help='Render clearly labelled synthetic preview; never used by workflow')
    args=parser.parse_args()
    if args.demo:
        rng=random.Random(92)
        start=dt.date(2025,10,15)
        days=[{'date':(start+dt.timedelta(days=i)).isoformat(),'contributionCount':rng.choice([0,0,0,1,2,3,5,8,13,21])} for i in range(365)]
    else: days=fetch_days(args.username)
    svg=render(days,args.username,args.demo)
    import xml.etree.ElementTree as ET
    ET.fromstring(svg)
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp');temp.write_text(svg,encoding='utf-8');temp.replace(path)
    print('Generated '+str(path))

if __name__=='__main__':
    try: main()
    except Exception as exc:
        print('City generation failed: '+str(exc),file=sys.stderr)
        sys.exit(1)

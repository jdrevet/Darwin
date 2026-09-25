import re, html, json, datetime as dt, collections
exec(open('scripts/body.py').read())
exec(open('scripts/compare.py').read().split("wd=collections.Counter")[0])   # W (wiki rows), R (rf pages), pdate
# --- corrections to Wikipedia
DATE_FIX={118:dt.date(2012,12,1),119:dt.date(2012,12,8),279:dt.date(2016,1,30)}
EP_FIX={518:191,531:95}
# series fixes by episode id: typo variants of a series name, varying names, unnumbered part 1
SERIES_FIX={
    61:('Les battements du temps',22),
    132:('À la découverte de Neandertal en nous',1),
    143:('Une hérédité des caractères acquis ?',1),144:('Une hérédité des caractères acquis ?',2),
    21:('Ressentir',1),22:('Ressentir',2),
    163:('Un voyage avec Oliver Sacks',3),
    23:('La course de la Reine rouge',1),
    235:('Arpenter le monde',1),
    336:("Entre le ciel et l'eau",1),
}
for w in W:
    w['date']=DATE_FIX.get(w['n'],w['date']); w['ep']=EP_FIX.get(w['n'],w['ep'])
    w['title']=re.sub(r"'''?|\[\[(?:[^|\]]*\|)?([^\]]*)\]\]",lambda m:m[1] or '',w['title']).strip()
rf_by_date={dt.date.fromisoformat(e['d']):e for e in json.load(open('data/radiofrance-pages.json'))}
def rf_for(d):
    for k in (0,1,-1):
        e=rf_by_date.get(d+dt.timedelta(days=k))
        if e: return e
# --- section classification
def kind(h):
    h=h.lower()
    if 'beau livre' in h or 'émission' in h: return 'skip'
    if re.search(r'chanson|titres? diffus|musi|extraits musicaux|sons et',h): return 'songs'
    if re.search(r'article|publication|revue',h): return 'articles'
    if re.search(r'livre',h): return 'books'
    if re.search(r'lien|site internet|en ligne',h): return 'links'
    if re.search(r'film|dvd',h): return 'films'
    if re.search(r'agenda|exposition|événement|evénement|colloque|annulation|été|rediffusion|année|noël|merci|médiamétrie|invité',h): return 'skip'
    return None   # sub-heading: stay in current section
def iso(d): 
    m=re.match(r'P0Y0M0DT(\d+)H(\d+)M(\d+)S',d or ''); return int(m[1])*3600+int(m[2])*60+int(m[3]) if m else None
def parse_song(t,artist_hint=None):
    t=re.sub(r'\s+',' ',t).strip(' -•')
    m=re.match(r'^(?P<t>.*?)\s*(?:album:\s*(?P<al>.*?))?\s*(?:label:\s*(?P<l>.*?))?\s*(?:parution:\s*(?P<y>\d{4}))?$',t)
    if m and (m['al'] or m['l'] or m['y']): return {'title':m['t'] or None,'artist':artist_hint,'label':m['l'],'text':None}
    if ' par ' not in t and t.count(' - ') in (1,2):
        x=t.split(' - '); return {'title':x[1],'artist':x[0],'label':x[2] if len(x)>2 else None,'text':None}
    m=re.match(r'^(.*?)\s*\(([^()]*)\)?$',t) if t.endswith(')') or re.search(r'\([^)]*$',t) else None
    label=None
    m2=re.search(r'\s*\(([^()]*)\)?\s*$',t)
    if m2 and ' par ' in t[:m2.start()]: label=m2[1].strip() or None; t=t[:m2.start()]
    if ' par ' in t:
        a,b=t.rsplit(' par ',1); return {'title':a.strip(' "«»'),'artist':b.strip(),'label':label,'text':None}
    return {'title':None,'artist':None,'label':label,'text':t}
def ems(inner): return [text(x).strip(' .') for x in re.findall(r'<em>(.*?)</em>',inner,re.S) if text(x).strip(' .')]
def year(t):
    y=re.findall(r'\b(1[5-9]\d\d|20[0-2]\d)\b',t); return int(y[-1]) if y else None
BOOK=re.compile(r'^(?P<a>[^.]{2,90}?)\.\s*(?P<t>.+)\.\s+(?P<p>[^.]+?),\s*(?P<y>\d{4})\s*\.?$')
def parse_book(inner):
    t=re.sub(r'_','',text(inner).replace('\n',' ')).strip(' -'); e=ems(inner)
    m=BOOK.match(t)
    if not e and m: return {'author':m['a'].strip(),'title':m['t'].strip(),'publisher':m['p'].strip(),'year':int(m['y']),'text':t}
    if e:
        i=t.find(e[0]); author=t[:i].strip(' .,:-') or None; rest=t[i+len(e[0]):].strip(' .,')
        return {'author':author,'title':e[0],'publisher':(re.sub(r',?\s*\b\d{4}\b.*$','',rest).strip(' .,') or None),'year':year(rest),'text':t}
    return {'author':None,'title':None,'publisher':None,'year':year(t),'text':t}
ART=re.compile(r'^(?P<a>.+?(?:et coll|et al\.?|\b[A-Z][a-z]?[A-Z]{0,2}))\s*\.\s+(?P<t>.+?)\s*\.\s+(?P<j>[^.:]+?)\s*,?\s*(?:\(?(?P<y>(?:19|20)\d\d)\b|\d+\s*:)')
def parse_article(inner):
    t=re.sub(r'_','',text(inner).replace('\n',' ')).strip(' -'); e=ems(inner); journal=None; authors=title=None
    m=ART.match(t)
    if m: return {'authors':m['a'].strip(' ,'),'title':m['t'].strip(),'journal':m['j'].strip(),'year':year(t),'text':t}
    cand=[x for x in e if x.lower() not in ('et coll','et al')]
    if cand:
        journal=cand[-1] if len(cand[-1])<80 else None
        pre=t[:t.rfind(journal)] if journal else t
        m=re.match(r'^(.*?(?:et coll|et al|\b[A-Z][A-Za-z]{0,2}|\b[A-Z]\.))\.\s+(.+)$',pre.strip())
        if m: authors,title=m[1].strip(' ,'),m[2].strip(' .')
    return {'authors':authors,'title':title,'journal':journal,'year':year(t),'text':t}
def parse_epigraph(inner):
    lines=[l.strip() for l in re.split(r'<br\s*/?>',inner)]
    lines=[l for l in lines if text(l)]
    if len(lines)<2: return None
    last=lines[-1]; e=ems(last)
    auth=text(re.sub(r'<em>.*?</em>','',last)).strip(' .,') if e else None
    q=' '.join(text(l) for l in lines[:-1]).strip()
    if e and auth and len(auth)<60: return {'text':q.strip(' "«»'),'author':auth,'work':e[0]}
    return None
def team(s):
    i=s.find(">L'équipe<")
    if i<0: return []
    seg=re.sub(r'<!--.*?-->','',s[i:s.find('SlidersRebond',i)])
    return [{'name':html.unescape(n),'role':text(r).strip(' .') or None} for n,r in re.findall(r'aria-label="([^"]+)"[^>]*>[^<]*</a></p>\s*<p class="typo-text-medium subtext[^>]*>(.*?)</p>',seg,re.S)]
def _old_team(s):
    i=s.find("L'équipe"); 
    if i<0: return []
    seg=s[i:i+20000]; seg=seg[:seg.find('Épisodes précédents')] if 'Épisodes précédents' in seg else seg
    t=[x for x in (text(p) for p in re.split(r'<[^>]+>',seg)) if x][1:]
    return [{'name':t[k],'role':t[k+1]} for k in range(0,len(t)-1,2) if len(t[k])<50]
def themes(s):
    i=s.find('data-testid="BlocTaxonomie"')
    if i<0: return []
    seg=s[i:s.find('</ul>',i)]
    return list(dict.fromkeys(html.unescape(a).strip() for a in re.findall(r'<a title="([^"]+)"',seg)))
def content(e):
    s=page(e['url']); b=body(s) or ''
    out=dict(standfirst=None,intro=[],articles=[],books=[],songs=[],links=[],films=[],themes=themes(s),team=team(s),image=None)
    m=re.search(r'<p class="chapo[^"]*"[^>]*>(.*?)</p>',s,re.S); out['standfirst']=text(m[1]) if m else None
    m=re.search(r'"@type":"RadioEpisode".*?"image":\{[^}]*"url":"([^"]+)"',s); out['image']=m[1] if m else None
    sec='intro'; hint=None
    for k,inner in blocks(b):
        if k=='h':
            h=text(inner); kd=kind(h)
            if kd: sec=kd; hint=None
            else: hint=h
            continue
        t=text(inner)
        if not t or t in('.','**'): continue
        if sec=='intro': out['intro'].append(t)
        elif sec in ('songs','books','articles'):
            t=re.sub(r'\s*#+\s*',' / ',re.sub(r'_','',t.replace('\n',' '))).strip(' -•/')
            if sec=='songs' and hint: t=f"{hint} – {t}"
            if t: out[sec].append(t)
        elif sec=='links':
            a=re.search(r'href="([^"]+)"',inner); out['links'].append({'text':t.replace('\n',' '),'url':html.unescape(a[1]) if a else None})
        elif sec=='films': out['films'].append({'text':t})
    return out
def richness(c): return sum(len(c[k]) for k in ('articles','books','songs','links'))+len(' '.join(c['intro']))/500
SER=re.compile(r'^(.*?)\s*\((\d+)\)\s*(?:[-–:.]\s*(.*))?$')
def series(title):
    m=SER.match(title)
    if m and m[1]: 
        name=m[1].strip(' :-'); sub=(m[3] or '').strip(' "«»') or None
        return {'name':name,'part':int(m[2])},sub
    return None,None
eps=collections.defaultdict(list)
for w in W: eps[w['ep']].append(w)
out=[]; unmatched=[]
for n,rows in sorted(eps.items()):
    rows.sort(key=lambda w:w['date'])
    first=rows[0]
    if first['r']: unmatched.append(('no original row',n))
    pages=[(w,rf_for(w['date'])) for w in rows]
    for w,e in pages:
        if not e: unmatched.append(('no rf page',w['n'],str(w['date'])))
    of=pages[0][1]
    cands=[(content(e),e) for w,e in pages if e]
    best=max(cands,key=lambda c:richness(c[0]))[0] if cands else None
    ser,sub=series(first['title'])
    if n in SERIES_FIX: ser={'name':SERIES_FIX[n][0],'part':SERIES_FIX[n][1]}
    teaser=next((re.sub(r"'''?|''",'',w_raw) for w_raw in [None] if w_raw),None)
    out.append({
        'id':n,'title':first['title'],'series':ser,
        'firstBroadcast':str(first['date']),
        'rerunCount':len(rows)-1,
        'durationSeconds':iso(of and of['duration']),
        'audioUrl':of and of['audio'],'pageUrl':of and of['url'],
        'imageUrl':best and best['image'],
        'teaser':first.get('teaser'),
        'standfirst':best and best['standfirst'],
        'intro':best and '\n\n'.join(best['intro']) or None,
        **{k:(best[k] if best else []) for k in ('articles','books','songs','links','films','themes','team')},
        'broadcasts':[{'number':w['n'],'date':str(w['date']),'rerun':i} for i,w in enumerate(rows)],
    })
# topics generated once by an LLM, see data/topics.json
T=json.load(open('data/topics.json'))
out=[{k2:v2 for k,v in e.items() for k2,v2 in ([(k,v),('topics',T.get(str(e['id']),[]))] if k=='themes' else [(k,v)])} for e in out]
doc={"generatedAt":str(dt.date.today()),"sources":{"wikipedia":"https://fr.wikipedia.org/wiki/Sur_les_%C3%A9paules_de_Darwin","radiofrance":"https://www.radiofrance.fr/franceinter/podcasts/sur-les-epaules-de-darwin"},"episodes":out}
json.dump(doc,open('data/episodes.json','w'),ensure_ascii=False,indent=1)
print(len(out),"episodes"); print("issues",unmatched)

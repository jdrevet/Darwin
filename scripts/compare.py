import re, json, datetime as dt, collections, unicodedata
from zoneinfo import ZoneInfo
M={'jan':1,'dec':12,'fev':2,'janv':1,'janvier':1,'févr':2,'fév':2,'février':2,'mars':3,'avr':4,'avril':4,'mai':5,'juin':6,'juil':7,'juillet':7,'août':8,'sept':9,'septembre':9,'oct':10,'octobre':10,'nov':11,'novembre':11,'déc':12,'décembre':12}
def pdate(s):
    s=s.replace('{{1er}}','1');m=re.match(r'(\d+)(?:er)?\s+([a-zéû]+)\.?\s+(\d{4})',s.strip())
    return dt.date(int(m[3]),M[m[2]],int(m[1])) if m and m[2] in M else None
t=open('data/wikipedia.txt').read()
W=[]
for r in t.split('\n|-\n')[1:]:
    c=[x for x in r.split('\n') if x.startswith('|') and not x.startswith('|}')]
    c=[re.sub(r'^\|(align="left"\|)?','',x).strip() for x in c]
    W.append(dict(n=int(c[0]),ep=int(c[1]),r=c[2],title=c[3],date=pdate(c[4]),raw=c[4],teaser=(re.sub(r"'''?|''",'',c[5]).strip() if len(c)>5 else '') or None))
bad=[w for w in W if not w['date']]; print("wiki unparsed dates",[(w['n'],w['raw']) for w in bad])
R=json.load(open('raw/rf.json'))
for e in R:
    d=dt.datetime.fromisoformat(e['date'].replace('Z','+00:00')).astimezone(ZoneInfo('Europe/Paris')).date()
    e['d']=d
    m=re.search(r"(?:émission|diffusion) du (\d+(?:er)? \w+ \d{4})",e['desc'] or '')
    e['orig']=pdate(m[1]) if m else None
    e['isrerun']=bool(re.search(r'rediffusion|nouvelle diffusion|déjà diffusée',(e['desc'] or '')+e['name'],re.I))
json.dump([{**e,'d':str(e['d']),'orig':str(e['orig'])} for e in R],open('data/radiofrance-pages.json','w'),ensure_ascii=False,indent=1)
wd=collections.Counter(w['date'] for w in W); rd=collections.Counter(e['d'] for e in R)
print("wiki dup dates",[(d,c) for d,c in wd.items() if c>1])
print("rf dup dates",[(str(d),c) for d,c in rd.items() if c>1])
print("wiki dates missing on RF:",len([d for d in wd if d not in rd]))
for w in W:
    if w['date'] not in rd: print("  W-only",w['n'],w['ep'],w['r'] or '-',w['date'],w['title'][:60])
print("RF dates missing in wiki:")
for e in R:
    if e['d'] not in wd: print("  RF-only",e['d'],e['name'][:60],e['url'][-50:])
# original date per episode per wiki
orig={}
for w in W:
    if not w['r']: orig.setdefault(w['ep'],w['date'])
byd={e['d']:e for e in R}
print("R-marker vs RF rerun text / original date:")
mism=0
for w in W:
    e=byd.get(w['date'])
    if not e: continue
    if w['r'] and e['orig'] and orig.get(w['ep'])!=e['orig']:
        mism+=1;print("  ORIG MISMATCH",w['n'],w['ep'],w['r'],w['date'],'wikiOrig',orig.get(w['ep']),'rfOrig',e['orig'],'|',w['title'][:40],'|',e['name'][:40])
    if not w['r'] and (e['orig'] or e['isrerun']):
        mism+=1;print("  WIKI SAYS ORIGINAL, RF SAYS RERUN",w['n'],w['ep'],w['date'],w['title'][:40],'|',(e['desc'] or '')[:120])
print("reruns in wiki",sum(1 for w in W if w['r']),"rf pages mentioning an original date",sum(1 for e in R if e['orig']),"rf rerun-like",sum(1 for e in R if e['isrerun']))
# R numbering consistency
cnt=collections.defaultdict(list)
for w in sorted(W,key=lambda w:w['date']): cnt[w['ep']].append(w)
for ep,l in cnt.items():
    exp=['']+[f'R{i}' for i in range(1,len(l))]
    if [x['r'] for x in l]!=exp: print("  R SEQUENCE",ep,[(x['r'] or '-',str(x['date'])) for x in l])
print("--- non-saturday wiki dates")
for w in W:
    if w['date'].weekday()!=5: print(" ",w['n'],w['ep'],w['r'] or '-',w['date'],w['date'].strftime('%A'),w['title'][:50])
print("--- wiki rows on the RF-claimed original dates")
for d in ['2015-12-12','2013-03-02','2017-01-07','2012-12-08']:
    for w in W:
        if str(w['date'])==d: print(" ",d,w['n'],w['ep'],w['r'] or '-',w['title'])
def norm(s):
    s=unicodedata.normalize('NFKD',s.lower()); s=''.join(c for c in s if c.isalnum() or c==' ')
    return set(s.split())
print("--- title mismatches (matched by date)")
k=0
for w in W:
    e=byd.get(w['date'])
    if not e: continue
    a,b=norm(re.sub(r"'''|''",'',w['title'])),norm(e['name'])
    if len(a&b)/max(1,min(len(a),len(b)))<0.5: k+=1;print(" ",w['n'],w['ep'],w['r'] or '-',w['date'],'|',w['title'][:50],'|',e['name'][:60])
print("count",k)
wr=[w for w in W if w['r'] and w['date'] in byd]
print("wiki reruns with an RF page",len(wr),"of which RF text says rerun",sum(1 for w in wr if byd[w['date']]['isrerun'] or byd[w['date']]['orig']))
yrs=collections.Counter(w['date'].year for w in wr if not (byd[w['date']]['isrerun'] or byd[w['date']]['orig']))
print("  reruns whose RF page doesn't say so, by year",sorted(yrs.items()))
print("--- RF titles around Visages")
for d in ['2017-01-07','2017-06-24','2021-04-17']:
    e=byd.get(dt.date.fromisoformat(d)); print(" ",d,e and e['name'],'|',e and (e['desc'] or '')[:150])
print("--- rerun whose RF title differs from RF title of wiki original")
fix={dt.date(2012,11,1):dt.date(2012,12,1),dt.date(2012,11,8):dt.date(2012,12,8),dt.date(2016,1,31):dt.date(2016,1,30)}
k=0
for w in W:
    if not w['r']: continue
    e=byd.get(w['date']); o=orig.get(w['ep']); o=fix.get(o,o); eo=byd.get(o)
    if not e or not eo: continue
    a,b=norm(e['name']),norm(eo['name'])
    if a!=b: k+=1;print(" ",w['n'],w['ep'],w['r'],w['date'],'|',e['name'][:55],'|orig',o,eo['name'][:55])
print("count",k)
print("--- same title used by several original episodes (wiki)")
tt=collections.defaultdict(list)
for w in W:
    if not w['r']: tt[' '.join(sorted(norm(re.sub(r"'''|''",'',w['title']))))].append((w['ep'],str(w['date']),w['title']))
for v in tt.values():
    if len(v)>1: print(" ",v)

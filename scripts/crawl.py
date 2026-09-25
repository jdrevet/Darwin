import re, json, urllib.request, concurrent.futures as cf
BASE="https://www.radiofrance.fr/franceinter/podcasts/sur-les-epaules-de-darwin"
import time, hashlib
import os, tarfile
if not os.path.isdir("raw/cache") and os.path.exists("raw/radiofrance-pages.tar.gz"):
    tarfile.open("raw/radiofrance-pages.tar.gz").extractall("raw", filter="data")
os.makedirs("raw/cache",exist_ok=True)
def get(u):
    f="raw/cache/"+hashlib.md5(u.encode()).hexdigest()
    if os.path.exists(f): return open(f).read()
    for a in range(5):
        try:
            s=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=30).read().decode()
            open(f,"w").write(s); time.sleep(0.3); return s
        except Exception as e:
            time.sleep(5*(a+1))
    raise RuntimeError(u)
urls=[]; p=1
while True:
    s=get(f"{BASE}?p={p}")
    m=re.search(r'"@type":"ItemList".*?"itemListElement":(\[.*?\])',s)
    items=[i["url"] for i in json.loads(m.group(1))] if m else []
    new=[u for u in items if u not in urls]
    if not new: break
    urls+=new; p+=1
print("pages",p-1,"urls",len(urls))
def ep(u):
    s=get(u)
    for b in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>',s,re.S):
        for n in json.loads(b).get("@graph",[]):
            if n.get("@type")=="RadioEpisode":
                return {"url":u,"name":n["name"],"date":n.get("dateCreated"),"desc":n.get("description"),
                        "audio":n.get("mainEntity",{}).get("contentUrl"),"duration":n.get("mainEntity",{}).get("duration")}
    return {"url":u,"error":True}
with cf.ThreadPoolExecutor(3) as ex: eps=list(ex.map(ep,urls))
json.dump(eps,open("raw/rf.json","w"),ensure_ascii=False,indent=1)
print("done",len(eps),sum(1 for e in eps if e.get("error")))

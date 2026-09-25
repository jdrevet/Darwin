import re, html, json, hashlib, collections
import os, tarfile
if not os.path.isdir("raw/cache") and os.path.exists("raw/radiofrance-pages.tar.gz"):
    tarfile.open("raw/radiofrance-pages.tar.gz").extractall("raw", filter="data")
def page(u): return open("raw/cache/"+hashlib.md5(u.encode()).hexdigest()).read()
def body(s):
    i=s.find('<div class="Body '); 
    if i<0: return None
    j=s.find('data-testid="BlocTaxonomie"',i); j=j if j>0 else s.find('L\'équipe',i)
    return s[i:j if j>0 else i+200000]
def clean(x):
    x=re.sub(r'<!--.*?-->','',x); x=re.sub(r'<span class="g-sr-only">.*?</span>','',x)
    x=re.sub(r'<div class="AdSlot.*?</div></div>','',x,flags=re.S)
    return x
def blocks(b):
    b=clean(b); out=[]
    for m in re.finditer(r'<(h[1-6]|p|li)\b[^>]*>(.*?)</\1>',b,re.S):
        tag,inner=m[1],m[2]
        if tag=='p' and 'AdSlot-label' in m[0]: continue
        out.append((tag[0] if tag[0]!='h' else 'h',inner))
    return out
def text(inner):
    t=re.sub(r'<br\s*/?>','\n',inner); t=html.unescape(re.sub(r'<[^>]+>','',t))
    return re.sub(r'[ \t\xa0]+',' ',t).strip()

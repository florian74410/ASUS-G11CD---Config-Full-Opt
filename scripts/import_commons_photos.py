#!/usr/bin/env python3
"""Download only verified exact-match Wikimedia Commons photos (CC/PD) to Assets/.
Run: python3 scripts/import_commons_photos.py --limit 200
Never substitutes a generic or different model; logs missing references.
"""
import argparse, json, re, time, unicodedata, urllib.parse, urllib.request, urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
API="https://commons.wikimedia.org/w/api.php"
USER_AGENT="ComponentsDatabase-HardwareLab/0.1 (local educational catalog; contact via GitHub florian74410)"
EXTENSIONS={".jpg",".jpeg",".png",".webp"}
def norm(v):
    v=unicodedata.normalize("NFKD",str(v))
    return re.sub(r"[^a-z0-9]+"," ", "".join(c for c in v if not unicodedata.combining(c)).lower()).strip()
def request(params):
    url=API+"?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"User-Agent":USER_AGENT,"Accept":"application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req,timeout=25) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt==2:raise
            time.sleep(8*(attempt+1))
def get_file(url,limit_bytes=2500000):
    req=urllib.request.Request(url,headers={"User-Agent":USER_AGENT})
    with urllib.request.urlopen(req,timeout=35) as response:
        data=response.read(limit_bytes+1)
        if len(data)>limit_bytes: raise ValueError("image too large")
        if response.headers.get("Content-Type","").lower().split(";")[0] not in ("image/jpeg","image/png","image/webp"):raise ValueError("unexpected file type")
        return data
def match(query,title):
    # No cross-brand substitution: exact designation must be present in photo title.
    q=norm(query).split()
    t=norm(title).split()
    if len(q)<2:return False
    return all(token in t for token in q if len(token)>1)
def candidates(query):
    raw=request({"action":"query","generator":"search","gsrsearch":'filetype:bitmap '+query,"gsrnamespace":6,"gsrlimit":12,"prop":"imageinfo","iiprop":"url|extmetadata|size","iiurlwidth":520,"format":"json","formatversion":2})
    for page in raw.get("query",{}).get("pages",[]):
        info=(page.get("imageinfo") or [{}])[0];title=page.get("title","")
        if not match(query,title):continue
        meta=info.get("extmetadata",{})
        lic=meta.get("LicenseShortName",{}).get("value","")
        if not re.search(r"CC0|CC BY|Public domain|PD-",lic,re.I):continue
        url=info.get("thumburl") or info.get("url")
        if not url:continue
        yield title,lic,url,info.get("descriptionurl",""),meta.get("Artist",{}).get("value",""),info.get("url")
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--limit",type=int,default=45);args=ap.parse_args()
    report={"downloaded":[],"missing":[],"skipped":[],"errors":[]}
    paths=[]
    for directory in sorted((ROOT/"Component").iterdir()):
        if directory.is_dir():paths.extend(sorted(directory.glob("*.json")))
    checked=0;limited=0
    for p in paths:
        try:
            d=json.loads(p.read_text(encoding="utf8"))
            cat=d.get("category") or p.parent.name
            model=d.get("model") or "";brand=d.get("manufacturer") or ""
            # Search most specific brand/model first; never infer a model from the GPU chip alone.
            if not brand or not model:
                report["skipped"].append({"file":str(p.relative_to(ROOT)),"reason":"brand/model absent"});continue
            folder=ROOT/"Assets"/cat;folder.mkdir(exist_ok=True,parents=True)
            existing=[f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in EXTENSIONS and (norm(p.stem) in norm(f.stem) or norm(brand+" "+model) in norm(f.stem))]
            if existing:
                report["skipped"].append({"file":str(p.relative_to(ROOT)),"reason":"photo existing"});continue
            if checked>=args.limit:break
            checked+=1
            found=False
            for title,lic,url,page,artist,original_url in candidates(brand+" "+model):
                suffix=Path(urllib.parse.urlparse(url).path).suffix.lower()
                if suffix not in EXTENSIONS:suffix=".jpg"
                target=folder/(cat+" - "+brand+" "+model+suffix)
                data=get_file(url)
                target.write_bytes(data)
                original_folder=ROOT/"Assets"/"Brut"/cat
                original_folder.mkdir(parents=True,exist_ok=True)
                original_ext=Path(urllib.parse.urlparse(original_url).path).suffix.lower()
                if original_ext in EXTENSIONS:
                    original_target=original_folder/(cat+" - "+brand+" "+model+original_ext)
                    try:
                        raw=get_file(original_url,limit_bytes=12000000)
                        original_target.write_bytes(raw)
                    except Exception as ex:
                        report["errors"].append({"file":str(original_target.relative_to(ROOT)),"error":"Original not archived: "+str(ex)[:180]})
                report["downloaded"].append({"component":d.get("full_name"),"file":str(target.relative_to(ROOT)),"source":page,"license":lic,"author_html":artist,"bytes":len(data),"original_url":original_url})
                found=True;break
            if not found:report["missing"].append({"component":d.get("full_name"),"reason":"No exact-model licensed photo on Wikimedia Commons"})
        except Exception as ex:
            report["errors"].append({"file":str(p.relative_to(ROOT)),"error":str(ex)[:300]})
            if "HTTP Error 429" in str(ex):
                limited+=1
                if limited>=2:
                    report["errors"].append({"reason":"Search rate limited by Wikimedia; stop batch and resume later"})
                    break
        time.sleep(1.5)
    report["remaining_unchecked"]=max(0,len(paths)-checked)
    (ROOT/"ASSET_IMPORT_REPORT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print({k:len(v) for k,v in report.items()})
if __name__=="__main__":main()

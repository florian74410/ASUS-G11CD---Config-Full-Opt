#!/usr/bin/env python3
"""Photo Collector V2: scan every component JSON, find up to 5 model-matched photos,
download originals, maintain gallery metadata, and resume safely.
Sources: verified-licensed Wikimedia Commons plus already sourced external JSON images.
External images without confirmed reuse rights stay LOCAL ONLY (gitignored).
No Google scraping, no attribution stripping, no imaginary photo substitutes.
"""
import argparse, hashlib, json, mimetypes, re, time, unicodedata
import urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
API="https://commons.wikimedia.org/w/api.php"
UA="HardwareLab-PhotoCollector/2.0 (github.com/florian74410/ASUS-G11CD---Config-Full-Opt)"
EXT={".jpg",".jpeg",".png",".webp"}
MIME={"image/jpeg":".jpg","image/png":".png","image/webp":".webp"}
def normalize(value):
    v=unicodedata.normalize("NFKD",str(value or ""))
    return re.sub(r"[^a-z0-9]+"," ","".join(c for c in v if not unicodedata.combining(c)).lower()).strip()
def query(url,params=None):
    if params:url+="?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
    for retry in range(4):
        try:
            with urllib.request.urlopen(req,timeout=25) as r:return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code not in (429,500,502,503,504) or retry==3:raise
            time.sleep(min(45,5*2**retry))
def download(url,max_bytes=16000000):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"image/jpeg,image/png,image/webp"})
    with urllib.request.urlopen(req,timeout=28) as r:
        kind=r.headers.get("Content-Type","").split(";")[0].lower()
        if kind not in MIME:raise ValueError("not an image: "+kind)
        body=r.read(max_bytes+1)
        if len(body)>max_bytes:raise ValueError("image exceeds maximum size")
        if not body:raise ValueError("empty image")
        return body,MIME[kind]
def exact_match(name,title):
    expected=normalize(name).split()
    actual=normalize(title).split()
    if len(expected)<2:return False
    return all(term in actual for term in expected if len(term)>1)
def discover(brand,model):
    designation=(brand+" "+model).strip()
    result=query(API,{"action":"query","generator":"search","gsrsearch":"filetype:bitmap "+designation,
        "gsrnamespace":6,"gsrlimit":20,"prop":"imageinfo",
        "iiprop":"url|extmetadata|size","iiurlwidth":800,"format":"json","formatversion":2})
    output=[]
    for page in result.get("query",{}).get("pages",[]):
        title=page.get("title","")
        if not exact_match(designation,title):continue
        info=(page.get("imageinfo") or [{}])[0]
        license_text=info.get("extmetadata",{}).get("LicenseShortName",{}).get("value","")
        if not re.search(r"(?:CC0|CC BY|Public domain|PD-)",license_text,re.I):continue
        url=info.get("url");thumb=info.get("thumburl") or url
        if not url or not thumb:continue
        output.append({"url":url,"thumbnail":thumb,"source":info.get("descriptionurl",""),
            "license":license_text,"author":info.get("extmetadata",{}).get("Artist",{}).get("value",""),
            "view":"product","label":title.removeprefix("File:")})
    return output
def scan_existing(d,cat):
    images=d.get("images") or []
    for p in (ROOT/"Assets"/cat).glob("*"):
        if p.suffix.lower() not in EXT:continue
        stem=normalize(p.stem).replace(" ","")
        identity=normalize(d["id"]).replace(" ","")
        if identity and identity in stem:
            relative=str(p.relative_to(ROOT))
            if not any(i.get("local_path")==relative for i in images if isinstance(i,dict)):
                images.append({"local_path":relative,"label":p.stem,"view":"existing","license":"unknown","source":""})
    return images
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--limit",type=int,default=0,help="maximum JSON files processed; 0=all")
    parser.add_argument("--max-photos",type=int,default=5)
    parser.add_argument("--refresh",action="store_true",help="retry sources even if already collected")
    args=parser.parse_args()
    report=[];processed=0
    for path in sorted((ROOT/"Component").glob("*/*.json")):
        if args.limit and processed>=args.limit:break
        processed+=1
        try:
            d=json.loads(path.read_text(encoding="utf-8"))
            brand,model=d.get("manufacturer",""),d.get("model","")
            cat=d.get("category") or path.parent.name
            if not brand or not model or not d.get("id"):raise ValueError("manufacturer/model/id missing")
            entries=scan_existing(d,cat)
            # Local actual files count; broken URLs are not counted as downloaded.
            def is_local(x):
                p=x.get("local_path")
                return p and (ROOT/p).is_file()
            acquired={hashlib.sha256((ROOT/x["local_path"]).read_bytes()).hexdigest() for x in entries if isinstance(x,dict) and is_local(x)}
            count=sum(bool(is_local(x)) for x in entries if isinstance(x,dict))
            sources=[]
            for item in entries:
                if not isinstance(item,dict) or not str(item.get("url","")).startswith("https://"):continue
                sources.append((item,"external"))
            if count<args.max_photos or args.refresh:
                try:sources.extend((item,"commons") for item in discover(brand,model))
                except Exception as e:report.append({"component":d["id"],"warning":"Commons unavailable: "+str(e)[:180]})
            new=0
            for item,origin in sources:
                if count>=args.max_photos:break
                if item.get("local_path") and is_local(item):continue
                url=item["url"]
                try:
                    raw,ext=download(url)
                    digest=hashlib.sha256(raw).hexdigest()
                    if digest in acquired:continue
                    index=count+1
                    ident=re.sub(r"[^A-Za-z0-9_-]","_",d["id"])
                    # Commons images have publication rights; private previews do not.
                    public=origin=="commons"
                    rawfolder=ROOT/"Assets"/"Brut"/cat if public else ROOT/"Assets"/"Brut"/"LocalPreview"/cat
                    rawfolder.mkdir(parents=True,exist_ok=True)
                    rawfile=rawfolder/(ident+"_photo"+str(index).zfill(2)+ext)
                    rawfile.write_bytes(raw)
                    item["local_path"]=str(rawfile.relative_to(ROOT))
                    item["sha256"]=digest
                    item["storage"]="original"
                    if public:
                        display=ROOT/"Assets"/cat
                        display.mkdir(parents=True,exist_ok=True)
                        outfile=display/rawfile.name
                        # Keep original bytes: image processing can be added later.
                        outfile.write_bytes(raw)
                        item["gallery_path"]=str(outfile.relative_to(ROOT))
                    else:item["gallery_path"]=item["local_path"]
                    item["rights_status"]="licensed" if public else "unverified_local_only"
                    if origin=="commons":entries.append(item)
                    acquired.add(digest);count+=1;new+=1
                except Exception as e:
                    report.append({"component":d["id"],"url":url,"error":str(e)[:200]})
            if entries != (d.get("images") or []):
                d["images"]=entries
                path.write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
            report.append({"component":d["id"],"downloaded":new,"local_photos":count,"target":args.max_photos})
        except Exception as e:
            report.append({"component":str(path.relative_to(ROOT)),"error":str(e)[:300]})
        # Gentle Commons usage for large catalogues.
        if processed%5==0:time.sleep(1)
    output=ROOT/"PHOTO_COLLECTOR_REPORT.json"
    output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Processed:",processed,"| downloaded:",sum(x.get("downloaded",0) for x in report),
          "| see:",output.name)
if __name__=="__main__":main()

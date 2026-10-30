#!/usr/bin/env python3
"""Download discovered retailer images for LOCAL PREVIEW ONLY (not redistribution).
For images with explicit redistribution rights, use licensed Commons workflow instead.
python3 scripts/download_photo_previews.py --limit 50
"""
import argparse,json,re,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ALLOWED={".jpg",".jpeg",".png",".webp"}
HEADERS={"User-Agent":"Mozilla/5.0 (compatible; HardwareLabLocalPreview/1.0)","Accept":"image/avif,image/webp,image/png,image/jpeg,*/*"}
def slug(v):return re.sub(r"[^A-Za-z0-9._-]+","_",str(v)).strip("_")[:110]
def main():
 p=argparse.ArgumentParser();p.add_argument("--limit",type=int,default=50);args=p.parse_args()
 results=[];count=0
 for path in sorted((ROOT/"Component").glob("*/*.json")):
  d=json.loads(path.read_text(encoding="utf-8"));cat=d.get("category",path.parent.name)
  for i,item in enumerate(d.get("images") or []):
   if count>=args.limit:break
   if not isinstance(item,dict) or not str(item.get("url","")).startswith("https://"):continue
   if item.get("license","").lower().startswith("cc"):continue
   count+=1
   # External images with unconfirmed reuse rights are never added to public git.
   targetdir=ROOT/"Assets"/"Brut"/"LocalPreview"/cat;targetdir.mkdir(parents=True,exist_ok=True)
   target=targetdir/(slug(cat+" - "+d.get("manufacturer","")+" "+d.get("model","")+" - "+str(i+1))+".jpg")
   try:
    req=urllib.request.Request(item["url"],headers=HEADERS)
    with urllib.request.urlopen(req,timeout=22) as response:
     kind=response.headers.get("Content-Type","").split(";")[0].lower()
     if kind not in ("image/jpeg","image/png","image/webp"):raise ValueError("unexpected media type: "+kind)
     ext={"image/jpeg":".jpg","image/png":".png","image/webp":".webp"}[kind]
     target=target.with_suffix(ext)
     b=response.read(7000001)
     if len(b)>7000000:raise ValueError("image too large")
     target.write_bytes(b)
    results.append({"id":d.get("id"),"status":"downloaded_local_only","file":str(target.relative_to(ROOT)),"source":item.get("source"),"url":item["url"],"rights":"unverified, not for public commit"})
   except Exception as e:results.append({"id":d.get("id"),"status":"failed","url":item["url"],"error":str(e)[:200]})
  if count>=args.limit:break
 report=ROOT/"LOCAL_PHOTO_PREVIEW_REPORT.json";report.write_text(json.dumps(results,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print(f"Processed {count}; downloaded {sum(x['status']=='downloaded_local_only' for x in results)}; see {report.name}")
if __name__=="__main__":main()

#!/usr/bin/env python3
"""Local-only hardware dashboard; no cloud service or frontend dependencies."""
import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/"web"
CATS=("CPU","GPU","Motherboard","NVMe","SDD","PSU","Extra","Case","RAM","Cooling")
def collect():
    entries=[];errors=[];seen=set()
    for cat in CATS:
        for p in sorted((ROOT/"Component"/cat).glob("*.json")):
            try:
                obj=json.loads(p.read_text(encoding="utf8"))
                if obj.get("category")!=cat or not obj.get("full_name") or not obj.get("id"):
                    raise ValueError("catégorie, nom ou identifiant manquant/incohérent")
                if obj["id"] in seen: raise ValueError("identifiant dupliqué")
                seen.add(obj["id"])
                obj["_json"]=str(p.relative_to(ROOT))
                base=p.stem
                photos=[x for ext in (".jpg",".jpeg",".png",".webp") for x in [(ROOT/"Assets"/cat/(base+ext))] if x.is_file()]
                obj["_photo"]="/files/"+str(photos[0].relative_to(ROOT)) if photos else None
                entries.append(obj)
            except Exception as exc: errors.append(f"{p.relative_to(ROOT)} : {exc}")
    return entries,errors

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path=unquote(urlsplit(self.path).path)
        if path=="/api/components":
            items,errors=collect()
            body=json.dumps({"components":items,"errors":errors,"categories":CATS},ensure_ascii=False).encode()
            self.send_response(200);self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Cache-Control","no-store");self.send_header("Content-Length",str(len(body)))
            self.end_headers();self.wfile.write(body);return
        if path=="/":path="/index.html"
        if path.startswith("/files/"):
            root=ROOT/"Assets";relative=path[len("/files/"):]
            if not relative.startswith("Assets/"):return self.send_error(404)
            target=(ROOT/relative).resolve()
        else:
            root=WEB;target=(WEB/path.lstrip("/")).resolve()
        if not target.is_relative_to(root.resolve()) or not target.is_file():return self.send_error(404)
        data=target.read_bytes()
        self.send_response(200);self.send_header("Content-Type",mimetypes.guess_type(target.name)[0] or "application/octet-stream")
        self.send_header("Cache-Control","no-store");self.send_header("Content-Length",str(len(data)))
        self.end_headers();self.wfile.write(data)
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--port",type=int,default=8765)
    p.add_argument("--host",default="127.0.0.1",help="Local only by default")
    a=p.parse_args()
    print(f"ASUS G11CD Dashboard : http://{a.host}:{a.port}  (Ctrl+C pour quitter)")
    ThreadingHTTPServer((a.host,a.port),Handler).serve_forever()

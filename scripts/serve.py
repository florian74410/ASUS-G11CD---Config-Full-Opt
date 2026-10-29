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


# MARKETPLACE_V1_BACKEND
import re
import threading
from datetime import datetime, timezone
from uuid import uuid4
from urllib.parse import urlparse
STORE=ROOT/"Listings"
STORE_LOCK=threading.RLock()
STATES={"spotted","negotiating","accepted","purchased","declined","expired"}
PLATFORMS={"Leboncoin","eBay","Autre"}
def listings():
    out=[];errors=[]
    for p in sorted(STORE.glob("*.json")):
        try:
            d=json.loads(p.read_text(encoding="utf-8"));d["_path"]=p.name;out.append(d)
        except Exception as ex: errors.append(f"{p.name}: {ex}")
    return out,errors
def validate(d, old=None):
    if not isinstance(d,dict): raise ValueError("Objet JSON attendu")
    text_fields=("component_name","component_id","url","condition","notes")
    def string(k,maxlen=500):
        v=d.get(k,"")
        if not isinstance(v,str) or len(v)>maxlen:raise ValueError(f"Champ {k} invalide")
        return v.strip()
    component_name=string("component_name",180)
    if not component_name:raise ValueError("Référence obligatoire")
    platform=d.get("platform")
    if platform not in PLATFORMS:raise ValueError("Plateforme invalide")
    status=d.get("status","spotted")
    if status not in STATES:raise ValueError("Statut invalide")
    pricing=d.get("pricing",{})
    if not isinstance(pricing,dict):raise ValueError("Prix invalides")
    values={}
    for k in ("seller_asking","shipping_estimated","our_offer","agreed_price","paid_price","shipping_paid"):
        v=pricing.get(k)
        if v in ("",None):v=None
        if v is not None and (type(v) not in (int,float) or not 0<=v<=10000000):raise ValueError(f"Prix {k} invalide")
        values[k]=v
    if values["seller_asking"] is None:raise ValueError("Prix vendeur obligatoire")
    if status=="purchased" and values["paid_price"] is None:raise ValueError("Prix réellement payé obligatoire pour achat confirmé")
    raw=d.get("negotiation",[])
    if not isinstance(raw,list) or len(raw)>100:raise ValueError("Historique invalide")
    events=[]
    for entry in raw:
        if not isinstance(entry,dict) or entry.get("actor") not in ("buyer","seller") or type(entry.get("amount")) not in (int,float) or entry["amount"]<0:raise ValueError("Offre invalide")
        events.append({"actor":entry["actor"],"amount":entry["amount"],"date":str(entry.get("date") or datetime.now(timezone.utc).isoformat())[:40],"note":str(entry.get("note",""))[:500]})
    url=string("url",1000)
    if url and urlparse(url).scheme not in ("https","http"):raise ValueError("URL HTTP(S) requise")
    now=datetime.now(timezone.utc).isoformat()
    return {"schema_version":"1.0","listing_id":old["listing_id"] if old else "LST-"+uuid4().hex[:12].upper(),
        "component_id":string("component_id",180),"component_name":component_name,
        "platform":platform,"url":url,"status":status,"condition":string("condition",100),
        "pricing":values,"negotiation":events,"notes":string("notes",5000),
        "created_at":old["created_at"] if old else now,"updated_at":now}
def save_listing(d,listing_id=None):
    with STORE_LOCK:
        STORE.mkdir(parents=True,exist_ok=True)
        old=None
        if listing_id:
            if not re.fullmatch(r"LST-[A-F0-9]{12}",listing_id):raise ValueError("Identifiant invalide")
            path=STORE/(listing_id+".json")
            if not path.is_file():raise FileNotFoundError("Annonce inconnue")
            old=json.loads(path.read_text(encoding="utf-8"))
        obj=validate(d,old)
        path=STORE/(obj["listing_id"]+".json")
        temporary=STORE/(obj["listing_id"]+"."+uuid4().hex+".tmp")
        try:
            temporary.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
            os.replace(temporary,path)
        finally:
            temporary.unlink(missing_ok=True)
        return obj

class Handler(BaseHTTPRequestHandler):
    def send_json(self,status,obj):
        body=json.dumps(obj,ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Cache-Control","no-store")
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Content-Length",str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def do_POST(self):
        path=urlsplit(self.path).path
        if path!="/api/listings" and not re.fullmatch(r"/api/listings/LST-[A-F0-9]{12}",path):
            return self.send_json(404,{"error":"Route inconnue"})
        if self.headers.get("Origin") not in (None,"http://127.0.0.1:"+str(self.server.server_port),"http://localhost:"+str(self.server.server_port)):
            return self.send_json(403,{"error":"Origine interdite"})
        try:
            size=int(self.headers.get("Content-Length","0"))
            if size<=0 or size>65536: return self.send_json(413,{"error":"Taille invalide"})
            data=json.loads(self.rfile.read(size))
            listing_id=path.split("/")[-1] if path!="/api/listings" else None
            result=save_listing(data,listing_id)
            return self.send_json(200 if listing_id else 201,result)
        except (ValueError,json.JSONDecodeError) as e:return self.send_json(400,{"error":str(e)})
        except FileNotFoundError as e:return self.send_json(404,{"error":str(e)})
        except Exception:return self.send_json(500,{"error":"Erreur de sauvegarde"})

    def do_GET(self):
        path=unquote(urlsplit(self.path).path)
        if path=="/api/listings":
            entries,errors=listings()
            return self.send_json(200,{"listings":entries,"errors":errors})
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

"""Local Hardware Lab configuration accounts, persistence and share tokens.

No external service. SQLite data and token salts stay out of Git.
Authorizations are checked on every read/write; a share token is *read-only*.
"""
from __future__ import annotations
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import threading
import time
import uuid
from http import HTTPStatus
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT=Path(__file__).resolve().parents[1]
PRIVATE=ROOT/".hardware-lab-private"
DB=PRIVATE/"profiles.sqlite3"
SESSION_MAX_AGE=14*24*3600
COOKIE="hwlab_session"
LOCK=threading.RLock()
ATTEMPTS={}
USERNAME=re.compile(r"^[A-Za-z0-9_.-]{3,48}$")
VALID_CATS={"CPU","GPU","Motherboard","RAM","PSU","Cooling","Case","NVMe","SDD","HDD","Extra"}
def init():
    PRIVATE.mkdir(mode=0o700,exist_ok=True)
    try:PRIVATE.chmod(0o700)
    except OSError:pass
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS accounts(
          id TEXT PRIMARY KEY, username TEXT NOT NULL UNIQUE COLLATE NOCASE,
          password_hash TEXT NOT NULL, created_at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions(
          token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL, csrf TEXT NOT NULL,
          expires_at INTEGER NOT NULL, FOREIGN KEY(user_id) REFERENCES accounts(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS configurations(
          id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, title TEXT NOT NULL,
          payload TEXT NOT NULL, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL,
          share_token_hash TEXT UNIQUE, share_expires_at INTEGER,
          FOREIGN KEY(owner_id) REFERENCES accounts(id) ON DELETE CASCADE);
        CREATE INDEX IF NOT EXISTS idx_owner_configs ON configurations(owner_id,updated_at DESC);
        """)
    try:DB.chmod(0o600)
    except OSError:pass
def connect():
    PRIVATE.mkdir(mode=0o700,exist_ok=True)
    db=sqlite3.connect(DB,timeout=12)
    db.row_factory=sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA journal_mode=WAL")
    return db
def stamp():return int(time.time())
def digest(v):return hashlib.sha256(v.encode("utf8")).hexdigest()
def secret():return secrets.token_urlsafe(32)
def password_hash(password):
    salt=secrets.token_bytes(16)
    value=hashlib.scrypt(password.encode(),salt=salt,n=2**15,r=8,p=1,maxmem=64*1024*1024)
    return "scrypt:32768:8:1:"+salt.hex()+":"+value.hex()
def check_password(password,encoded):
    try:
        tag,n,r,p,salt,stored=encoded.split(":")
        if tag!="scrypt":return False
        actual=hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt),n=int(n),r=int(r),p=int(p),maxmem=64*1024*1024)
        return hmac.compare_digest(actual,bytes.fromhex(stored))
    except (ValueError,TypeError):return False
def fail(status,message):return status,{"error":message},None
def session_cookie(handler):
    cookie=SimpleCookie()
    try:cookie.load(handler.headers.get("Cookie",""))
    except Exception:return ""
    return cookie.get(COOKIE).value if cookie.get(COOKIE) else ""
def current(handler):
    token=session_cookie(handler)
    if not token:return None
    with connect() as db:
        row=db.execute("""SELECT a.id,a.username,s.csrf FROM sessions s
            JOIN accounts a ON a.id=s.user_id
            WHERE token_hash=? AND expires_at>?""",(digest(token),stamp())).fetchone()
        return dict(row) if row else None
def cookie_header(token,clear=False,secure=False):
    pieces=[COOKIE+"="+(token if not clear else ""),"Path=/","HttpOnly","SameSite=Strict"]
    if clear:pieces.append("Max-Age=0")
    else:pieces.append("Max-Age="+str(SESSION_MAX_AGE))
    if secure:pieces.append("Secure")
    return "; ".join(pieces)
def read_body(handler):
    try:n=int(handler.headers.get("Content-Length","0"))
    except ValueError:raise ValueError("Longueur invalide")
    if n<2 or n>131072:raise ValueError("Document trop volumineux")
    try:v=json.loads(handler.rfile.read(n))
    except (ValueError,UnicodeDecodeError):raise ValueError("JSON invalide")
    if not isinstance(v,dict):raise ValueError("Objet JSON attendu")
    return v
def validate_config(obj):
    title=str(obj.get("title","")).strip()
    if not 1<=len(title)<=100:raise ValueError("Nom de configuration requis (100 caractères max)")
    items=obj.get("components",[])
    if not isinstance(items,list) or len(items)>64:raise ValueError("Liste de composants invalide")
    cleaned=[]
    for x in items:
        if not isinstance(x,dict):raise ValueError("Ligne de composant invalide")
        component_id=x.get("id");cat=x.get("category");qty=x.get("quantity",1)
        if not isinstance(component_id,str) or len(component_id)>140 or not re.fullmatch(r"[A-Za-z0-9_.-]+",component_id):raise ValueError("ID composant invalide")
        if cat not in VALID_CATS:raise ValueError("Catégorie invalide")
        if not isinstance(qty,int) or isinstance(qty,bool) or qty<1 or qty>16:raise ValueError("Quantité invalide")
        mode=x.get("price_mode","unknown")
        if mode not in ("new","used","owned","custom","unknown"):raise ValueError("Mode de prix invalide")
        value=x.get("price_snapshot")
        if value is not None and (not isinstance(value,(float,int)) or isinstance(value,bool) or value<0 or value>500000):raise ValueError("Montant invalide")
        cleaned.append({"id":component_id,"category":cat,"quantity":qty,"price_mode":mode,"price_snapshot":value})
    # References remain IDs; no arbitrary HTML, private data or component catalog copies.
    return {"title":title,"description":str(obj.get("description",""))[:1500],"purpose":str(obj.get("purpose","custom"))[:60],
            "budget":obj.get("budget") if isinstance(obj.get("budget"),(int,float)) and 0<=obj["budget"]<=1000000 else None,
            "components":cleaned,"schema_version":1}
def serialize(row,with_share=False):
    obj=json.loads(row["payload"]);obj.update({"id":row["id"],"created_at":row["created_at"],"updated_at":row["updated_at"],"shared":bool(row["share_token_hash"])})
    if with_share:obj["share_expires_at"]=row["share_expires_at"]
    return obj
def post(handler):
    path=unquote(urlsplit(handler.path).path)
    if not path.startswith("/api/auth/") and not path.startswith("/api/configurations"):return None
    try:body=read_body(handler)
    except ValueError as exc:return fail(400,str(exc))
    host=handler.headers.get("Host","")
    origin=handler.headers.get("Origin")
    if origin not in (None,"http://"+host,"https://"+host):return fail(403,"Origine refusée")
    ip=handler.client_address[0]
    if path in ("/api/auth/register","/api/auth/login"):
        key=ip+":"+path;now=stamp()
        ATTEMPTS[key]=[x for x in ATTEMPTS.get(key,[]) if now-x<900]
        if len(ATTEMPTS[key])>=12:return fail(429,"Trop de tentatives. Réessayer plus tard.")
        ATTEMPTS[key].append(now)
        username=body.get("username","");password=body.get("password","")
        if not isinstance(username,str) or not USERNAME.fullmatch(username):return fail(400,"Identifiant : 3 à 48 caractères alphanumériques")
        if not isinstance(password,str) or len(password)<12 or len(password)>200:return fail(400,"Mot de passe : 12 à 200 caractères")
        with LOCK,connect() as db:
            if path.endswith("register"):
                try:
                    account=str(uuid.uuid4())
                    db.execute("INSERT INTO accounts VALUES (?,?,?,?)",(account,username,password_hash(password),now))
                except sqlite3.IntegrityError:return fail(409,"Cet identifiant est déjà utilisé")
            else:
                user=db.execute("SELECT * FROM accounts WHERE username=?",(username,)).fetchone()
                if not user or not check_password(password,user["password_hash"]):return fail(401,"Identifiants invalides")
                account=user["id"];username=user["username"]
            token=secret();csrf=secret()
            db.execute("INSERT INTO sessions VALUES (?,?,?,?)",(digest(token),account,csrf,now+SESSION_MAX_AGE))
            db.commit()
        return 200,{"user":{"id":account,"username":username},"csrf":csrf},{"Set-Cookie":cookie_header(token,secure=bool(getattr(handler.server,"is_https",False)))}
    user=current(handler)
    if not user:return fail(401,"Connexion requise")
    if not hmac.compare_digest(str(handler.headers.get("X-CSRF-Token","")),user["csrf"]):return fail(403,"Jeton CSRF invalide")
    if path=="/api/auth/logout":
        with connect() as db:db.execute("DELETE FROM sessions WHERE token_hash=?",(digest(session_cookie(handler)),));db.commit()
        return 200,{"ok":True},{"Set-Cookie":cookie_header("",clear=True)}
    if path=="/api/auth/delete-account":
        if body.get("confirm")!=user["username"]:return fail(400,"Confirmer le nom du compte")
        with connect() as db:db.execute("DELETE FROM accounts WHERE id=?",(user["id"],));db.commit()
        return 200,{"deleted":True},{"Set-Cookie":cookie_header("",clear=True)}
    if path=="/api/configurations":
        try:config=validate_config(body)
        except ValueError as exc:return fail(400,str(exc))
        now=stamp();cid=str(uuid.uuid4())
        with connect() as db:
            db.execute("INSERT INTO configurations(id,owner_id,title,payload,created_at,updated_at) VALUES (?,?,?,?,?,?)",
                       (cid,user["id"],config["title"],json.dumps(config,ensure_ascii=False),now,now))
            db.commit()
        return 201,{"configuration":{**config,"id":cid,"created_at":now,"updated_at":now,"shared":False}},None
    m=re.fullmatch(r"/api/configurations/([a-f0-9-]{36})(?:/(share|duplicate))?",path)
    if not m:return fail(404,"Route inconnue")
    cid,operation=m.groups()
    with LOCK,connect() as db:
        row=db.execute("SELECT * FROM configurations WHERE id=? AND owner_id=?",(cid,user["id"])).fetchone()
        if not row:return fail(404,"Configuration introuvable")
        if operation=="share":
            if body.get("enabled") is False:
                db.execute("UPDATE configurations SET share_token_hash=NULL,share_expires_at=NULL WHERE id=?",(cid,))
                db.commit();return 200,{"shared":False},None
            token=secret();expires=stamp()+30*24*3600
            db.execute("UPDATE configurations SET share_token_hash=?,share_expires_at=? WHERE id=?",(digest(token),expires,cid))
            db.commit()
            return 200,{"shared":True,"token":token,"expires_at":expires,"public_internet":False},None
        if operation=="duplicate":
            now=stamp();newid=str(uuid.uuid4());obj=json.loads(row["payload"]);obj["title"]=obj["title"]+" (copie)"
            db.execute("INSERT INTO configurations(id,owner_id,title,payload,created_at,updated_at) VALUES(?,?,?,?,?,?)",(newid,user["id"],obj["title"],json.dumps(obj,ensure_ascii=False),now,now))
            db.commit();return 201,{"configuration":{**obj,"id":newid,"created_at":now,"updated_at":now,"shared":False}},None
        if body.get("_delete") is True:
            db.execute("DELETE FROM configurations WHERE id=?",(cid,));db.commit();return 200,{"deleted":True},None
        try:config=validate_config(body)
        except ValueError as exc:return fail(400,str(exc))
        db.execute("UPDATE configurations SET title=?,payload=?,updated_at=? WHERE id=?",(config["title"],json.dumps(config,ensure_ascii=False),stamp(),cid))
        db.commit()
        return 200,{"configuration":{**config,"id":cid}},None
def get(handler):
    path=unquote(urlsplit(handler.path).path)
    if path=="/api/auth/me":
        user=current(handler)
        return (200,{"user":{"id":user["id"],"username":user["username"]},"csrf":user["csrf"]},None) if user else fail(401,"Non connecté")
    m=re.fullmatch(r"/api/shared/([A-Za-z0-9_-]{32,128})",path)
    if m:
        with connect() as db:
            row=db.execute("SELECT * FROM configurations WHERE share_token_hash=? AND share_expires_at>?",(digest(m.group(1)),stamp())).fetchone()
        if not row:return fail(404,"Lien révoqué ou expiré")
        return 200,{"configuration":serialize(row),"read_only":True},None
    if path=="/api/configurations":
        user=current(handler)
        if not user:return fail(401,"Connexion requise")
        with connect() as db:rows=db.execute("SELECT * FROM configurations WHERE owner_id=? ORDER BY updated_at DESC LIMIT 300",(user["id"],)).fetchall()
        return 200,{"configurations":[serialize(row,with_share=True) for row in rows]},None
    m=re.fullmatch(r"/api/configurations/([a-f0-9-]{36})",path)
    if m:
        user=current(handler)
        if not user:return fail(401,"Connexion requise")
        with connect() as db:row=db.execute("SELECT * FROM configurations WHERE id=? AND owner_id=?",(m.group(1),user["id"])).fetchone()
        return (200,{"configuration":serialize(row,with_share=True)},None) if row else fail(404,"Configuration introuvable")
    return None

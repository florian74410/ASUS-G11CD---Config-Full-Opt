import io
import os
import sqlite3
import sys
import tempfile
import unittest
import json
import pathlib
from email.message import Message
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"scripts"))
import configurator_store as store

class Fake:
    def __init__(self,path,data=None,cookie="",csrf="",origin="http://127.0.0.1:8765"):
        self.path=path
        self.server=type('Server',(),{'is_https':False})()
        self.client_address=("127.0.0.1",12345)
        self.headers={"Host":"127.0.0.1:8765","Origin":origin}
        if data is not None:
            content=json.dumps(data).encode()
            self.rfile=io.BytesIO(content)
            self.headers["Content-Length"]=str(len(content))
        if cookie:self.headers["Cookie"]=cookie
        if csrf:self.headers["X-CSRF-Token"]=csrf

class StoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.orig=(store.PRIVATE,store.DB,store.ATTEMPTS)
        store.PRIVATE=pathlib.Path(self.tmp.name)
        store.DB=store.PRIVATE/"profiles.sqlite3"
        store.ATTEMPTS={}
        store.init()
    def tearDown(self):
        store.PRIVATE,store.DB,store.ATTEMPTS=self.orig
        self.tmp.cleanup()
    def reg(self,name):
        status,data,headers=store.post(Fake("/api/auth/register",{"username":name,"password":"CorrectHorseBattery99!"}))
        self.assertEqual(status,200)
        return headers["Set-Cookie"].split(";")[0],data["csrf"]
    def conf(self,title="Gaming"):
        return {"title":title,"purpose":"gaming","budget":500,"components":[
          {"id":"AMD_Ryzen_5_1600","category":"CPU","quantity":1,"price_mode":"used","price_snapshot":30},
          {"id":"Intel_GPU","category":"GPU","quantity":1,"price_mode":"unknown","price_snapshot":None}]}
    def test_private_sessions_and_acl(self):
        a,csrf=self.reg("userAlpha");b,csrf_b=self.reg("userBeta")
        status,data,_=store.post(Fake("/api/configurations",self.conf(),a,csrf))
        self.assertEqual(status,201)
        ident=data["configuration"]["id"]
        self.assertEqual(store.get(Fake("/api/configurations",cookie=a))[0],200)
        self.assertEqual(store.get(Fake("/api/configurations/"+ident,cookie=b))[0],404)
        self.assertEqual(store.post(Fake("/api/configurations/"+ident,{"_delete":True},b,csrf_b))[0],404)
        self.assertEqual(store.post(Fake("/api/configurations/"+ident,{"_delete":True},a,"INVALID"))[0],403)
        self.assertEqual(store.post(Fake("/api/configurations/"+ident,{"_delete":True},a,csrf,origin="http://evil.invalid"))[0],403)
    def test_share_token_readonly_and_revoke(self):
        cookie,csrf=self.reg("shareOwner")
        _,created,_=store.post(Fake("/api/configurations",self.conf(),cookie,csrf))
        ident=created["configuration"]["id"]
        code,d,_=store.post(Fake("/api/configurations/"+ident+"/share",{"enabled":True},cookie,csrf))
        self.assertEqual(code,200);token=d["token"]
        self.assertEqual(store.get(Fake("/api/shared/"+token))[0],200)
        self.assertEqual(store.post(Fake("/api/configurations/"+ident,{"title":"Bad"},csrf="bad"))[0],401)
        code,d,_=store.post(Fake("/api/configurations/"+ident+"/share",{"enabled":False},cookie,csrf))
        self.assertEqual(code,200);self.assertFalse(d["shared"])
        self.assertEqual(store.get(Fake("/api/shared/"+token))[0],404)
    def test_persistence_and_duplicate(self):
        cookie,csrf=self.reg("personTest")
        _,created,_=store.post(Fake("/api/configurations",self.conf(),cookie,csrf))
        ident=created["configuration"]["id"]
        store.init() # simulate process restart
        self.assertEqual(store.get(Fake("/api/configurations/"+ident,cookie=cookie))[0],200)
        code,result,_=store.post(Fake("/api/configurations/"+ident+"/duplicate",{},cookie,csrf))
        self.assertEqual(code,201)
        self.assertNotEqual(result["configuration"]["id"],ident)
        self.assertEqual(len(store.get(Fake("/api/configurations",cookie=cookie))[1]["configurations"]),2)
    def test_password_hash_and_fail_closed(self):
        cookie,csrf=self.reg("secureUser")
        with store.connect() as db:
            row=db.execute("SELECT password_hash FROM accounts").fetchone()
        self.assertNotIn("CorrectHorseBattery",row["password_hash"])
        self.assertTrue(row["password_hash"].startswith("scrypt:"))
        self.assertEqual(store.post(Fake("/api/auth/login",{"username":"secureUser","password":"WrongPassword12345!"}))[0],401)
        self.assertEqual(store.post(Fake("/api/auth/register",{"username":"x","password":"short"}))[0],400)
        self.assertEqual(store.post(Fake("/api/configurations",{"title":"Oops","components":[{"id":"../secret","category":"CPU"}]},cookie,csrf))[0],400)
        code,_,extra=store.post(Fake("/api/auth/logout",{},cookie,csrf))
        self.assertEqual(code,200)
        self.assertEqual(store.get(Fake("/api/auth/me",cookie=cookie))[0],401)
    def test_account_delete_cascades(self):
        cookie,csrf=self.reg("deleteOwner")
        store.post(Fake("/api/configurations",self.conf(),cookie,csrf))
        code,_,_=store.post(Fake("/api/auth/delete-account",{"confirm":"deleteOwner"},cookie,csrf))
        self.assertEqual(code,200)
        with store.connect() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM configurations").fetchone()[0],0)
            self.assertEqual(db.execute("SELECT count(*) FROM accounts").fetchone()[0],0)
if __name__=="__main__": unittest.main()

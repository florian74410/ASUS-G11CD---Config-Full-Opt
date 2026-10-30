#!/usr/bin/env python3
"""Export indépendant du catalogue JSON: ne modifie jamais Configuration.xlsx (édition manuelle)."""
import json
import re
from pathlib import Path
from collections import Counter
import xlsxwriter
ROOT=Path(__file__).resolve().parents[1]
CATS=["GPU","CPU","Motherboard","PSU","Case","RAM","SDD","NVMe","HDD","Extra","Cooling"]
OUT=ROOT/"Configuration_Catalogue.xlsx"
def items():
    seen=set(); data=[]
    for cat in CATS:
        for f in sorted((ROOT/"Component"/cat).glob("*.json")):
            d=json.loads(f.read_text(encoding="utf8"))
            if d.get("category")!=cat or not d.get("id"):raise ValueError(str(f)+": catégorie/id invalide")
            if d["id"] in seen:raise ValueError("ID dupliqué: "+d["id"])
            seen.add(d["id"]);data.append((cat,f,d))
    return data
def main():
    data=items()
    wb=xlsxwriter.Workbook(str(OUT))
    wb.set_properties({"title":"Hardware Lab - Catalogue","comments":"Données JSON; tarifs uniquement si justifiés"})
    base=wb.add_format({"bg_color":"#121C30","font_color":"#FFFFFF","bold":True,"bottom":2,"bottom_color":"#F04459"})
    title=wb.add_format({"font_size":20,"bold":True,"font_color":"#F04459"})
    body=wb.add_format({"font_color":"#202A3A"})
    grey=wb.add_format({"bg_color":"#EFF2F7","font_color":"#202A3A"})
    eur=wb.add_format({"num_format":'#,##0.00 "€"'})
    warn=wb.add_format({"font_color":"#C66100"})
    def make(cat,subset,category_col=False):
        ws=wb.add_worksheet(cat);ws.hide_gridlines(2);ws.freeze_panes(1,2)
        cols=["Référence","Label","Format","Cores","Threads","Socket","Capacité","Description technique","Neuf moyen €","Échant. neuf","Occasion moyen €","Échant. occasion","Achat réel €","Livraison €","Statut","Photos","Sources","Fichier JSON"]
        if category_col:cols.insert(0,"Catégorie")
        ws.write_row(0,0,cols,base);ws.set_row(0,32)
        ws.set_column(0,0,37);ws.set_column(1,2,20);ws.set_column(3,6,15);ws.set_column(7,7,90)
        ws.set_column(8,14,18);ws.set_column(15,16,65);ws.set_column(17,17,68)
        if category_col:ws.set_column(0,0,18);ws.set_column(1,1,42)
        for row,(category,p,d) in enumerate(subset,1):
            s=d.get("specifications") or {};pr=d.get("pricing") or {}
            form=s.get("form_factor") or s.get("case_form_factor") or s.get("memory_type") or s.get("pcie_gen") or ""
            cap=s.get("socket") or s.get("capacity_gb") or s.get("vram_gb") or s.get("nominal_w") or ""
            label=d.get("label") or (str(s.get("certification") or "")+" / "+str(s.get("modular") or "") if category=="PSU" else "")
            desc=d.get("technical_description") or d.get("description_technical") or ""
            technologies=d.get("technologies") or []
            if not desc:
                bits=[]
                if category=="CPU":
                    bits=["CPU "+str(s.get("cores","?"))+" cœurs / "+str(s.get("threads","?"))+" threads, socket "+str(s.get("socket","inconnu"))+"."]
                elif category=="GPU":bits=["GPU "+str(s.get("vram_gb","?"))+" Go "+str(s.get("vram_type",""))+", bus "+str(s.get("memory_bus_bits","?"))+" bits."]
                else:bits=[str(d.get("full_name",""))+" — "+str(s.get("form_factor") or s.get("capacity_gb") or "spécifications partielles")]
                desc=" ".join(bits)
            if technologies:desc+=" Technologies documentées : "+", ".join(map(str,technologies))+"."
            nnew=pr.get("new_sample_count",0);nused=pr.get("used_sample_count",0)
            new=pr.get("new_eur");used=pr.get("used_eur")
            if d.get("schema_version")=="1.1":
                new=new if nnew>=10 else None
                used=used if nused>=20 else None
            photo=d.get("asset") or ""
            if not photo:
                folder=ROOT/"Assets"/category
                candidates=[x for x in folder.glob("*") if x.suffix.lower() in (".jpg",".jpeg",".png",".webp") and (d.get("model","").lower().replace(" ","_") in x.stem.lower().replace(" ","_") or d["id"].lower() in x.stem.lower())]
                if candidates:photo=str(sorted(candidates)[0].relative_to(ROOT))
            sources=d.get("sources") or []
            links=[v if isinstance(v,str) else (v.get("url") or "") for v in sources]
            manufacturer_domains={"AMD":["amd.com"],"Intel":["intel.com"],"NVIDIA":["nvidia.com"],"ASUS":["asus.com"],"MSI":["msi.com"],"Gigabyte":["gigabyte.com"],"ASRock":["asrock.com"],"EVGA":["evga.com"],"Corsair":["corsair.com"],"Samsung":["samsung.com"],"Crucial":["crucial.com"],"Kingston":["kingston.com"],"Seasonic":["seasonic.com"],"WD":["westerndigital.com"],"Cooler Master":["coolermaster.com"],"be quiet!":["bequiet.com"]}
            brand=d.get("manufacturer","")
            official=next((v for v in links if v.startswith(("https://","http://")) and any(domain in v.lower().split("/")[2] for domain in manufacturer_domains.get(brand,[]))),"")
            values=[d.get("full_name",""),label,form,s.get("cores"),s.get("threads"),s.get("socket"),s.get("capacity_gb") or s.get("vram_gb") or s.get("nominal_w"),desc,new,nnew,used,nused,pr.get("acquisition_eur"),pr.get("shipping_eur"),d.get("status",""),photo,official,str(p.relative_to(ROOT))]
            if category_col:values.insert(0,category)
            for col,v in enumerate(values):
                if v is None or v=="":continue
                if isinstance(v,(int,float)):
                    ws.write_number(row,col,v,eur if cols[col] in ("Neuf moyen €","Occasion moyen €","Achat réel €","Livraison €") else body)
                elif cols[col] in ("Photos","Sources") and isinstance(v,str):
                    if cols[col]=="Photos" and not v.startswith("http"):
                        path=ROOT/v
                        if path.is_file():
                            ws.write_url(row,col,"external:"+v,body,v)
                        else:ws.write(row,col,v,body)
                    elif v.startswith(("http://","https://")):ws.write_url(row,col,v,body,"Ouvrir "+cols[col].lower())
                    else:ws.write(row,col,v,body)
                else:ws.write(row,col,str(v),grey if row%2==0 else body)
        ws.autofilter(0,0,max(len(subset),1),len(cols)-1)
    dash=wb.add_worksheet("TABLEAU DE BORD")
    dash.hide_gridlines(2);dash.set_column("A:A",38);dash.set_column("B:B",22)
    dash.write("A1","HARDWARE LAB | CATALOGUE",title)
    dash.write_row("A3",["Famille","Références"],base)
    counter=Counter(c for c,_,_ in data)
    for i,c in enumerate(CATS,3):
        dash.write(i,0,c,body);dash.write_number(i,1,counter[c],body)
    dash.write("A17","TOTAL RÉFÉRENCES",base);dash.write_number("B17",len(data),body)
    chart=wb.add_chart({"type":"bar"});chart.add_series({"name":"Références","categories":"='TABLEAU DE BORD'!$A$4:$A$14","values":"='TABLEAU DE BORD'!$B$4:$B$14","fill":{"color":"#E53955"}})
    chart.set_legend({"none":True});chart.set_title({"name":"Répartition du catalogue"});dash.insert_chart("D3",chart)
    make("All",data,True)
    for cat in CATS:make(cat,[x for x in data if x[0]==cat])
    inventory=wb.add_worksheet("INVENTAIRE")
    inventory.write_row(0,0,["Référence","Catégorie","Statut","Prix payé €","Livraison €","Total payé €"],base)
    inventory.set_column("A:A",45);inventory.set_column("B:C",22);inventory.set_column("D:F",22)
    for i,(cat,p,d) in enumerate(data,1):
        pr=d.get("pricing") or {}
        inventory.write(i,0,d["full_name"]);inventory.write(i,1,cat);inventory.write(i,2,d.get("status",""))
        for col,key in ((3,"acquisition_eur"),(4,"shipping_eur")):
            if isinstance(pr.get(key),(int,float)):inventory.write_number(i,col,pr[key],eur)
        inventory.write_formula(i,5,f'=IF(D{i+1}="","",D{i+1}+IF(E{i+1}="",0,E{i+1}))',eur,"")
    inventory.autofilter(0,0,max(len(data),1),5);inventory.freeze_panes(1,0)
    budget=wb.add_worksheet("BUDGET");budget.set_column("A:A",36);budget.set_column("B:B",22)
    budget.write_row("A1",["Budget réel","EUR"],base)
    end=max(2,len(data)+1)
    for row,label,form in [(1,"Acquisitions",f"=SUM(INVENTAIRE!D2:D{end})"),(2,"Frais de port acquis",f'=SUMIF(INVENTAIRE!D2:D{end},">=0",INVENTAIRE!E2:E{end})'),(3,"Total frais inclus","=B2+B3")]:
        budget.write(row,0,label);budget.write_formula(row,1,form,eur)
    guide=wb.add_worksheet("GUIDE");guide.set_column("A:A",46);guide.set_column("B:B",94)
    guide.write_row("A1",["Règle","Explication"],base)
    for i,(a,b) in enumerate([("Source unique","Component/<Catégorie>/*.json"),("Mettre à jour","python3 scripts/export_catalogue.py"),("Prix moyen neuf","Uniquement après vérification de 10 offres, sinon vide"),("Prix moyen occasion","Uniquement après vérification de 20 offres, sinon vide"),("Éditions manuelles","Configuration.xlsx reste conservé ; cet export est régénéré"),("Photos","Chemin Asset présent quand l'image existe et est réutilisable"),("Manquants","Voir CATALOGUE_MANQUANTS.md")],1):guide.write_row(i,0,[a,b])
    wb.close();print(f"{len(data)} références -> {OUT}")
if __name__=="__main__":main()

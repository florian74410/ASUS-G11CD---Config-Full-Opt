#!/usr/bin/env python3
"""Export indépendant du catalogue JSON: ne modifie jamais Configuration.xlsx (édition manuelle)."""
import json
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
        cols=["Référence","Label","Format","Socket / Capacité","Détail technique","Neuf moyen €","Échant. neuf","Occasion moyen €","Échant. occasion","Achat réel €","Livraison €","Statut","Photo / source","Fichier JSON"]
        if category_col:cols.insert(0,"Catégorie")
        ws.write_row(0,0,cols,base);ws.set_row(0,32)
        ws.set_column(0,0,38);ws.set_column(1,1,28);ws.set_column(2,3,23);ws.set_column(4,4,66)
        ws.set_column(5,10,17);ws.set_column(11,11,17);ws.set_column(12,13,68)
        if category_col:ws.set_column(0,0,18);ws.set_column(1,1,40)
        for row,(category,p,d) in enumerate(subset,1):
            s=d.get("specifications") or {};pr=d.get("pricing") or {}
            form=s.get("form_factor") or s.get("case_form_factor") or s.get("memory_type") or s.get("pcie_gen") or ""
            cap=s.get("socket") or s.get("capacity_gb") or s.get("vram_gb") or s.get("nominal_w") or ""
            fields={k:v for k,v in s.items() if v is not None}
            technical=" | ".join(f"{k}: {v}" for k,v in fields.items())
            label=d.get("label") or (s.get("certification","")+" / "+s.get("modular","") if category=="PSU" else "")
            new=pr.get("new_eur");used=pr.get("used_eur")
            # Leave price blank unless offer samples support average / explicit prior entry.
            nnew=pr.get("new_sample_count",0);nused=pr.get("used_sample_count",0)
            new=(new if nnew>=10 else None) if d.get("schema_version")=="1.1" else new
            used=(used if nused>=20 else None) if d.get("schema_version")=="1.1" else used
            values=[d.get("full_name",""),label,form,str(cap),technical,new,nnew,used,nused,pr.get("acquisition_eur"),pr.get("shipping_eur"),d.get("status",""),d.get("asset",""),str(p.relative_to(ROOT))]
            if category_col:values.insert(0,category)
            for col,v in enumerate(values):
                if v is None:continue
                if isinstance(v,(int,float)):ws.write_number(row,col,v,eur if col in ([6,8,10,11] if category_col else [5,7,9,10]) else body)
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

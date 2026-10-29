#!/usr/bin/env python3
"""Regénère Configuration.xlsx depuis Component/<categorie>/*.json.
Usage : python3 scripts/sync_components.py [--output Configuration.xlsx].
Le classeur est un export : les JSON constituent l'unique source des données.
"""
import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
import xlsxwriter

ROOT = Path(__file__).resolve().parents[1]
CATS = ("CPU", "GPU", "Motherboard", "NVMe", "SDD", "PSU", "Extra", "Case", "RAM", "Cooling")
HEADERS = ["Référence", "Fabricant", "Modèle", "Statut", "Neuf €", "Occasion €", "Achat €",
           "Port €", "Total payé €", "Prix cible €", "Compatibilité", "Caractéristiques",
           "Benchmarks", "FPS", "Fichier JSON", "Photo"]
BG, NAVY, RED, LIGHT, MUTED, GREEN = "#0F1421", "#202A3F", "#C9253A", "#EEF2F8", "#65748B", "#188467"

def load():
    records, ids = [], set()
    for category in CATS:
        for path in sorted((ROOT/"Component"/category).glob("*.json")):
            data=json.loads(path.read_text(encoding="utf-8"))
            if data.get("category") != category or not data.get("id") or not data.get("full_name"):
                raise ValueError(f"{path}: catégorie, identifiant ou nom invalide")
            if data["id"] in ids:
                raise ValueError(f"ID dupliqué: {data['id']}")
            ids.add(data["id"])
            price=data.get("pricing") or {}
            for key in ("new_eur","used_eur","acquisition_eur","shipping_eur"):
                value=price.get(key)
                if value is not None and (type(value) not in (int,float) or value<0):
                    raise ValueError(f"{path}: montant invalide {key}")
            records.append((category,path,data))
    return records

def build(output):
    records=load()
    output.parent.mkdir(parents=True,exist_ok=True)
    wb=xlsxwriter.Workbook(str(output))
    wb.set_properties({"title":"ASUS G11CD · Configuration","subject":"Inventaire, comparatifs et budget matériel","comments":"Automatiquement généré depuis les fichiers JSON du dépôt."})
    header=wb.add_format({"bold":1,"bg_color":BG,"font_color":"#FFFFFF","font_size":10,"valign":"vcenter","bottom":2,"bottom_color":RED})
    title=wb.add_format({"bold":1,"bg_color":BG,"font_color":"#FFFFFF","font_size":20,"valign":"vcenter"})
    subtitle=wb.add_format({"font_color":MUTED,"italic":1})
    plain=wb.add_format({"font_color":NAVY,"valign":"vcenter"})
    stripe=wb.add_format({"font_color":NAVY,"bg_color":LIGHT,"valign":"vcenter"})
    eur=wb.add_format({"num_format":'#,##0.00 "€"',"font_color":NAVY})
    eur_stripe=wb.add_format({"num_format":'#,##0.00 "€"',"font_color":NAVY,"bg_color":LIGHT})
    num=wb.add_format({"font_color":NAVY,"align":"center"})
    kpi=wb.add_format({"font_size":18,"bold":1,"font_color":RED,"num_format":'#,##0.00 "€"'})
    badge=wb.add_format({"font_color":GREEN,"bold":1,"bg_color":"#DFF7ED"})
    overall=wb.add_format({"font_color":"#FFFFFF","bold":1,"bg_color":RED,"font_size":12})
    wrap=wb.add_format({"font_color":NAVY,"text_wrap":True,"valign":"top"})

    def start(sheet, columns, width=19):
        sheet.hide_gridlines(2)
        sheet.set_tab_color(RED if sheet.name in ("TABLEAU DE BORD","BUDGET") else NAVY)
        sheet.freeze_panes(1, 1)
        sheet.set_row(0, 30)
        sheet.set_column(0, 0, 42)
        sheet.set_column(1, 3, width)
        sheet.set_column(4, 9, 16)
        sheet.set_column(10, 10, 20)
        sheet.set_column(11, 13, 52)
        sheet.set_column(14, 15, 60)
        sheet.write_row(0,0,columns,header)
        sheet.autofilter(0,0,max(1,len(records)),len(columns)-1)

    def sheet_for(category, entries, all_items=False):
        sh=wb.add_worksheet("INVENTAIRE" if all_items else category)
        cols=(["Catégorie"]+HEADERS) if all_items else HEADERS
        start(sh,cols)
        offset=int(all_items)
        if all_items:
            sh.set_column(0,0,17);sh.set_column(1,1,42)
            sh.set_column(12,14,53)
            sh.set_column(15,16,55)
        for i,(cat,path,d) in enumerate(entries,1):
            p=d.get("pricing") or {}
            perf=d.get("performance") or {}
            values=[d["full_name"], d.get("manufacturer",""),d.get("model",""),d.get("status",""),
                    p.get("new_eur"),p.get("used_eur"),p.get("acquisition_eur"),p.get("shipping_eur"),
                    None,None,(d.get("compatibility") or {}).get("status",""),
                    json.dumps(d.get("specifications") or {},ensure_ascii=False,separators=(", ",": ")),
                    json.dumps(perf.get("benchmarks") or [],ensure_ascii=False),
                    json.dumps(perf.get("gaming_fps") or [],ensure_ascii=False),
                    str(path.relative_to(ROOT)),d.get("asset","")]
            if all_items: values=[cat]+values
            fmt=stripe if i%2==0 else plain
            for j,v in enumerate(values):
                if j in (4+offset,5+offset,6+offset,7+offset) and v is not None:
                    sh.write_number(i,j,v,eur_stripe if i%2==0 else eur)
                elif v is not None: sh.write(i,j,v,fmt)
            # Formulas reference cells; blank acquisitions remain visually blank.
            r=i+1; col=lambda j:xlsxwriter.utility.xl_col_to_name(j+offset)
            paid=f"{col(6)}{r}";ship=f"{col(7)}{r}"
            used=f"{col(5)}{r}";new=f"{col(4)}{r}"
            sh.write_formula(i,8+offset,f'=IF({paid}="","",{paid}+IF({ship}="",0,{ship}))',eur_stripe if i%2==0 else eur,"")
            sh.write_formula(i,9+offset,f'=IF({used}<>"",{used},IF({new}<>"",{new},""))',eur_stripe if i%2==0 else eur,"")
        sh.autofilter(0,0,max(1,len(entries)),len(cols)-1)
        sh.conditional_format(1,3+offset,max(1,len(entries)),3+offset,{"type":"text","criteria":"containing","value":"installed","format":badge})
        return sh

    dashboard=wb.add_worksheet("TABLEAU DE BORD")
    dashboard.hide_gridlines(2)
    dashboard.set_tab_color(RED)
    dashboard.set_column("A:A",31);dashboard.set_column("B:B",22);dashboard.set_column("C:C",15)
    dashboard.set_column("D:D",22);dashboard.set_column("E:E",20);dashboard.set_column("F:L",13)
    dashboard.merge_range("A1:L2","ASUS G11CD  /  CONFIG FULL OPT",title)
    dashboard.write("A4","Inventaire et configuration",header)
    dashboard.write("A5","Références",plain);dashboard.write_number("B5",len(records),num)
    dashboard.write("A6","Composants installés",plain)
    dashboard.write_number("B6",sum(d.get("status")=="installed" for _,_,d in records),num)
    dashboard.write("A7","Références candidates",plain)
    dashboard.write_number("B7",sum(d.get("status")=="candidate" for _,_,d in records),num)
    dashboard.write("A8","Achats chiffrés",plain)
    dashboard.write_number("B8",sum((d.get("pricing") or {}).get("acquisition_eur") is not None for _,_,d in records),num)
    dashboard.write("A10","Sous-total hors port",plain)
    dashboard.write_formula("B10","=BUDGET!B4",kpi)
    dashboard.write("A11","Total avec livraison",plain)
    dashboard.write_formula("B11","=BUDGET!B6",kpi)
    dashboard.write("A14","Catégorie",header);dashboard.write("B14","Références",header)
    counts=Counter(c for c,_,_ in records)
    for i,cat in enumerate(CATS,14):
        dashboard.write(i,0,cat,stripe if i%2==0 else plain)
        dashboard.write_number(i,1,counts[cat],num)
    dashboard.write("A27","Actualisé",plain)
    dashboard.write("B27",datetime.now().strftime("%Y-%m-%d %H:%M"),subtitle)
    dashboard.write("A29","Source : Component/**/*.json",subtitle)
    chart=wb.add_chart({"type":"column"})
    chart.add_series({"name":"Références","categories":"='TABLEAU DE BORD'!$A$15:$A$24",
                      "values":"='TABLEAU DE BORD'!$B$15:$B$24","fill":{"color":RED},"border":{"none":True}})
    chart.set_title({"name":"Références par famille"})
    chart.set_legend({"none":True})
    chart.set_chartarea({"border":{"none":True},"fill":{"color":"#FFFFFF"}})
    chart.set_size({"width":660,"height":330})
    dashboard.insert_chart("D5",chart)

    sheet_for(None,records,all_items=True)
    budget=wb.add_worksheet("BUDGET");budget.hide_gridlines(2);budget.set_tab_color(RED)
    budget.set_column("A:A",40);budget.set_column("B:B",23);budget.set_column("C:D",52)
    budget.write_row("A1",["BUDGET / G11CD","Montant €","Définition","Précision"],header)
    budget.write("A2","Pièces payées sans livraison",plain)
    budget.write("A3","Livraison associée aux achats",plain)
    budget.write("A4","SOUS-TOTAL",overall)
    budget.write("A5","Frais de livraison",plain)
    budget.write("A6","TOTAL AVEC LIVRAISON",overall)
    budget.write("A8","Estimation des références",plain)
    n=max(2,len(records)+1)
    budget.write_formula("B2",f"=SUM(INVENTAIRE!H2:H{n})",eur)
    budget.write_formula("B3",f'=SUMIF(INVENTAIRE!H2:H{n},">=0",INVENTAIRE!I2:I{n})',eur)
    budget.write_formula("B4","=B2",kpi)
    budget.write_formula("B5","=B3",eur)
    budget.write_formula("B6","=B4+B5",kpi)
    budget.write_formula("B8",f"=SUM(INVENTAIRE!K2:K{n})",eur)
    budget.write("C2","Prix acquisition uniquement",subtitle)
    budget.write("C3","Port des pièces dont acquisition renseignée",subtitle)
    budget.write("C8","Occasion si renseignée, sinon neuf",subtitle)
    for cat in CATS: sheet_for(cat,[x for x in records if x[0]==cat])
    help_sh=wb.add_worksheet("GUIDE")
    help_sh.hide_gridlines(2);help_sh.set_column("A:A",35);help_sh.set_column("B:B",93)
    help_sh.write_row("A1",["MODE D'EMPLOI","Aide"],header)
    for i,(a,b) in enumerate([
        ("1 · Ajouter","Créer Component/<Categorie>/<Reference>.json"),
        ("2 · Renseigner","Ajouter full_name, status, specifications, performance, pricing et sources."),
        ("3 · Photo","Mettre Assets/<Categorie>/<Reference>.jpg ou .png, même nom de base."),
        ("4 · Régénérer","python3 scripts/sync_components.py"),
        ("5 · Lire","Ouvrir Configuration.xlsx avec LibreOffice Calc."),
        ("Nouveaux candidats","Prix de marché ≠ prix payé; un candidat n'est pas un achat."),
        ("Mesures vérifiables","Préciser jeu, résolution, preset, pilote, source et date des benchmarks."),
        ("Note","Toute édition manuelle du XLSX est perdue à la prochaine synchronisation.")
    ],1):
        help_sh.write(i,0,a,plain);help_sh.write(i,1,b,wrap)
        help_sh.set_row(i,32)
    wb.close()
    print(f"OK — {len(records)} JSON -> {output}")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=ROOT/"Configuration.xlsx")
    build(parser.parse_args().output)

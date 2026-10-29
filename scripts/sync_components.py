#!/usr/bin/env python3
"""Synchronise JSON de composants vers un classeur Excel. Exécuter à la racine du dépôt."""
import json
from pathlib import Path
from artifact_tool import Workbook, SpreadsheetFile

ROOT=Path(__file__).resolve().parents[1]
CATS=["CPU","GPU","Motherboard","NVMe","SDD","PSU","Extra"]
COLS=["Référence","Catégorie","Statut","Fabricant","Modèle","Neuf €","Occasion €","Acquisition €","Port €","Total €","Meilleur prix €","Compatibilité","Spécifications","Performances","Sources","JSON"]
NAVY="#111827"; RED="#DC2626"; PALE="#F3F4F6"; WHITE="#FFFFFF"
def scan():
    out=[]
    for cat in CATS:
        for path in sorted((ROOT/"Component"/cat).glob("*.json")):
            d=json.loads(path.read_text(encoding="utf-8"))
            if d.get("category") != cat or not d.get("full_name") or not isinstance(d.get("pricing"),dict):
                raise ValueError(f"JSON invalide : {path}")
            p=d["pricing"]
            for k in ("new_eur","used_eur","acquisition_eur","shipping_eur"):
                v=p.get(k)
                if v is not None and (isinstance(v,bool) or not isinstance(v,(int,float)) or v<0): raise ValueError(f"{path}: {k}")
            out.append((path,d))
    return out
def build():
    records=scan(); wb=Workbook.create()
    main=wb.worksheets.add("INVENTAIRE")
    main.get_range("A1:P1").values=[COLS]
    main.get_range("A1:P1").format={"fill":NAVY,"font":{"bold":True,"color":WHITE},"row_height":30}
    main.freeze_panes.freeze_rows(1)
    for col,width in {"A":38,"B":18,"C":18,"D":20,"E":24,"F":15,"G":15,"H":17,"I":13,"J":16,"K":19,"L":20,"M":54,"N":46,"O":40,"P":56}.items():
        main.get_range(f"{col}:{col}").format.column_width=width
    for i,(path,d) in enumerate(records,2):
        p=d["pricing"]
        src=d.get("sources",[])
        row=[d.get("full_name"),d["category"],d.get("status"),d.get("manufacturer"),d.get("model"),p.get("new_eur"),p.get("used_eur"),p.get("acquisition_eur"),p.get("shipping_eur"),None,None,d.get("compatibility",{}).get("status"),json.dumps(d.get("specifications",{}),ensure_ascii=False),json.dumps(d.get("performance",{}),ensure_ascii=False),"; ".join(str(x) for x in src),str(path.relative_to(ROOT))]
        main.get_range(f"A{i}:P{i}").values=[row]
        main.get_range(f"J{i}").formulas=[[f'=IF(H{i}="","",H{i}+IF(I{i}="",0,I{i}))']]
        main.get_range(f"K{i}").formulas=[[f'=IF(G{i}<>"",G{i},IF(F{i}<>"",F{i},""))']]
        if i%2==0: main.get_range(f"A{i}:P{i}").format.fill=PALE
    n=max(len(records)+1,2)
    main.get_range(f"F2:K{n}").set_number_format('#,##0.00 "€"')
    budget=wb.worksheets.add("BUDGET")
    budget.get_range("A1:D1").values=[["ASUS G11CD • BUDGET","Montant €","Lecture","Règle"]]
    budget.get_range("A1:D1").format={"fill":NAVY,"font":{"bold":True,"color":WHITE},"row_height":32}
    data=[["Acquisitions hors livraison",None,"Dépense réelle","Somme des achats confirmés"],["Livraisons",None,"Transport","Sur les composants avec acquisition"],["TOTAL AVEC LIVRAISON",None,"Dépense totale","Achats + transport"],["Références en base",len(records),"Inventaire","Tous statuts confondus"],["Pièces acquises",None,"Suivi","Acquisition renseignée"],["Sélection indicative",None,"Estimation","Occasion si renseignée, sinon neuf"]]
    budget.get_range("A2:D7").values=data
    budget.get_range("B2").formulas=[[f'=SUM(INVENTAIRE!H2:H{n})']]
    budget.get_range("B3").formulas=[[f'=SUMIF(INVENTAIRE!H2:H{n},">=0",INVENTAIRE!I2:I{n})']]
    budget.get_range("B4").formulas=[["=B2+B3"]]
    budget.get_range("B6").formulas=[[f'=COUNT(INVENTAIRE!H2:H{n})']]
    budget.get_range("B7").formulas=[[f'=SUM(INVENTAIRE!K2:K{n})']]
    budget.get_range("A4:D4").format={"fill":"#FEE2E2","font":{"bold":True,"color":RED}}
    for col,width in {"A":38,"B":21,"C":28,"D":49}.items(): budget.get_range(f"{col}:{col}").format.column_width=width
    budget.get_range("B2:B4").set_number_format('#,##0.00 "€"')
    budget.get_range("B7").set_number_format('#,##0.00 "€"')
    guide=wb.worksheets.add("MODE D'EMPLOI")
    tips=[["G11CD • GUIDE DE LECTURE",""],["1. Ajouter un JSON dans Component/<Type>/","Une référence = un fichier"],["2. Vérifier la compatibilité et les sources","Une mesure sans protocole = non comparable"],["3. Ajouter une photo dans Assets/<Type>/","Nom de base identique au JSON"],["4. Exécuter python3 scripts/sync_components.py","Le classeur est régénéré"],["5. Consulter INVENTAIRE et BUDGET","Prix manquant ≠ prix nul"],["Statut candidat vs installé","Ne pas compter un prix observé comme dépense"]]
    guide.get_range("A1:B7").values=tips
    guide.get_range("A1:B1").format={"fill":NAVY,"font":{"bold":True,"color":WHITE}}
    guide.get_range("A:A").format.column_width=64;guide.get_range("B:B").format.column_width=65
    for cat in CATS:
        sh=wb.worksheets.add(cat)
        sh.get_range("A1:J1").values=[COLS[:10]]
        sh.get_range("A1:J1").format={"fill":NAVY,"font":{"bold":True,"color":WHITE}}
        sh.get_range("A:A").format.column_width=40
        sh.get_range("B:J").format.column_width=20
        sh.freeze_panes.freeze_rows(1)
        subset=[(i,d) for i,(_,d) in enumerate(records,2) if d["category"]==cat]
        for j,(i,d) in enumerate(subset,2):
            for col,k in [("A","A"),("B","B"),("C","C"),("D","D"),("E","E"),("F","F"),("G","G"),("H","H"),("I","I"),("J","J")]:
                sh.get_range(f"{col}{j}").formulas=[[f"=INVENTAIRE!{k}{i}"]]
    target=ROOT/"Tableur.xlsx"
    SpreadsheetFile.export_xlsx(wb).save(str(target))
    print(f"OK : {len(records)} composants → {target}")
if __name__=="__main__": build()

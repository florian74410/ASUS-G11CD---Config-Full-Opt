#!/usr/bin/env python3
"""G11CD - convertit les composants JSON en Configuration.xlsx.
Source unique: Component/<Categorie>/*.json. N'utilise jamais les lignes du XLSX comme source.
"""
import argparse
import json
from collections import Counter
from pathlib import Path
from artifact_tool import Workbook, SpreadsheetFile

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = ["CPU","GPU","Motherboard","NVMe","SDD","PSU","Extra","Case","RAM","Cooling"]
HEAD = ["Référence", "Marque", "Modèle", "État", "Prix neuf €", "Occasion €",
        "Payé €", "Livraison €", "Total payé €", "Candidat €",
        "Compatibilité", "Caractéristiques", "Benchmarks", "FPS", "Source JSON", "Photo"]
NAVY, RED, LIGHT, WHITE = "#151A25", "#C92C32", "#F0F3F7", "#FFFFFF"
GREEN = "#147D64"

def read_items():
    items = []
    ids = set()
    for cat in CATEGORIES:
        for path in sorted((ROOT / "Component" / cat).glob("*.json")):
            d = json.loads(path.read_text(encoding="utf-8"))
            if d.get("category") != cat or not d.get("full_name") or not d.get("id"):
                raise ValueError(f"Identification invalide dans {path}")
            if d["id"] in ids:
                raise ValueError(f"Identifiant en doublon : {d['id']}")
            ids.add(d["id"])
            p = d.get("pricing", {})
            for field in ("new_eur", "used_eur", "acquisition_eur", "shipping_eur"):
                v = p.get(field)
                if v is not None and (type(v) not in (int, float) or v < 0):
                    raise ValueError(f"{path}: {field} invalide")
            items.append((cat, path, d))
    return items

def style(sheet, last_col="P"):
    sheet.get_range(f"A1:{last_col}1").format = {
        "fill": NAVY, "font": {"bold": True, "color": WHITE}, "row_height": 34
    }
    sheet.freeze_panes.freeze_rows(1)
    sheet.get_range("A:A").format.column_width = 44
    sheet.get_range("B:C").format.column_width = 24
    sheet.get_range("D:D").format.column_width = 17
    sheet.get_range("E:J").format.column_width = 18
    sheet.get_range("K:K").format.column_width = 21
    sheet.get_range("L:N").format.column_width = 47
    sheet.get_range("O:P").format.column_width = 62

def add_table(wb, name, entries, include_category=False):
    sh = wb.worksheets.add(name)
    header = (["Catégorie"] + HEAD) if include_category else HEAD
    end_col = "Q" if include_category else "P"
    sh.get_range(f"A1:{end_col}1").values = [header]
    style(sh, end_col)
    if include_category:
        sh.get_range("A:A").format.column_width=18
        sh.get_range("B:B").format.column_width=45
    for i, (cat, path, d) in enumerate(entries, 2):
        p = d.get("pricing", {})
        perf = d.get("performance") or {}
        b = perf.get("benchmarks") or []
        fps = perf.get("gaming_fps") or []
        row = [
            d["full_name"], d.get("manufacturer"), d.get("model"),
            d.get("status"), p.get("new_eur"), p.get("used_eur"),
            p.get("acquisition_eur"), p.get("shipping_eur"), None, None,
            (d.get("compatibility") or {}).get("status"),
            json.dumps(d.get("specifications", {}), ensure_ascii=False),
            json.dumps(b, ensure_ascii=False),
            json.dumps(fps, ensure_ascii=False),
            str(path.relative_to(ROOT)), d.get("asset") or ""
        ]
        sh.get_range_by_indexes(i-1, 0, 1, len(header)).values = [
            ([cat] + row) if include_category else row
        ]
        off = 1 if include_category else 0
        acq, ship, total, used, new, candidate = [chr(ord(c)+off) for c in ("G","H","I","F","E","J")]
        sh.get_range(f"{total}{i}").formulas = [[f'=IF({acq}{i}="","",{acq}{i}+IF({ship}{i}="",0,{ship}{i}))']]
        sh.get_range(f"{candidate}{i}").formulas = [[f'=IF({used}{i}<>"",{used}{i},IF({new}{i}<>"",{new}{i},""))']]
        if i % 2 == 0:
            sh.get_range_by_indexes(i-1, 0, 1, len(header)).format.fill = LIGHT
    if entries:
        n = len(entries)+1
        left, right = ("F","K") if include_category else ("E","J")
        sh.get_range(f"{left}2:{right}{n}").set_number_format('#,##0.00 "€"')
    return sh

def build(output):
    entries = read_items()
    wb = Workbook.create()
    board = wb.worksheets.add("TABLEAU DE BORD")
    board.get_range("A1:D1").values = [["G11CD • CONTROL CENTER", "Valeur", "Détail", "Lecture"]]
    board.get_range("A1:D1").format = {
        "fill": NAVY, "font": {"color": WHITE, "bold": True}, "row_height": 40
    }
    board.get_range("A:A").format.column_width=39
    board.get_range("B:B").format.column_width=20
    board.get_range("C:D").format.column_width=52
    counts = Counter(c for c, _, _ in entries)
    installed = sum(d.get("status") == "installed" for _, _, d in entries)
    bought = sum(d.get("pricing", {}).get("acquisition_eur") is not None for _, _, d in entries)
    board.get_range("A2:D6").values = [
        ["Références recensées", len(entries), "Toutes catégories", "Chaque référence = un JSON"],
        ["Composants installés", installed, "Statut installed", "Montés ou déclarés présents"],
        ["Achats chiffrés", bought, "Acquisition connue", "Sans estimation du stock ancien"],
        ["Coût constaté hors port", None, "Seulement prix payés", "Pas les prix observés"],
        ["Coût avec livraison", None, "Dépense connue", "Hors données manquantes"],
    ]
    for i,cat in enumerate(CATEGORIES,9):
        board.get_range(f"A{i}:C{i}").values=[[cat, counts[cat], "références"]]
        if i%2==0: board.get_range(f"A{i}:D{i}").format.fill=LIGHT
    board.get_range("B5").formulas=[["=BUDGET!B2"]]
    board.get_range("B6").formulas=[["=BUDGET!B4"]]
    board.get_range("B5:B6").set_number_format('#,##0.00 "€"')
    add_table(wb, "INVENTAIRE", entries, include_category=True)
    budget = wb.worksheets.add("BUDGET")
    budget.get_range("A1:D1").values = [["G11CD • BUDGET", "Montant €", "Définition", "Note"]]
    budget.get_range("A1:D1").format={"fill":NAVY,"font":{"color":WHITE,"bold":True},"row_height":35}
    budget.get_range("A:A").format.column_width=39
    budget.get_range("B:B").format.column_width=21
    budget.get_range("C:D").format.column_width=53
    budget.get_range("A2:D7").values = [
        ["SOUS-TOTAL SANS LIVRAISON", None, "Acquisitions enregistrées", "N'inclut pas les pièces sans prix d'achat"],
        ["Livraison des pièces acquises", None, "Port sur achats connus", "Les ports sur candidats ne comptent pas"],
        ["TOTAL AVEC LIVRAISON", None, "Sous-total + livraison", "Dépense effective connue"],
        ["Composants référencés", len(entries), "Nombre total de JSON", ""],
        ["Composants achetés et chiffrés", bought, "Acquisitions dont prix connu", ""],
        ["Estimation alternatives", None, "Occasion sinon neuf", "Tous candidats avec prix connu"],
    ]
    row_end = max(len(entries)+1,2)
    budget.get_range("B2").formulas=[[f"=SUM(INVENTAIRE!H2:H{row_end})"]]
    budget.get_range("B3").formulas=[[f'=SUMIF(INVENTAIRE!H2:H{row_end},">=0",INVENTAIRE!I2:I{row_end})']]
    budget.get_range("B4").formulas=[["=B2+B3"]]
    budget.get_range("B7").formulas=[[f"=SUM(INVENTAIRE!K2:K{row_end})"]]
    budget.get_range("A4:D4").format={"fill":"#FFE6E7","font":{"bold":True,"color":RED}}
    budget.get_range("B2:B4").set_number_format('#,##0.00 "€"')
    budget.get_range("B7").set_number_format('#,##0.00 "€"')
    for cat in CATEGORIES:
        add_table(wb, cat, [item for item in entries if item[0]==cat])
    guide=wb.worksheets.add("GUIDE")
    guide.get_range("A1:B1").values=[["G11CD • GUIDE", "Fonctionnement"]]
    guide.get_range("A1:B1").format={"fill":NAVY,"font":{"bold":True,"color":WHITE}}
    guide.get_range("A:A").format.column_width=52
    guide.get_range("B:B").format.column_width=105
    guide.get_range("A2:B8").values=[
        ["Source unique","Component/<Categorie>/<Reference>.json"],
        ["Mise à jour","python3 scripts/sync_components.py"],
        ["Classeur","Configuration.xlsx, lecture seule; ne pas saisir dans les feuilles générées"],
        ["Prix neuf / occasion","Prix observés; jamais confondus avec dépenses"],
        ["Prix acquis","Seulement prix réellement payés"],
        ["Statuts","candidate, shortlisted, purchased, installed, rejected"],
        ["Photos","Assets/<Categorie>/<Reference>.<extension>, nom identique au JSON"]
    ]
    output.parent.mkdir(parents=True,exist_ok=True)
    SpreadsheetFile.export_xlsx(wb).save(str(output))
    print(f"OK: {len(entries)} composants, {len(CATEGORIES)} familles -> {output}")
if __name__ == "__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,default=ROOT/"Configuration.xlsx")
    args=ap.parse_args()
    build(args.output)

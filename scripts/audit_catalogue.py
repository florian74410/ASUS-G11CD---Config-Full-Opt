#!/usr/bin/env python3
"""Audit all Component JSONs. Never invent missing specifications, photos or benchmarks."""
import json, csv
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
COMP=ROOT/"Component"
REQUIRED={
"CPU":["cores","threads","socket","architecture","base_ghz","boost_ghz","tdp_w","memory_type","pcie_gen"],
"GPU":["vram_gb","vram_type","memory_bus_bits","architecture","tgp_w"],
"Motherboard":["form_factor","socket","chipset","memory_type","pcie_generation_exact","memory_slots","m2_slots"],
"RAM":["memory_type","speed_mts","cas_latency_cycles","kit_capacity_gb","modules"],
"PSU":["nominal_w","certification","modular"],
"NVMe":["capacity_gb","pcie_gen","sequential_read_mbs","sequential_write_mbs"],
"SDD":["capacity_gb","interface","sequential_read_mbs","sequential_write_mbs"],
"HDD":["capacity_gb","rpm","interface","form_factor_inches"],
"Case":["case_form_factor","supported_form_factors"],
}
def audit():
    output=[]; counts=Counter()
    for path in sorted(COMP.glob("*/*.json")):
        try: d=json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            output.append({"category":path.parent.name,"id":path.stem,"name":path.stem,"status":"invalid_json","specs":"invalid JSON: "+str(e),"photos":"missing","description":"missing","benchmarks":"missing","sources":"missing"})
            continue
        category=d.get("category",path.parent.name)
        specs=d.get("specifications") or {}
        missing=[x for x in REQUIRED.get(category,[]) if specs.get(x) in (None,"",[])]
        raw_images=d.get("images") or []
        folder=ROOT/"Assets"/category
        local=[p for p in folder.glob("*") if p.suffix.lower() in (".png",".jpg",".jpeg",".webp") and (d.get("id","").lower().replace("_","") in p.stem.lower().replace("_","").replace(" ","") or d.get("model","").lower().replace(" ","") in p.stem.lower().replace(" ",""))] if folder.is_dir() else []
        # External photo URLs are references, not downloaded originals.
        ext=len([i for i in raw_images if isinstance(i,dict) and str(i.get("url","")).startswith("https://")])
        numphotos=len(local)+ext
        description=bool((d.get("technical_description") or d.get("description_technical") or "").strip())
        benchmarks=d.get("performance",{}).get("benchmarks",[])
        measured=len([v for v in benchmarks if isinstance(v,dict) and v.get("source") and v.get("score") is not None])
        sources=len(d.get("sources") or [])
        status="ready" if not missing and numphotos>=3 and description and measured and sources else "incomplete"
        counts[status]+=1
        output.append({"category":category,"id":d.get("id",path.stem),"name":d.get("full_name",""),"status":status,
            "specs":", ".join(missing) or "ok","photos":str(numphotos)+"/3 min ("+str(len(local))+" local, "+str(ext)+" external)",
            "description":"ok" if description else "missing","benchmarks":str(measured)+" sourced","sources":str(sources),
            "file":str(path.relative_to(ROOT))})
    return output,counts
def main():
    rows,counts=audit()
    out=ROOT/"CATALOGUE_AUDIT.csv"
    with out.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    report=["# Audit de la base composants","",
      "**Total de références : "+str(len(rows))+"**. Fiches prêtes selon les critères : **"+str(counts["ready"])+"**. Incomplètes : **"+str(counts["incomplete"])+"**.",
      "","Critères : caractéristiques minimales propres à la famille, description technique validée, 3 photos du bon modèle, au moins un benchmark sourcé, sources documentées.",
      "Les images externes ne sont pas des fichiers archivés. Une donnée absente reste absente.","",
      "## Procédure obligatoire pour chaque nouvelle référence",
      "1. JSON individuel avec ID unique, fabricant, référence/SKU et caractéristiques vérifiables.",
      "2. 3 à 5 photos du modèle et de ses variantes exactes si disponibles, liens et droits consignés dans Assets/Brut et Assets/.",
      "3. Prévisualisation et galerie, sans remplacer des vues manquantes par des photos d'un autre modèle.",
      "4. Description technique en français : technologies, possibilités, contraintes et compatibilité.",
      "5. Benchmarks réels sourcés : protocole, version, conditions, date, métrique et unité.",
      "6. Prix : moyennes seulement après 10 annonces neuves et 20 occasion comparables.",
      "7. Audit puis exécution de scripts/export_catalogue.py ; vérifier Configuration_Catalogue.xlsx.",
      "8. Validation et commit sur la branche de travail ; ne pas modifier main sans accord.","",
      "## Détail de toutes les références","",
      "Voir `CATALOGUE_AUDIT.csv` (une ligne par JSON)."]
    (ROOT/"CATALOGUE_AUDIT.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print(f"{len(rows)} JSON, {counts['ready']} ready, {counts['incomplete']} incomplete")
if __name__=="__main__": main()

# DOCUMENTATION · Référentiel G11CD

## Organisation

- `Component/CPU|GPU|Motherboard|NVMe|SDD|PSU|Extra/` : un fichier JSON par référence.
- `Assets/<categorie>/` : photo sous le même nom de base que son JSON (ex. `ASUS_Dual_RTX_3060_Ti.json` ↔ `ASUS_Dual_RTX_3060_Ti.jpg`).
- `schemas/` : structure commune et champs techniques par famille.
- `Tableur.xlsx` : registre et comparaison, régénéré via script.

## Nommage

Utiliser nom complet, caractères ASCII, underscores; conserver la même casse JSON/image. Exemple `AMD_Ryzen_7_1700X.json` et `AMD_Ryzen_7_1700X.jpg`.

## Champs et traçabilité

`category`, `manufacturer`, `model`, `full_name`, `status`, `specifications`, `performance`, `pricing`, `compatibility`, `sources`, `asset`.
Prix en EUR. `null` = non renseigné, **jamais** zéro. Statut : `candidate`, `shortlisted`, `purchased`, `installed`, `rejected`.

Chaque benchmark : `metric`, `value`, `unit`, `test`, `resolution`, `settings`, `source_url`, `measured_at`. Chaque FPS : jeu, version, résolution, preset, RT/FSR/DLSS, CPU, driver, FPS moyen, 1% low, consommation et source si disponibles. Ne pas comparer des mesures réalisées dans des conditions différentes sans avertissement.

## Compatibilité

Vérifier physiquement longueurs GPU, emplacement PSU, hauteur, largeur du radiateur, connecteurs, BIOS et enveloppe de puissance. Status `unverified` tant qu'aucune mesure n'est documentée.

## Import

Exécuter `python3 scripts/sync_components.py` après chaque ajout JSON, puis versionner le classeur mis à jour. Le script valide les JSON, produit les feuilles synthétiques et conserve des références aux sources.

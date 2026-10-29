# Référentiel composants — G11CD

## Modèle de données

Un JSON par référence dans `Component/<Catégorie>/`. Les champs détaillés incluent `specifications`, `performance.benchmarks`, `performance.gaming_fps`, `performance.measurements`, `pricing`, `compatibility`, `sources`, `asset`. Enregistrement de valeurs mesurées accompagné de la source, du contexte de test, de l'unité et de la date. Champ non vérifié : `null`.

`status` : `candidate` (envisagé), `shortlisted` (retenu pour comparaison), `purchased` (acheté), `installed` (installé), `rejected` (écarté).

`pricing` : `new_eur` et `used_eur` sont des prix de marché; `acquisition_eur` et `shipping_eur` désignent la dépense réelle, sans supposer de prix pour le stock d'origine.

Les images portent le même nom de base que le JSON. Ne placer des photographies que lorsque le droit de réutilisation est établi, avec provenance documentée.

## Import et synchronisation

Exécuter `python3 scripts/sync_components.py` à la racine; il parcourt les JSON, contrôle les catégories, refuse les identifiants dupliqués et valide les montants. Il réécrit `Configuration.xlsx` : pas de duplication, suppression d'une référence prise en compte. Le fichier Excel ne doit pas être ouvert pendant sa régénération sur Linux pour éviter les conflits.

## Contrôles avant montage

Contrôler BIOS et référence réelle de la carte mère, enveloppe PSU, connecteurs PCIe et dimensions intérieures GPU et radiateur. Les mesures de FPS doivent préciser résolution, preset, jeu, RT/upscaling, CPU et pilote. Les données provisoires de l'inventaire sont explicitement signalées.

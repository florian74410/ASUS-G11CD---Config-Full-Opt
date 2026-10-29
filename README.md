# ASUS G11CD — Full Opt 🛠️

Inventaire et comparaison de composants pour le projet ASUS G11CD.

**Le seul fichier à ouvrir : [Configuration.xlsx](Configuration.xlsx)** (généré automatiquement).

**Source de vérité :** fichiers `Component/<Famille>/<Nom_complet>.json`, une référence par JSON. Les photos correspondantes utilisent `Assets/<Famille>/<Nom_complet>.jpg` ou `.png`.

### Mettre à jour le tableur (Linux Mint)
```bash
python3 -m pip install -r requirements.txt
python3 scripts/sync_components.py
libreoffice --calc Configuration.xlsx
```

Ne pas modifier le classeur pour saisir des composants : le prochain lancement le régénère entièrement. Modifier plutôt les JSON.

Feuilles : TABLEAU DE BORD, INVENTAIRE, BUDGET, CPU, GPU, Motherboard, NVMe, SDD, PSU, Extra, Case, RAM, Cooling et GUIDE.

Voir [DOCUMENTATION.md](DOCUMENTATION.md) et [ROADMAD.md](ROADMAD.md).

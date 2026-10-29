# ASUS G11CD — CONFIG FULL OPT 🔧

Base de données matérielle locale : **un JSON par référence, un tableau de bord unique**.

## 🖥️ Dashboard Web local (recommandé)

Sous Linux Mint, après `git clone` ou `git pull` :

```bash
python3 scripts/serve.py
```

Ouvrir **http://127.0.0.1:8765** dans Firefox. Pour arrêter : `Ctrl+C`.

- Tableau de bord : compteurs, budget et répartition par catégorie
- Inventaire : tous les composants, recherche et filtres
- Budget : acquisitions réelles et frais de livraison, sans confondre avec les offres
- Une page par catégorie : CPU, GPU, Motherboard, NVMe, SDD, PSU, Extra, Case, RAM, Cooling
- Clic sur un composant : caractéristiques, benchmarks, FPS, sources, prix et compatibilité
- **Actualiser les JSON** : recharge toutes les fiches immédiatement, sans refaire le classeur
- Toute photo dans `Assets/<Categorie>/<Nom_du_JSON>.jpg` ou `.png` s'affiche automatiquement

Le serveur n'écoute que sur **127.0.0.1** par défaut. L'interface n'envoie aucune donnée à un service tiers.

## 📊 Export Excel facultatif

`Configuration.xlsx` est régénéré à chaque ajout/changement de JSON par GitHub Actions ou localement :

```bash
python3 -m pip install -r requirements.txt
python3 scripts/sync_components.py
libreoffice --calc Configuration.xlsx
```

**Les JSON de `Component/` sont la seule source de vérité.** Les modifications manuelles du classeur seront écrasées lors de sa régénération.

Documentation : [DOCUMENTATION.md](DOCUMENTATION.md) · [Budget](BUDGET.md) · [Roadmap](ROADMAD.md).

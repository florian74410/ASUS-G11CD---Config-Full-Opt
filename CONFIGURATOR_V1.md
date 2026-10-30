# Hardware Lab · Configurateur PC V1.0 DEV

## Déploiement et périmètre

Branche : `feature/configurator-v1`, basée sur `feature/marketplace-manual-v1`.

Lancer depuis la racine du dépôt :

```bash
python3 scripts/serve.py
```

Puis ouvrir [http://127.0.0.1:8765/?page=configurator](http://127.0.0.1:8765/?page=configurator).

**Aucune dépendance Python supplémentaire** : le backend utilise `http.server`, `sqlite3`, `hashlib.scrypt`, les sessions sécurisées et les fichiers JSON locaux. Le serveur reste limité à `127.0.0.1` par défaut.

## Fonctionnalités implémentées

- Boutons **Configurateur PC**, **Mes configurations**, **Mon profil** dans la barre latérale du Hardware Lab.
- Choix par catégorie et recherche parmi les références `Component/<Catégorie>/*.json`. Le catalogue n'est pas dupliqué.
- Sélection CPU / carte mère / GPU / RAM / refroidissement / boîtier / alimentation / stockage.
- Fiches de sélection avec photo principale, premières données techniques et prix d'occasion disponible.
- Prix neuf, occasion, déjà possédé, prix personnel ou inconnu ; état inconnu jamais remplacé par 0 €. Instantané du prix choisi enregistré dans chaque ligne.
- Quantités de 1 à 16 pour chaque référence, support de plusieurs disques et modules RAM.
- Estimation de compatibilité **partielle et conservatrice** : sockets CPU/MB, DDR RAM/MB, encombrement GPU, budget watt PSU et montage cooler lorsque les champs sont disponibles.
- **COMPATIBLE / INCOMPATIBLE / WARNING / UNKNOWN / NOT_CHECKED** ; les champs non documentés ne sont pas présentés comme compatibles.
- Export **et import JSON portable**, sans connexion nécessaire.
- Création de profils locaux, connexion, déconnexion, suppression de compte et effacement en cascade des sauvegardes.
- Sauvegarde persistante en SQLite ; configuration rechargée depuis **Mes configurations** ; duplication, modification, suppression.
- Partage par jeton aléatoire révocable et expirant après 30 jours ; accès en lecture seule par l'endpoint `/api/shared/<token>`.
- Icônes vectorielles locales : `web/assets/icons.svg`, avec crédits `web/assets/ICONS_LICENSE.md`.

## Sécurité

Les données personnelles des profils se trouvent dans `.hardware-lab-private/profiles.sqlite3` (répertoire mode 0700 et fichier 0600 quand l'OS le permet). Ce répertoire est dans `.gitignore`.

Les mots de passe sont dérivés par `scrypt` avec sel aléatoire (n=32768, r=8, p=1). Le serveur stocke uniquement les condensats SHA-256 des cookies de session et des jetons de partage ; les cookies sont `HttpOnly`, `SameSite=Strict`, et incluent `Secure` lorsqu'un serveur HTTPS est déclaré.

Les requêtes mutantes authentifiées vérifient l'origine et le jeton CSRF. Chaque lecture/modification de configuration est filtrée par `owner_id` côté SQLite ; aucune configuration d'autrui n'est rendue par l'API authentifiée. Les liens de partage ne donnent accès qu'à une vue read-only.

**Il ne s'agit pas d'un service d'authentification Internet prêt pour la production.** Avant une exposition publique : configuration HTTPS avec vrai reverse proxy, cookies Secure obligatoires, protections anti-abus persistantes, processus d'inscription et récupération de compte, chiffrement/sauvegarde des données privées, revue sécurité, observabilité et vérification indépendante.

### Limitation du partage

Un lien `http://127.0.0.1:8765/?share=...` ne fonctionne **que sur le serveur local**. Il ne permet pas à des personnes à distance de consulter la configuration. Exporter le JSON pour échanger hors du poste, ou attendre un hébergement HTTPS approprié.

## JSON de configuration

```json
{
  "schema_version": 1,
  "title": "Mon PC Gaming",
  "purpose": "gaming",
  "budget": 500,
  "description": "",
  "components": [
    {"id":"AMD_Ryzen_5_1600","category":"CPU","quantity":1,"price_mode":"used","price_snapshot":30}
  ]
}
```

Le configurateur conserve les IDs même si la référence est ultérieurement absente : la fiche affiche alors cette référence comme indisponible.

## Tests

```bash
python3 -m py_compile scripts/configurator_store.py scripts/serve.py
node --check web/configurator.js
node --check web/app.js
python3 -m unittest discover -s tests -p 'test_configurator_store.py' -v
```

GitHub Actions : `.github/workflows/configurator-v1.yml`.

## Fonctionnalités reportées avant lancement public

- Vérification BIOS / firmware par modèle exact et révision.
- Simulation mécanique précise de tous les dégagements (AIO/radiateur, mémoire, GPU/câbles).
- Connecteurs PCIe / EPS / adaptateurs et partage des lanes M.2/SATA lorsque les JSON ne contiennent pas ces données.
- Publication Internet et URL mondiale.
- Réinitialisation de mot de passe par courriel.
- Collaboration multi-utilisateurs en écriture.
- Synchronisation de prix marchands en temps réel.
- Rapport PDF dédié (l'export JSON est opérationnel).

Ces fonctions ne doivent pas être annoncées comme terminées : les JSON sont actuellement partiels sur beaucoup de références.

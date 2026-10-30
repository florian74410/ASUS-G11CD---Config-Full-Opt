# Assets/Brut — originaux non retouchés

Zone de conservation des photographies **originales**, téléchargées avec leur résolution native lorsqu'une licence autorise l'hébergement dans le dépôt.

- `Assets/Brut/<Catégorie>/` : originaux, jamais redimensionnés ni écrasés volontairement.
- `Assets/<Catégorie>/` : miniatures ou images optimisées utilisées par l'application.
- `ASSET_IMPORT_REPORT.json` : source et licence lorsque connues.
- Ne jamais qualifier les miniatures déjà présentes d'« originaux ».
- Les fichiers déjà importés ne sont pas rétroactivement restaurés sans téléchargement de la source originale.
- Les photos sans droits de redistribution documentés ne doivent pas être publiées.

L'importeur Wikimedia produit les deux versions sur ses **prochains imports**. Si le téléchargement de l'original échoue (taille, réseau, droits), la version optimisée reste accompagnée d'une erreur explicite dans le rapport.

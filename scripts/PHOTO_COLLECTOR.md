# Photo Collector V2

Commande : `python3 scripts/photo_collector.py`

Le collecteur parcourt **tous les fichiers `Component/<Catégorie>/*.json`**. Il récupère les images externes déjà renseignées, recherche des photographies correspondant à la référence exacte sur Wikimedia Commons, élimine les doublons binaires et tente d'obtenir **jusqu'à cinq photos locales par composant**. Il reprend au prochain lancement sans re-télécharger les fichiers déjà présents.

- `python3 scripts/photo_collector.py --limit 10` : tester sur les dix premiers JSON.
- `python3 scripts/photo_collector.py --max-photos 3` : limiter à trois images.
- `python3 scripts/photo_collector.py --refresh` : reconsulter Wikimedia Commons.

**Sources et droits.** Les fichiers sous licence libre vérifiée sont sauvegardés dans `Assets/Brut/<Catégorie>/` puis dans `Assets/<Catégorie>/` pour la galerie. Les images déjà référencées provenant de magasins ou autres hébergeurs, lorsque les droits ne sont pas attestés, sont enregistrées localement uniquement dans `Assets/Brut/LocalPreview/<Catégorie>/` (ignoré par Git). Elles peuvent être vues sur le serveur local, mais ne doivent pas être publiées sans autorisation.

Le script met à jour le tableau `images` des JSON avec `local_path`, `gallery_path`, `source`, `license` et `rights_status`. Le serveur local lit ces chemins ; relancer `python3 scripts/serve.py` et rafraîchir Firefox pour voir la galerie.

**Limites :** la recherche Google Images n'a pas d'API publique libre utilisable sans clé ni autorisation ; le collecteur ne contourne pas les blocages ni les licences. Wikimedia Commons peut imposer des limites de débit, et certains modèles n'ont aucune photo libre correspondante. « Jusqu'à cinq » n'est donc pas une promesse de cinq images pour chaque référence. Les miniatures ne sont pas encore redimensionnées : elles sont pour l'instant des copies des originaux autorisés.

# Marketplace V1.0 — branche de test

## Démarrage local
```bash
git switch feature/marketplace-manual-v1
python3 scripts/serve.py
```
Ouvrir http://127.0.0.1:8765, rubrique Marketplace.

## Fonctions
- Ajouter une annonce manuellement, modifier une annonce.
- Associer éventuellement la référence à un composant existant.
- Enregistrer prix demandé, livraison estimée, proposition, prix accepté, coût payé, port payé.
- Ajouter des offres horodatées dans l'historique.
- Suivre les statuts repérée, négociation, acceptée, payée, refusée, expirée.
- Consulter les dépenses Marketplace des annonces payées, distinctes du budget historique des composants.

## Limites V1
- Pas de scraping, d'import automatique, de compte utilisateur ni de synchronisation externe.
- Référence inconnue autorisée sans fiche technique : liaison ultérieure manuelle.
- Les achats Marketplace ne sont pas ajoutés automatiquement au budget matériel pour éviter les doublons.
- Usage sur localhost; éviter toute exposition réseau.
- Pour sauvegarder les annonces, sauvegarder le dossier Listings/. Les données saisies ne sont pas automatiquement poussées sur GitHub.

## Scénarios de validation
1. Ajouter une annonce : vérifier la création d'un JSON et l'affichage dans Marketplace.
2. Modifier l'annonce puis actualiser la page : vérifier la persistance.
3. Ajouter deux offres et vérifier l'ordre et les dates.
4. Mettre un statut autre que payée : vérifier qu'aucune dépense n'est calculée.
5. Mettre statut payée sans montant : vérifier le rejet.
6. Renseigner 150 € payé et 8 € port, statut payée : total Marketplace 158 €.
7. Vérifier que les feuilles Inventaire, Budget initial et le dashboard des composants ne changent pas.

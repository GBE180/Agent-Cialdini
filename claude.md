# Book Concept Agent

## Objectif
Extraire les concepts clés d'un livre EPUB et envoyer une notification quotidienne.

## Stack technique
- Python 3.11+
- Libs: ebooklib, beautifulsoup4, anthropic, requests
- Stockage: data/concepts.json (tableau JSON)
- Notifications: ntfy.sh (canal: book-concepts-<ton-id>)

## Structure des concepts
Chaque concept dans concepts.json suit ce schéma :
{
  "id": "uuid",
  "titre": "nom court",
  "definition": "2-3 phrases claires",
  "exemple": "application concrète",
  "categorie": "outil|méthode|principe|framework",
  "tags": ["mot-clé-1", "mot-clé-2"],
  "source_chapitre": "Chapitre X",
  "envoye": false
}

## Règles importantes
- Ne jamais écraser concepts.json sans sauvegarde
- Toujours valider le JSON avant d'écrire
- Utiliser l'agent epub-extractor pour tout parsing EPUB
- Utiliser l'agent notif-sender pour toute notification
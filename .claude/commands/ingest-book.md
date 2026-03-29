---
description: Ingère un fichier EPUB et extrait tous les concepts
---

L'utilisateur veut ingérer un livre EPUB. Voici les étapes :

1. Vérifier que le fichier EPUB existe (demander le chemin si non fourni)
2. Installer les dépendances si nécessaire :
   `pip install ebooklib beautifulsoup4 anthropic`
3. Déléguer à l'agent @epub-extractor avec le chemin du fichier
4. Afficher un résumé final : nombre de concepts, catégories trouvées
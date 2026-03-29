#!/usr/bin/env python3
"""
Script pour parser un fichier EPUB et extraire les concepts cles
en utilisant l'API Claude (claude-haiku-4-5-20251001).
"""

import os
import sys
import json
import uuid
import re
import shutil
from datetime import datetime
from pathlib import Path

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import anthropic


# Configuration
BASE_DIR = Path("C:/Users/WORKs/Desktop/Travail_IA/book-agent")
DATA_DIR = BASE_DIR / "data"
CONCEPTS_FILE = DATA_DIR / "concepts.json"
ERROR_LOG = DATA_DIR / "extraction_errors.log"

# Modele Claude a utiliser
CLAUDE_MODEL = "claude-haiku-4-5-20251001"


def log_error(message: str):
    """Log une erreur dans le fichier de log."""
    timestamp = datetime.now().isoformat()
    with open(ERROR_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"ERREUR: {message}", file=sys.stderr)


def backup_concepts_file():
    """Cree une sauvegarde du fichier concepts.json avant modification."""
    if CONCEPTS_FILE.exists() and CONCEPTS_FILE.stat().st_size > 0:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = DATA_DIR / f"concepts_backup_{timestamp}.json"
        shutil.copy(CONCEPTS_FILE, backup_path)
        print(f"Sauvegarde creee: {backup_path}")
        return backup_path
    return None


def load_existing_concepts() -> list:
    """Charge les concepts existants depuis concepts.json."""
    if not CONCEPTS_FILE.exists():
        return []

    try:
        content = CONCEPTS_FILE.read_text(encoding="utf-8").strip()
        if not content:
            return []
        concepts = json.loads(content)
        if not isinstance(concepts, list):
            return []
        return concepts
    except json.JSONDecodeError as e:
        log_error(f"Erreur de parsing JSON dans concepts.json: {e}")
        return []


def save_concepts(concepts: list) -> bool:
    """Sauvegarde les concepts dans concepts.json apres validation."""
    try:
        # Validation du JSON avant ecriture
        json_str = json.dumps(concepts, ensure_ascii=False, indent=2)
        # Re-parser pour valider
        json.loads(json_str)

        # Ecriture
        CONCEPTS_FILE.write_text(json_str, encoding="utf-8")
        return True
    except (json.JSONDecodeError, TypeError) as e:
        log_error(f"Erreur de validation JSON: {e}")
        return False


def extract_text_from_html(html_content: str) -> str:
    """Extrait le texte brut d'un contenu HTML."""
    soup = BeautifulSoup(html_content, "html.parser")

    # Supprimer les scripts et styles
    for tag in soup(["script", "style", "meta", "link"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    # Nettoyer les espaces multiples
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()


def get_chapter_title(soup: BeautifulSoup, default: str) -> str:
    """Tente d'extraire le titre du chapitre."""
    # Chercher h1, h2, ou titre
    for tag in ["h1", "h2", "title"]:
        element = soup.find(tag)
        if element and element.get_text(strip=True):
            title = element.get_text(strip=True)
            if len(title) > 3 and len(title) < 200:
                return title
    return default


def parse_epub(epub_path: str) -> list:
    """
    Parse un fichier EPUB et retourne une liste de chapitres.
    Chaque chapitre est un dict avec 'title' et 'content'.
    """
    chapters = []

    try:
        book = epub.read_epub(epub_path)
    except Exception as e:
        log_error(f"Erreur lors de l'ouverture de l'EPUB: {e}")
        return []

    chapter_num = 0
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            try:
                content = item.get_content().decode("utf-8", errors="ignore")
                text = extract_text_from_html(content)

                # Ignorer les contenus trop courts (pages de titre, etc.)
                if len(text) < 500:
                    continue

                chapter_num += 1
                soup = BeautifulSoup(content, "html.parser")
                title = get_chapter_title(soup, f"Chapitre {chapter_num}")

                chapters.append({
                    "title": title,
                    "content": text,
                    "item_name": item.get_name()
                })

            except Exception as e:
                log_error(f"Erreur lors du parsing de {item.get_name()}: {e}")
                continue

    print(f"Nombre de chapitres extraits: {len(chapters)}")
    return chapters


def extract_concepts_from_chapter(client: anthropic.Anthropic, chapter: dict) -> list:
    """
    Utilise l'API Claude pour extraire les concepts d'un chapitre.
    """
    title = chapter["title"]
    content = chapter["content"]

    # Limiter le contenu si trop long (limite tokens)
    max_chars = 15000
    if len(content) > max_chars:
        content = content[:max_chars] + "...[contenu tronque]"

    prompt = f"""Tu es un expert en extraction de concepts cles a partir de textes de non-fiction.

Analyse le chapitre suivant du livre "Influence et Manipulation" de Robert Cialdini et extrais les concepts cles.

CHAPITRE: {title}

CONTENU:
{content}

Pour chaque concept identifie, retourne un objet JSON avec:
- "titre": nom court du concept (3-5 mots max)
- "definition": explication claire en 2-3 phrases
- "exemple": une application concrete du concept
- "categorie": une parmi ["outil", "methode", "principe", "framework"]
- "tags": liste de 2-4 mots-cles pertinents

IMPORTANT:
- Extrais uniquement les concepts fondamentaux et significatifs
- Evite les redondances
- Concentre-toi sur les techniques d'influence et principes psychologiques
- Le livre traite de 6 principes majeurs: reciprocite, engagement/coherence, preuve sociale, autorite, sympathie, rarete

Retourne UNIQUEMENT un tableau JSON valide, sans texte supplementaire.
Si aucun concept significatif n'est trouve, retourne [].

Exemple de format attendu:
[
  {{
    "titre": "Principe de reciprocite",
    "definition": "Les gens se sentent obliges de rendre les faveurs recues. Cette obligation sociale est profondement ancree.",
    "exemple": "Offrir un echantillon gratuit pour inciter a l'achat.",
    "categorie": "principe",
    "tags": ["reciprocite", "obligation", "don"]
  }}
]
"""

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = response.content[0].text.strip()

        # Extraire le JSON de la reponse
        # Parfois le modele ajoute des backticks
        if response_text.startswith("```"):
            response_text = re.sub(r'^```json?\s*', '', response_text)
            response_text = re.sub(r'\s*```$', '', response_text)

        concepts = json.loads(response_text)

        if not isinstance(concepts, list):
            log_error(f"Reponse non-liste pour {title}")
            return []

        # Ajouter les metadonnees
        for concept in concepts:
            concept["id"] = str(uuid.uuid4())
            concept["source_chapitre"] = title
            concept["envoye"] = False

        return concepts

    except json.JSONDecodeError as e:
        log_error(f"Erreur JSON pour chapitre '{title}': {e}\nReponse: {response_text[:500]}")
        return []
    except anthropic.APIError as e:
        log_error(f"Erreur API Anthropic pour chapitre '{title}': {e}")
        return []
    except Exception as e:
        log_error(f"Erreur inattendue pour chapitre '{title}': {e}")
        return []


def deduplicate_concepts(existing: list, new_concepts: list) -> list:
    """
    Fusionne les nouveaux concepts avec les existants en evitant les doublons.
    """
    existing_titles = {c.get("titre", "").lower() for c in existing}

    unique_new = []
    for concept in new_concepts:
        titre = concept.get("titre", "").lower()
        if titre and titre not in existing_titles:
            unique_new.append(concept)
            existing_titles.add(titre)

    return existing + unique_new


def main(epub_path: str):
    """Fonction principale d'extraction."""
    print(f"Demarrage de l'extraction pour: {epub_path}")

    # Verifier que le fichier existe
    if not os.path.exists(epub_path):
        log_error(f"Fichier EPUB introuvable: {epub_path}")
        return None

    # Sauvegarder les concepts existants
    backup_concepts_file()

    # Charger les concepts existants
    existing_concepts = load_existing_concepts()
    print(f"Concepts existants: {len(existing_concepts)}")

    # Parser l'EPUB
    chapters = parse_epub(epub_path)
    if not chapters:
        log_error("Aucun chapitre extrait de l'EPUB")
        return None

    # Initialiser le client Anthropic (utilise automatiquement ANTHROPIC_API_KEY)
    try:
        client = anthropic.Anthropic()
    except anthropic.AuthenticationError as e:
        log_error(f"Erreur d'authentification Anthropic: {e}")
        return None

    # Extraire les concepts de chaque chapitre
    all_new_concepts = []
    stats_by_category = {}

    for i, chapter in enumerate(chapters):
        print(f"\nTraitement du chapitre {i+1}/{len(chapters)}: {chapter['title'][:50]}...")

        concepts = extract_concepts_from_chapter(client, chapter)
        print(f"  -> {len(concepts)} concepts extraits")

        for concept in concepts:
            cat = concept.get("categorie", "autre")
            stats_by_category[cat] = stats_by_category.get(cat, 0) + 1

        all_new_concepts.extend(concepts)

    # Deduplication et fusion
    final_concepts = deduplicate_concepts(existing_concepts, all_new_concepts)
    new_count = len(final_concepts) - len(existing_concepts)

    print(f"\n{'='*50}")
    print(f"Nouveaux concepts uniques: {new_count}")
    print(f"Total concepts: {len(final_concepts)}")

    # Sauvegarder
    if save_concepts(final_concepts):
        print(f"Concepts sauvegardes dans: {CONCEPTS_FILE}")
    else:
        log_error("Echec de la sauvegarde des concepts")
        return None

    # Resume
    summary = {
        "total_concepts": len(final_concepts),
        "nouveaux_concepts": new_count,
        "chapitres_traites": len(chapters),
        "categories": stats_by_category
    }

    print(f"\n{'='*50}")
    print("RESUME DE L'EXTRACTION")
    print(f"{'='*50}")
    print(f"Chapitres traites: {summary['chapitres_traites']}")
    print(f"Nouveaux concepts extraits: {summary['nouveaux_concepts']}")
    print(f"Total concepts en base: {summary['total_concepts']}")
    print("\nRepartition par categorie:")
    for cat, count in sorted(stats_by_category.items()):
        print(f"  - {cat}: {count}")

    return summary


if __name__ == "__main__":
    if len(sys.argv) < 2:
        epub_file = str(BASE_DIR / "Influence et manipulation.epub")
    else:
        epub_file = sys.argv[1]

    result = main(epub_file)

    if result:
        print("\nExtraction terminee avec succes!")
    else:
        print("\nExtraction terminee avec des erreurs.", file=sys.stderr)
        sys.exit(1)

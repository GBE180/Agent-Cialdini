#!/usr/bin/env python3
"""
Script pour extraire les chapitres d'un fichier EPUB et les sauvegarder en JSON.
"""

import sys
import json
import re
from pathlib import Path

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup


def extract_text_from_html(html_content: str) -> str:
    """Extrait le texte brut d'un contenu HTML."""
    soup = BeautifulSoup(html_content, "html.parser")
    for tag in soup(["script", "style", "meta", "link"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()


def get_chapter_title(soup: BeautifulSoup, default: str) -> str:
    """Extrait le titre du chapitre."""
    for tag in ["h1", "h2", "title"]:
        element = soup.find(tag)
        if element and element.get_text(strip=True):
            title = element.get_text(strip=True)
            if len(title) > 3 and len(title) < 200:
                return title
    return default


def parse_epub(epub_path: str) -> list:
    """Parse un fichier EPUB et retourne les chapitres."""
    chapters = []
    book = epub.read_epub(epub_path)

    chapter_num = 0
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            content = item.get_content().decode("utf-8", errors="ignore")
            text = extract_text_from_html(content)

            if len(text) < 500:
                continue

            chapter_num += 1
            soup = BeautifulSoup(content, "html.parser")
            title = get_chapter_title(soup, f"Chapitre {chapter_num}")

            # Nettoyer le titre
            title = title.replace('\xa0', ' ').replace('�', ' ')

            chapters.append({
                "numero": chapter_num,
                "title": title,
                "content": text[:20000],  # Limiter la taille
                "length": len(text)
            })

    return chapters


if __name__ == "__main__":
    epub_path = sys.argv[1] if len(sys.argv) > 1 else "C:/Users/WORKs/Desktop/Travail_IA/book-agent/Influence et manipulation.epub"
    chapters = parse_epub(epub_path)

    output = {
        "source": epub_path,
        "total_chapters": len(chapters),
        "chapters": chapters
    }

    output_path = Path("C:/Users/WORKs/Desktop/Travail_IA/book-agent/data/chapters.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Chapitres extraits: {len(chapters)}")
    for ch in chapters:
        print(f"  {ch['numero']}. {ch['title'][:60]}... ({ch['length']} chars)")

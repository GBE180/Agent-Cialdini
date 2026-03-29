#!/usr/bin/env python3
"""
Script pour lire un chapitre specifique du fichier chapters.json.
"""

import sys
import json
from pathlib import Path

chapters_path = Path("C:/Users/WORKs/Desktop/Travail_IA/book-agent/data/chapters.json")

with open(chapters_path, "r", encoding="utf-8") as f:
    data = json.load(f)

chapter_num = int(sys.argv[1]) if len(sys.argv) > 1 else 1

if chapter_num < 1 or chapter_num > len(data["chapters"]):
    print(f"Chapitre invalide. Disponibles: 1-{len(data['chapters'])}")
    sys.exit(1)

chapter = data["chapters"][chapter_num - 1]
print(f"=== CHAPITRE {chapter_num}: {chapter['title']} ===")
print(f"Longueur: {chapter['length']} caracteres")
print()
print(chapter["content"])

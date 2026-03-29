#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script to send daily concept notifications via ntfy.sh"""

import json
import requests
import sys
import os
from datetime import datetime

# Force UTF-8 encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def send_notification(concept, user_id="book-concepts-default"):
    """Send a concept notification via ntfy.sh"""

    # Format the message (max 200 words)
    title = concept['titre']
    definition = concept['definition']
    exemple = concept['exemple']
    categorie = concept['categorie']

    # Create the message
    message = f"""
{title}

{definition}

Exemple: {exemple}

Catégorie: {categorie}
Source: {concept['source_chapitre']}
"""

    # ntfy.sh endpoint
    ntfy_url = f"https://ntfy.sh/{user_id}"

    headers = {
        "Title": title,
        "Tags": "book,concept",
        "Priority": "default"
    }

    try:
        response = requests.post(ntfy_url, data=message, headers=headers)
        response.raise_for_status()
        print(f"[OK] Notification envoyée: {title}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"[ERREUR] Erreur lors de l'envoi: {e}")
        return False

def mark_as_sent(concept_id, concepts_file):
    """Mark a concept as sent in the JSON file"""

    with open(concepts_file, 'r', encoding='utf-8') as f:
        concepts = json.load(f)

    # Find and update the concept
    for concept in concepts:
        if concept['id'] == concept_id:
            concept['envoye'] = True
            break

    # Write back to file
    with open(concepts_file, 'w', encoding='utf-8') as f:
        json.dump(concepts, f, indent=2, ensure_ascii=False)

    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: send_notification.py <concepts_file> <concept_id> [user_id]")
        sys.exit(1)

    concepts_file = sys.argv[1]
    concept_id = sys.argv[2]
    user_id = sys.argv[3] if len(sys.argv) > 3 else "book-concepts-default"

    # Load concept
    with open(concepts_file, 'r', encoding='utf-8') as f:
        concepts = json.load(f)

    concept = None
    for c in concepts:
        if c['id'] == concept_id:
            concept = c
            break

    if not concept:
        print(f"Concept {concept_id} not found")
        sys.exit(1)

    # Send notification
    if send_notification(concept, user_id):
        # Mark as sent
        mark_as_sent(concept_id, concepts_file)
        print(f"[OK] Concept marqué comme envoyé")
        sys.exit(0)
    else:
        sys.exit(1)

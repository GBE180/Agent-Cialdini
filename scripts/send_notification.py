import json
import os
import requests
from datetime import date
import anthropic

# Chemins
CONCEPTS_FILE = "data/concepts.json"
NTFY_CHANNEL = "Cialdini-GBE180"  # personnalise ce nom

def load_concepts():
    with open(CONCEPTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_concepts(concepts):
    with open(CONCEPTS_FILE, "w", encoding="utf-8") as f:
        json.dump(concepts, f, ensure_ascii=False, indent=2)

def pick_concept(concepts):
    # Cherche les concepts non envoyés
    non_envoyes = [c for c in concepts if not c.get("envoye", False)]
    
    # Si tous envoyés, on réinitialise
    if not non_envoyes:
        for c in concepts:
            c["envoye"] = False
        non_envoyes = concepts
    
    # Sélection basée sur la date (reproductible)
    index = date.today().toordinal() % len(non_envoyes)
    return non_envoyes[index]

def format_message(concept):
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": f"""Transforme ce concept en une notification mobile 
engageante et mémorable (max 150 mots, ton dynamique) :

Titre: {concept['titre']}
Définition: {concept['definition']}
Exemple: {concept.get('exemple', '')}

Commence directement par le contenu, sans intro."""
        }]
    )
    return response.content[0].text

def send_notification(title, body):
    requests.post(
        f"https://ntfy.sh/{NTFY_CHANNEL}",
        data=body.encode("utf-8"),
        headers={
            "Title": title,
            "Priority": "default",
            "Tags": "book,concept"
        }
    )
    print(f"✅ Notification envoyée : {title}")

def main():
    concepts = load_concepts()
    concept = pick_concept(concepts)
    
    message = format_message(concept)
    send_notification(concept["titre"], message)
    
    # Marquer comme envoyé
    for c in concepts:
        if c.get("titre") == concept["titre"]:
            c["envoye"] = True
            break
    
    save_concepts(concepts)

if __name__ == "__main__":
    main()
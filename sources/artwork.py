import requests
import os
import json
from PIL import Image
Image.MAX_IMAGE_PIXELS = None  # Désactive la vérification de la taille de l'image
from io import BytesIO
import time

def resize_image(image_url, max_height=1040):
    print(image_url)
    response = requests.get(image_url)
    if 'image' not in response.headers.get('Content-Type', ''):
        print(f"Erreur: Le contenu à {image_url} n'est pas une image.")
        return None
    try:
        img = Image.open(BytesIO(response.content))
    except IOError as e:
        print(f"Erreur lors de l'ouverture de l'image depuis {image_url}: {e}")
        return None
    width, height = img.size
    if height > max_height:
        ratio = max_height / height
        new_width = int(width * ratio)
        new_height = max_height
        img = img.resize((new_width, new_height), Image.LANCZOS)
    return img

def telecharger_image(nom, url, retries=3, delay=5):
    # Récupère le répertoire du script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Construit le chemin vers le dossier assets/oeuvre qui se trouve dans le dossier parent de src
    oeuvres_folder = os.path.join(script_dir, "assets", "oeuvre")
    
    if not os.path.exists(oeuvres_folder):
        os.makedirs(oeuvres_folder)
    image_path = os.path.join(oeuvres_folder, nom)
    
    if not os.path.exists(image_path):
        print(f"Téléchargement de {nom}...")
        headers = {'User-Agent': 'Mozilla/5.0'}
        for attempt in range(retries):
            try:
                response = requests.get(url, headers=headers)
                print(f"Code de statut pour {nom}: {response.status_code}")
                response.raise_for_status()
                content_type = response.headers.get('Content-Type', '')
                if 'image' not in content_type:
                    print(f"Erreur: Le contenu à {url} n'est pas une image (Content-Type: {content_type}).")
                    return None
                try:
                    img = Image.open(BytesIO(response.content))
                except IOError as e:
                    print(f"Erreur lors de l'ouverture de l'image depuis {url}: {e}")
                    return None
                max_height = 1040
                width, height = img.size
                if height > max_height:
                    ratio = max_height / height
                    new_width = int(width * ratio)
                    img = img.resize((new_width, max_height), Image.LANCZOS)
                img.save(image_path)
                print(f"{nom} téléchargé et redimensionné avec succès.")
                return image_path
            except requests.exceptions.RequestException as e:
                print(f"Erreur lors du téléchargement de {nom} : {e}")
                if attempt < retries - 1:
                    print(f"Nouvelle tentative dans {delay} secondes...")
                    time.sleep(delay)
                else:
                    print("Échec après plusieurs tentatives.")
    return image_path


def fetch_artworks():
    print("Récupération des données depuis Wikidata...")
    url = "https://query.wikidata.org/sparql"
    query = """
    SELECT ?artwork ?artworkLabel ?creatorLabel ?image ?inception ?height ?width ?locationLabel WHERE {
      ?artwork wdt:P31 wd:Q3305213;
               wdt:P170 ?creator;
               wdt:P571 ?inception;
               wdt:P18 ?image.
      OPTIONAL { ?artwork wdt:P2048 ?height. }
      OPTIONAL { ?artwork wdt:P2049 ?width. }
      OPTIONAL { ?artwork wdt:P276 ?location. }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "fr". }
    }
    LIMIT 150
    """
    headers = {"User-Agent": "MyApp/1.0 (your@email.com)"}
    response = requests.get(url, params={"query": query, "format": "json"}, headers=headers)
    artworks = {}
    if response.status_code == 200:
        data = response.json()
        for item in data["results"]["bindings"]:
            titre = item["artworkLabel"]["value"]
            auteur = item["creatorLabel"]["value"]
            date = item["inception"]["value"]
            image_url = item["image"]["value"]
            hauteur = item.get("height", {}).get("value", "Inconnu")
            largeur = item.get("width", {}).get("value", "Inconnu")
            location = item.get("locationLabel", {}).get("value", "Inconnu")
            safe_titre = ''.join(e for e in titre if e.isalnum() or e == '_').lower()
            ext = os.path.splitext(image_url)[1] or '.jpg'
            nom_fichier = f"{safe_titre}{ext}"
            artworks[nom_fichier] = {
                "titre": titre,
                "auteur": auteur,
                "date": date,
                "image_url": image_url,
                "nom_fichier": nom_fichier,
                "hauteur": hauteur,
                "largeur": largeur,
                "location": location
            }
            print("Artwork:", titre, "par", auteur, "en", date, "- Dimensions:", hauteur, "x", largeur, "- Lieu:", location)
            telecharger_image(nom_fichier, image_url)
    else:
        print("Erreur lors de la requête Wikidata:", response.status_code)
    return artworks


# Récupère le répertoire du script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Construit le chemin vers le fichier dans le dossier data qui se trouve dans le répertoire parent de src
data_path = os.path.join(script_dir, "data", "oeuvres.json")

if os.path.exists(data_path):
    with open(data_path, "r", encoding="utf-8") as f:
        oeuvres_data = json.load(f)
else:
    oeuvres_data = fetch_artworks()
    
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(oeuvres_data, f, indent=4, ensure_ascii=False)
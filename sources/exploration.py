from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina import color, Vec2, Vec3
from ursina.lights import AmbientLight
import os, sys, json, random
from ursina.audio import Audio

# Variables globales
elt_jeu = None
joueur = None
terrain_actuel = {'num': 1}  # Numéro de l'étage actuel
tableau_utilise = set()  # Ensemble des tableaux déjà utilisés
tableaux_actuel = {}  # Dictionnaire des tableaux actuellement affichés
positions_etage1 = []  # Positions des tableaux pour l'étage 1
positions_etage2 = []  # Positions des tableaux pour l'étage 2

def chargement_oeuvres(json_file=r"sources/data/oeuvres.json"):
    """
    Charge les données des œuvres depuis un fichier JSON.

    Args:
        json_file (str): Chemin du fichier JSON contenant les données des œuvres.

    Returns:
        dict: Dictionnaire des œuvres avec leurs informations.
    """
    with open(json_file, "r", encoding="utf-8") as f:
        return json.load(f)

def chargement_textures(oeuvres, folder="../assets/oeuvre"):
    """
    Charge les textures des œuvres à partir des fichiers d'images.

    Args:
        oeuvres (dict): Dictionnaire des œuvres.
        folder (str): Dossier contenant les images des œuvres.

    Returns:
        dict: Dictionnaire des textures associées à chaque œuvre.
    """
    textures = {}
    for titre, data in oeuvres.items():
        chemin = os.path.join(folder, data["nom_fichier"])
        textures[titre] = chemin
    return textures

def creation_elements_jeu():
    """
    Crée les éléments de l'interface utilisateur du jeu, comme la minimap et la fenêtre d'information.

    Returns:
        dict: Dictionnaire contenant les éléments de l'interface utilisateur.
    """
    elt_jeu = Entity(name='elt_jeu', parent=camera.ui)

    # Minimap
    minimap_emplacement = Entity(parent=elt_jeu, model='quad', scale=(0.3, 0.3), position=(0.73, 0.35))
    if terrain_actuel['num'] == 1:
        minimap_texture = load_texture('../assets/minimap/grid.png')
    else:
        minimap_texture = load_texture('../assets/minimap/grid_etage2.png')
    Entity(parent=minimap_emplacement, model=Quad(scale=Vec3(1, 1, 1)), texture=minimap_texture, name='minimap')
    icone_joueur = Entity(parent=minimap_emplacement, model='circle', color=color.hex("#8a0000"), scale=(0.03, 0.03), z=-0.1)

    # Fenêtre d'information sur les tableaux
    fenetre_info = Entity(parent=elt_jeu, model='quad', color=color.rgba(240, 240, 240, 220), scale=(0.85, 0.5), position=(0, 0), enabled=False, shadow=True)
    fenetre_bordure = Entity(parent=elt_jeu, model='quad', color=color.hex('#8a0000'), scale=(0.87, 0.52), position=(0, 0), enabled=False, z=0.1)
    titre_texte = Text(parent=fenetre_info, text="", scale=2, position=(0, 0.3), origin=(0, 0), color=color.hex("#8a0000"))
    info_texte = Text(parent=fenetre_info, text="", scale=1.5, position=(0, 0.05), origin=(0, 0), color=color.black, font='polices/Poppins-Bold.ttf')

    return {
        'elt_jeu': elt_jeu,
        'fenetre_info': fenetre_info,
        'titre_texte': titre_texte,
        'info_texte': info_texte,
        'fenetre_bordure': fenetre_bordure,
        'minimap': {
            'minimap_emplacement': minimap_emplacement,
            'icone_joueur': icone_joueur,
        }
    }

def chargement_modele(debut_jeu, etage_num=1):
    """
    Charge les modèles 3D pour l'étage spécifié.

    Args:
        debut_jeu (Entity): Entité parente pour les modèles.
        etage_num (int): Numéro de l'étage (1 ou 2).

    Returns:
        tuple: (terrain, collisions_entity) - Entités du terrain et des collisions.
    """
    glb = f"../assets/models/etage{etage_num}.glb"
    collision = f"../assets/models/etage{etage_num}_collision.obj"

    modele_glb = load_model(glb)
    modele_collision = load_model(collision)
    if not modele_glb or not modele_collision:
        print(f"❌ Erreur : Modèle non trouvé pour l'étage {etage_num}. Vérifiez vos fichiers !")
        sys.exit(1)
    terrain = Entity(model=modele_glb, position=(0, 0, 0), parent=debut_jeu, visible=True)
    collisions_entity = Entity(model=modele_collision, collider='mesh', visible=False, position=(0, 0, 0), scale=(-1, 1, 1), parent=debut_jeu)
    return terrain, collisions_entity

def creation_joueur(debut_jeu):
    """
    Crée le joueur avec un contrôleur en première personne.

    Args:
        debut_jeu (Entity): Entité parente pour le joueur.

    Returns:
        FirstPersonController: Instance du joueur.
    """
    joueur = FirstPersonController(collider='box', speed=7, position=(0, 0, 0), parent=debut_jeu)
    joueur.camera_pivot.y = 1.6
    return joueur

def creation_tableaux(debut_jeu, oeuvres, textures, positions, on_click_callback):
    """
    Crée les entités des tableaux dans le jeu.

    Args:
        debut_jeu (Entity): Entité parente pour les tableaux.
        oeuvres (dict): Dictionnaire des œuvres.
        textures (dict): Dictionnaire des textures des œuvres.
        positions (list): Liste des positions des tableaux.
        on_click_callback (function): Fonction à appeler lors d'un clic sur un tableau.

    Returns:
        dict: Dictionnaire des entités des tableaux.
    """
    random.shuffle(positions)
    tableaux = {}
    pos_index = 0

    def convertir_en_float(valeur, valeur_par_defaut):
        """Convertit une valeur en float ou retourne une valeur par défaut."""
        try:
            return float(valeur)
        except (ValueError, TypeError):
            return valeur_par_defaut

    for titre, data in oeuvres.items():
        if pos_index >= len(positions):
            break
        pos, rot = positions[pos_index]
        pos_index += 1

        # Récupération des dimensions avec gestion des erreurs
        hauteur = convertir_en_float(data.get('hauteur'), 3)  # 3 par défaut
        largeur = convertir_en_float(data.get('largeur'), 5)  # 5 par défaut

        # Calcul de l'échelle en fonction des dimensions
        r1 = largeur / 5
        r2 = hauteur / 3
        if r1 > r2:
            largeur = largeur / r1
            hauteur = hauteur / r1
        else:
            largeur = largeur / r2
            hauteur = hauteur / r2
        tableau_entity = Entity(model='quad', texture=textures[titre], position=pos, rotation=rot, scale=(largeur, hauteur), collider='box', name=titre, parent=debut_jeu, double_sided=True)
        tableau_entity.on_click = lambda e=tableau_entity: on_click_callback(e)
        tableaux[titre] = tableau_entity
    return tableaux

def blocage_controle(joueur):
    """Bloque les contrôles du joueur."""
    joueur.speed = 0
    joueur.mouse_sensitivity = Vec2(0, 0)
    mouse.locked = False

def deblocage_controle(joueur):
    """Débloque les contrôles du joueur."""
    joueur.speed = 7
    joueur.mouse_sensitivity = Vec2(100, 100)
    mouse.locked = True

def afficher_infos_tableaux(elt_jeu, data, joueur):
    """
    Affiche les informations d'un tableau dans une fenêtre.

    Args:
        elt_jeu (dict): Dictionnaire des éléments de l'interface utilisateur.
        data (dict): Informations du tableau.
        joueur (FirstPersonController): Instance du joueur.
    """
    fenetre_info = elt_jeu['fenetre_info']
    fenetre_info.enabled = True
    fenetre_bordure = elt_jeu['fenetre_bordure']
    fenetre_bordure.enabled = True
    blocage_controle(joueur)

    # Titre
    elt_jeu['titre_texte'].text = f"{data['titre']}"

    # Informations
    info_text = ""
    if 'auteur' in data and data['auteur'] and not data['auteur'].startswith('Q'):
        info_text += f"Auteur: {data['auteur']}\n\n"
    if 'date' in data and data['date'] and not data['date'].startswith('Q'):
        info_text += f"Date: {data['date'].split('-')[0]}\n\n"
    if 'hauteur' in data and 'largeur' in data and data['hauteur'] and data['largeur'] and not data['hauteur'].startswith('Q') and not data['largeur'].startswith('Q'):
        info_text += f"Dimensions: {data['hauteur']}x{data['largeur']} cm\n\n"
    if 'location' in data and data['location'] and not data['location'].startswith('Q'):
        info_text += f"Localisation: {data['location']}\n\n"

    elt_jeu['info_texte'].text = info_text

    # Bouton Fermer
    Button(parent=fenetre_info, text='Fermer', scale=(0.3, 0.1), position=(0, -0.3), color=color.hex("#8a0000"), on_click=Func(lambda: [son_clic.play(), setattr(fenetre_info, 'enabled', False), setattr(fenetre_bordure, 'enabled', False), deblocage_controle(joueur)]))

def affichage_clique(e, oeuvres, elt_jeu, joueur):
    """
    Gère l'affichage des informations d'un tableau lors d'un clic.

    Args:
        e (Entity): Entité du tableau cliqué.
        oeuvres (dict): Dictionnaire des œuvres.
        elt_jeu (dict): Dictionnaire des éléments de l'interface utilisateur.
        joueur (FirstPersonController): Instance du joueur.
    """
    son_clic.play()
    if data := oeuvres.get(e.name):
        afficher_infos_tableaux(elt_jeu, data, joueur)

def jeu_principal_exploration():
    """
    Fonction principale du mode exploration. Initialise le jeu, charge les ressources,
    et démarre la boucle principale.
    """
    global son_marche, son_saut, son_clic, musique_fond, elt_jeu, joueur, terrain_actuel, oeuvres, textures, tableaux_actuel, positions_etage1, positions_etage2, debut_jeu
    son_marche = Audio('../assets/musique/bruit_pas.mp3', loop=True, autoplay=False)
    son_saut = Audio('../assets/musique/saut.mp3', loop=False, autoplay=False)
    son_clic = Audio('../assets/musique/clique.mp3', loop=False, autoplay=False)
    musique_fond = Audio("../assets/musique/exploration.mp3", loop=True, autoplay=True)
    AmbientLight(color=(1, 1, 1, 1))

    debut_jeu = Entity(name='debut_jeu')
    oeuvres = chargement_oeuvres()
    textures = chargement_textures(oeuvres)
    elt_jeu = creation_elements_jeu()

    # Définition des listes de positions pour chaque étage
    positions_etage1 = [((9.45, 2.5, 10.5), (0, 90, 0)), ((9.45, 2.5, 18), (0, 90, 0)), ((9.45, 2.5, 25.5), (0, 90, 0)), ((9.45, 2.5, 33), (0, 90, 0)), ((9.45, 2.5, 40.5), (0, 90, 0)), ((5, 2.5, 44.7), (0, 0, 0)), ((-2.5, 2.5, 44.7), (0, 0, 0)),
                        ((-9.45, 2.5, 37.4), (0, -90, 0)), ((-9.45, 2.5, 30.4), (0, -90, 0)), ((-9.45, 2.5, 23.4), (0, -90, 0)), ((-9.45, 2.5, 17), (0, -90, 0)), ((-9.45, 2.5, 9), (0, 270, 0)), ((5.5, 2.5, 5.55), (0, 180, 0)), ((-5.5, 2.5, 5.55), (0, 180, 0)),
                        ((0.21, 2.5, 35), (0, -90, 0)), ((-0.21, 2.5, 35), (0, 90, 0)), ((0.21, 2.5, 22), (0, -90, 0)), ((-0.21, 2.5, 22), (0, 90, 0)), ((-20.3, 2.5, 45), (0, 90, 0)), ((-20.3, 2.5, 52), (0, 90, 0)), ((-20.3, 2.5, 59), (0, 90, 0)),
                        ((-24, 2.5, 64.7), (0, 0, 0)), ((-31, 2.5, 64.7), (0, 0, 0)), ((-35.7, 2.5, 61), (0, -90, 0)), ((-35.7, 2.5, 54), (0, -90, 0)), ((-35.7, 2.5, 47), (0, -90, 0)), ((-35.7, 2.5, 40), (0, -90, 0)), ((-30, 2.5, 35.6), (0, 180, 0)),
                        ((-28, 2.5, 43.78), (0, 0, 0)), ((-28, 2.5, 44.21), (0, 180, 0)), ((-29.6, 2.5, 12), (0, -90, 0)), ((-24.5, 2.5, 7.8), (0, 180, 0))]

    positions_etage2 = [((19.45, 2.5, 10.5), (0, 90, 0)), ((19.45, 2.5, 18), (0, 90, 0)), ((19.45, 2.5, 25.5), (0, 90, 0)), ((19.45, 2.5, 33), (0, 90, 0)), ((19.45, 2.5, 40.5), (0, 90, 0)), ((5, 2.5, 44.7), (0, 0, 0)), ((-2.5, 2.5, 44.7), (0, 0, 0)),
                        ((12, 2.5, 44.7), (0, 0, 0)), ((-9.45, 2.5, 37.4), (0, -90, 0)), ((-9.45, 2.5, 30.4), (0, -90, 0)), ((-9.45, 2.5, 23.4), (0, -90, 0)), ((-9.45, 2.5, 17), (0, -90, 0)), ((-9.45, 2.5, 9), (0, 90, 0)), ((5.5, 2.5, 5.55), (0, 180, 0)), ((-5.5, 2.5, 5.55), (0, 180, 0)),
                        ((12.5, 2.5, 5.55), (0, 180, 0)), ((0.1, 2.5, 34.75), (0, -180, 0)), ((0.1, 2.5, 35.25), (0, 180, 0)), ((10, 2.5, 34.75), (0, -180, 0)), ((10, 2.5, 35.25), (0, 180, 0)), ((0.1, 2.5, 21.755), (0, -180, 0)), ((0.1, 2.5, 22.23), (0, 180, 0)),
                        ((10, 2.5, 21.755), (0, -180, 0)), ((10, 2.5, 22.23), (0, 180, 0)), ((-20.3, 2.5, 45), (0, 90, 0)), ((-20.3, 2.5, 52), (0, 90, 0)), ((-20.3, 2.5, 59), (0, 90, 0)), ((-24, 2.5, 64.7), (0, 0, 0)), ((-31, 2.5, 64.7), (0, 0, 0)),
                        ((-35.7, 2.5, 61), (0, -90, 0)), ((-35.7, 2.5, 54), (0, -90, 0)), ((-35.7, 2.5, 47), (0, -90, 0)), ((-35.7, 2.5, 40), (0, -90, 0)), ((-30, 2.5, 35.6), (0, 180, 0)), ((-28, 2.5, 43.78), (0, 0, 0)), ((-28, 2.5, 44.21), (0, 180, 0)),
                        ((-28, 2.5, 55.25), (0, 0, 0)), ((-28, 2.5, 54.75), (0, 180, 0)), ((-35.7, 2.5, 13), (0, -90, 0)), ((-35.7, 2.5, 6), (0, -90, 0)), ((-35.7, 2.5, -1), (0, -90, 0)), ((-30, 2.5, 16.95), (0, 180, 0)), ((-31.5, 2.5, -4.6), (0, 180, 0)),
                        ((-24.5, 2.5, -4.6), (0, 180, 0)), ((-17.5, 2.5, -4.6), (0, 180, 0)), ((-10.5, 2.5, -4.6), (0, 180, 0)), ((-3.5, 2.5, -4.6), (0, 180, 0)), ((-3.5, 2.5, 4.98), (0, 0, 0)), ((-10.5, 2.5, 4.98), (0, 0, 0)), ((-17.5, 2.5, 4.98), (0, 0, 0)),
                        ((-20.3, 2.5, 9), (0, 90, 0)), ((-29.8, 2.5, 2), (0, 0, 0)), ((-29.8, 2.5, 2.45), (0, 180, 0)), ((-29.8, 2.5, 10.12), (0, 0, 0)), ((-29.8, 2.5, 10.62), (0, 180, 0)), ((-30, 2.5, 31), (0, -90, 0)), ((-30, 2.5, 23.5), (0, -90, 0))]

    joueur = creation_joueur(debut_jeu)
    terrain_actuel['terrain'], terrain_actuel['collider'] = chargement_modele(debut_jeu, 1)

    folder = "../assets/image"
    chemin_ascensceur = os.path.join(folder, "ascensceur.jpg")
    ascenseur = load_texture(chemin_ascensceur)
    bouton_etage = Button(parent=debut_jeu, model='quad', texture=ascenseur, rotation=Vec3(0, 90, 0), position=(4.49, 2.5, 0), scale=(5, 5, 0.1), on_click=lambda: changer_etage(debut_jeu), double_sided=True, highlight_color=color.white)

    tableaux_actuel = creation_tableaux(debut_jeu, oeuvres, textures, positions_etage1, lambda e: affichage_clique(e, oeuvres, elt_jeu, joueur))
    verification_update = Entity(parent=debut_jeu)
    verification_update.update = lambda: update()
    return debut_jeu

def changer_etage(debut_jeu):
    """
    Change l'étage actuel du jeu en détruisant les éléments de l'étage précédent
    et en chargeant ceux du nouvel étage.

    Args:
        debut_jeu (Entity): Entité parente pour les éléments du jeu.
    """
    global tableaux_actuel, positions_etage1, positions_etage2, oeuvres, textures
    etage_précédent = terrain_actuel['num']
    destroy(terrain_actuel['terrain'])
    destroy(terrain_actuel['collider'])

    # Détruire les tableaux existants
    if tableaux_actuel:
        for titre in list(tableaux_actuel.keys()):
            destroy(tableaux_actuel[titre])
        tableaux_actuel.clear()
    tableau_utilise.clear()

    # Mettre à jour le numéro de l'étage et charger le nouveau terrain
    nouvel_etage = 2 if etage_précédent == 1 else 1
    terrain_actuel.update({'num': nouvel_etage, 'terrain': None, 'collider': None})
    terrain_actuel['terrain'], terrain_actuel['collider'] = chargement_modele(debut_jeu, nouvel_etage)

    # Créer les nouveaux tableaux pour le nouvel étage
    positions = positions_etage1 if nouvel_etage == 1 else positions_etage2
    tableaux_actuel = creation_tableaux(debut_jeu, oeuvres, textures, positions, lambda e: affichage_clique(e, oeuvres, elt_jeu, joueur))

    # Mettre à jour la minimap
    carte_emplacement = elt_jeu['minimap']['minimap_emplacement']
    for child in carte_emplacement.children:
        if child.name == 'grid':
            destroy(child)
    grid_texture = load_texture('../assets/minimap/grid.png' if nouvel_etage == 1 else '../assets/minimap/grid_etage2.png')
    Entity(parent=carte_emplacement, model='quad', texture=grid_texture, scale=(1, 1), name='grid')

    # Détruire l'ancienne icône du joueur avant de créer une nouvelle
    if 'icone_joueur' in elt_jeu['minimap']:
        destroy(elt_jeu['minimap']['icone_joueur'])

    # Mettre à jour la position du joueur et l'icône
    joueur.position = (0, 0, 0)
    joueur.rotation = (0, 0, 0)
    joueur.camera_pivot.rotation = (0, 0, 0)
    elt_jeu['minimap']['icone_joueur'] = Entity(parent=carte_emplacement, model='circle', color=color.hex("#8a0000"), scale=(0.03, 0.03), z=-0.1)
    update_minimap(joueur, elt_jeu['minimap'])

def update_minimap(joueur, minimap_data):
    """
    Met à jour la position de l'icône du joueur sur la minimap.

    Args:
        joueur (FirstPersonController): Instance du joueur.
        minimap_data (dict): Dictionnaire des données de la minimap.
    """
    if terrain_actuel['num'] == 1:
        echelle = 0.012
        decalage = Vec2(0.13, -0.35)
    else:
        echelle = 0.011
        decalage = Vec2(0.12, -0.325)
    icone_pos = Vec2(joueur.position.x, joueur.position.z) * echelle + decalage
    minimap_data['icone_joueur'].position = icone_pos

def main():
    """
    Fonction principale du programme. Initialise l'application Ursina et démarre le mode exploration.
    """
    app = Ursina()
    jeu_principal_exploration()
    app.run()

def update():
    """
    Fonction appelée à chaque frame pour mettre à jour les éléments du jeu.
    """
    global elt_jeu, joueur
    if elt_jeu and joueur:
        update_minimap(joueur, elt_jeu['minimap'])

    if held_keys['w'] or held_keys['a'] or held_keys['s'] or held_keys['d']:
        if not son_marche.playing:
            son_marche.play()
    else:
        son_marche.stop()

    if held_keys['space']:
        if not son_saut.playing:
            son_saut.play()
    if held_keys['escape']:
        retour_menu_principal()

def retour_menu_principal():
    """
    Retourne au menu principal en arrêtant les sons, détruisant les éléments du jeu
    et réinitialisant les variables globales.
    """
    global elt_jeu, joueur, debut_jeu, musique_fond, son_marche, son_saut, son_clic

    # Arrêter les sons et la musique
    if musique_fond:
        musique_fond.stop()
    if son_marche:
        son_marche.stop()
    if son_saut:
        son_saut.stop()
    if son_clic:
        son_clic.stop()

    # Détruire les éléments du jeu
    if debut_jeu:
        destroy(debut_jeu)
    if elt_jeu and elt_jeu['elt_jeu']:
        destroy(elt_jeu['elt_jeu'])
    if joueur:
        destroy(joueur)

    # Réinitialiser les variables globales
    elt_jeu = None
    joueur = None
    debut_jeu = None

    # Réafficher le menu principal
    from main import afficher_menu_principal
    afficher_menu_principal()
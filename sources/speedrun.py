import os
import sys
import json
import random
import time
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina import color, Vec2, Vec3

# Variable globale pour la musique de fond
musique_fond = None

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

def creation_elt_jeu():
    """
    Crée les éléments de l'interface utilisateur du jeu, comme la fenêtre d'information et le timer.

    Returns:
        dict: Dictionnaire contenant les éléments de l'interface utilisateur.
    """
    elt_jeu = Entity(name='elt_jeu', parent=camera.ui)

    fenetre_info = Entity(parent=elt_jeu, model='quad', color=color.rgba(240, 240, 240, 220), scale=(0.85, 0.5), position=(0, 0), enabled=False, shadow=True)
    fenetre_bordure = Entity(parent=elt_jeu, model='quad', color=color.hex('#8a0000'), scale=(0.87, 0.52), position=(0, 0), enabled=False,z=0.1)
    titre_text = Text(parent=fenetre_info,text="",scale=2,position=(0, 0.18),origin=(0, 0),color=color.hex("#8a0000"))
    info_text = Text(parent=fenetre_info,text="",scale=1.5,position=(0, 0.05),origin=(0, 0),color=color.hex("#8a0000"))
    timer_text = Text(parent=elt_jeu,text="0.00 s",position=(0.80, 0.47),scale=2, color=color.black, origin=(0.5, 0.5), font = "polices/Poppins-Bold.ttf")
    
    return {'elt_jeu': elt_jeu,'fenetre_info': fenetre_info,'titre_text': titre_text,'info_text': info_text,'timer_text': timer_text, 'fenetre_bordure': fenetre_bordure }


def afficher_feedback(message, couleur, duration=2):
    """
    Affiche un message de feedback à l'écran.

    Args:
        message (str): Message à afficher.
        couleur (color): Couleur du texte.
        duration (float): Durée d'affichage du message en secondes.
    """
    feedback = Text(text=message, color=couleur, scale=3, background=True, background_color=color.white, parent=camera.ui, position=(-0.5, 0))
    invoke(destroy, feedback, delay=duration)

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
    joueur = FirstPersonController(collider='box', speed=0, position=(0, 0, 0), parent=debut_jeu)
    joueur.camera_pivot.y = 1.6
    return joueur

def blocage_controle(joueur):
    """
    Bloque les contrôles du joueur.

    Args:
        joueur (FirstPersonController): Instance du joueur.
    """
    joueur.speed = 0
    joueur.mouse_sensitivity = Vec2(0, 0)
    joueur.rotation_y = 1.6
    joueur.camera_pivot.rotation_x = 0
    mouse.locked = False

def deblocage_controle(joueur):
    """
    Débloque les contrôles du joueur.

    Args:
        joueur (FirstPersonController): Instance du joueur.
    """
    joueur.speed = 10
    joueur.mouse_sensitivity = Vec2(100, 100)
    mouse.locked = True

def reglage_timer(debut_jeu, elt_jeu, joueur):
    """
    Configure et démarre le timer du jeu.

    Args:
        debut_jeu (Entity): Entité parente pour le timer.
        elt_jeu (dict): Dictionnaire des éléments de l'interface utilisateur.
        joueur (FirstPersonController): Instance du joueur.

    Returns:
        tuple: (timer, update_timer) - Liste contenant le temps écoulé et l'entité de mise à jour du timer.
    """
    timer = [0]
    def update():
        timer[0] += time.dt
        elt_jeu['timer_text'].text = f"Timer: {timer[0]:.2f} s"
    update_timer = Entity(update=update, enabled=False, parent=debut_jeu)

    def depart_timer():
        timer[0] = 0
        update_timer.enabled = True
    invoke(depart_timer, delay=4)
    return timer, update_timer

def creation_tableaux(debut_jeu, oeuvres, textures, positions, on_click_callback, tableau_a_trouver):
    """
    Crée les entités des tableaux dans le jeu.

    Args:
        debut_jeu (Entity): Entité parente pour les tableaux.
        oeuvres (dict): Dictionnaire des œuvres.
        textures (dict): Dictionnaire des textures des œuvres.
        positions (list): Liste des positions des tableaux.
        on_click_callback (function): Fonction à appeler lors d'un clic sur un tableau.
        tableau_a_trouver (str): Titre du tableau à trouver.

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

    # Placer d'abord le tableau à trouver
    if tableau_a_trouver in textures:
        pos, rot = positions[pos_index]
        pos_index += 1

        hauteur = convertir_en_float(oeuvres[tableau_a_trouver].get('hauteur'), 3)  # 3 par défaut
        largeur = convertir_en_float(oeuvres[tableau_a_trouver].get('largeur'), 5)  # 5 par défaut

        r1 = largeur / 5
        r2 = hauteur / 3
        if r1 > r2:
            largeur = largeur / r1
            hauteur = hauteur / r1
        else:
            largeur = largeur / r2
            hauteur = hauteur / r2

        tableau_entity = Entity(model='quad', texture=textures[tableau_a_trouver], position=pos, rotation=rot, scale=(largeur, hauteur), collider='box', name=tableau_a_trouver, parent=debut_jeu, double_sided=True)
        tableau_entity.on_click = lambda e=tableau_entity: on_click_callback(e)
        tableaux[tableau_a_trouver] = tableau_entity

    # Placer les autres tableaux
    for titre, data in oeuvres.items():
        if titre == tableau_a_trouver:
            continue  # Déjà placé
        if pos_index >= len(positions):
            break
        pos, rot = positions[pos_index]
        pos_index += 1

        hauteur = convertir_en_float(data.get('hauteur'), 3)  # 3 par défaut
        largeur = convertir_en_float(data.get('largeur'), 5)  # 5 par défaut

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

def afficher_infos_tableaux(elt_jeu, oeuvres, tableau_a_trouver, on_answer, joueur):
    """
    Affiche les informations d'un tableau dans une fenêtre.

    Args:
        elt_jeu (dict): Dictionnaire des éléments de l'interface utilisateur.
        oeuvres (dict): Dictionnaire des œuvres.
        tableau_a_trouver (str): Titre du tableau à trouver.
        on_answer (function): Fonction à appeler lors de la sélection d'une réponse.
        joueur (FirstPersonController): Instance du joueur.
    """
    fenetre_info = elt_jeu['fenetre_info']
    fenetre_bordure = elt_jeu['fenetre_bordure']
    fenetre_bordure.enabled = True
    titre_text = elt_jeu['titre_text']
    info_text = elt_jeu['info_text']
    data = oeuvres[tableau_a_trouver]
    fenetre_info.name = tableau_a_trouver
    titre_text.text = f"Auteur : {data['auteur']}"
    info_text.text = f"{data.get('titre', '')}"

    date_oeuvre = str(data['date'].split('-')[0])
    reponses = [date_oeuvre[:2] + str(random.randint(0, 9)) + str(random.randint(0, 9)) for _ in range(2)]
    reponses.append(date_oeuvre)
    random.shuffle(reponses)

    for idx, rep in enumerate(reponses):
        Button(parent=fenetre_info, text=rep, scale=(0.3, 0.1), position=(0, -0.05 - idx * 0.15), color=color.hex("#8a0000"), text_color=color.white, on_click=Func(on_answer, rep))
    fenetre_info.enabled = True
    blocage_controle(joueur)

def gestion_reponse(rep, oeuvres, tableau_a_trouver, on_finish, timer, debut_jeu, trouve):
    """
    Gère la réponse du joueur et affiche un feedback.

    Args:
        rep (str): Réponse du joueur.
        oeuvres (dict): Dictionnaire des œuvres.
        tableau_a_trouver (str): Titre du tableau à trouver.
        on_finish (function): Fonction à appeler à la fin du jeu.
        timer (list): Liste contenant le temps écoulé.
        debut_jeu (Entity): Entité parente du jeu.
        trouve (bool): Indique si le joueur a trouvé le tableau.
    """
    global musique_fond
    data = oeuvres[tableau_a_trouver]
    annee_correcte = str(data['date'].split('-')[0])

    feedback_text = Text(parent=camera.ui, scale=2, position=(0, 0.2), origin=(0, 0), background=True, background_color=color.white)

    if rep == annee_correcte:
        feedback_text.text = "Bonne réponse !"
        feedback_text.color = color.green
        juste = True
    else:
        feedback_text.text = f"Mauvaise réponse ! La bonne réponse était {annee_correcte}"
        feedback_text.color = color.red
        juste = False

    invoke(destroy, feedback_text, delay=2)
    invoke(lambda: on_finish(timer, juste, trouve), delay=2)
    musique_fond.stop()
    destroy(debut_jeu)

def affichage_clique(e, tableau_a_trouver, oeuvres, elt_jeu, joueur, on_finish, timer, debut_jeu, mauvais_clics):
    """
    Gère l'interaction avec les tableaux.

    Args:
        e (Entity): Entité du tableau cliqué.
        tableau_a_trouver (str): Titre du tableau à trouver.
        oeuvres (dict): Dictionnaire des œuvres.
        elt_jeu (dict): Dictionnaire des éléments de l'interface utilisateur.
        joueur (FirstPersonController): Instance du joueur.
        on_finish (function): Fonction à appeler à la fin du jeu.
        timer (list): Liste contenant le temps écoulé.
        debut_jeu (Entity): Entité parente du jeu.
        mauvais_clics (list): Liste contenant le nombre de mauvais clics.
    """
    if e.name == tableau_a_trouver:
        mouse.locked = False
        trouve = True
        afficher_infos_tableaux(elt_jeu, oeuvres, tableau_a_trouver, lambda rep: gestion_reponse(rep, oeuvres, tableau_a_trouver, on_finish, timer, debut_jeu, trouve), joueur)
    else:
        mauvais_clics[0] += 1
        afficher_feedback(f"Mauvaise tentative ({mauvais_clics[0]}/3)", color.orange, duration=1)
        if mauvais_clics[0] >= 3:
            destroy(debut_jeu)
            trouve = False
            musique_fond.stop()
            on_finish(timer, juste=False, trouve=False)

def jeu_principal_speedrun(on_finish, points_initial=0, timer_initial=0):
    """
    Fonction principale du mode speedrun. Initialise le jeu, charge les ressources,
    et démarre la boucle principale.

    Args:
        on_finish (function): Fonction à appeler à la fin du jeu.
        points_initial (int): Points initiaux (par défaut 0).
        timer_initial (int): Temps initial (par défaut 0).
    """
    global musique_fond
    debut_jeu = Entity(name='debut_jeu')
    oeuvres = chargement_oeuvres()
    textures = chargement_textures(oeuvres)
    tableau_a_trouver = random.choice(list(textures.keys()))
    mauvais_clics = [0]  # Utilisation d'une liste pour permettre la modification
    elt_jeu = creation_elt_jeu()

    terrain_actuel = {'num': 1, 'terrain': None, 'collider': None}
    terrain_actuel['terrain'], terrain_actuel['collider'] = chargement_modele(debut_jeu, 1)

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
    blocage_controle(joueur)
    timer, update_timer = reglage_timer(debut_jeu, elt_jeu, joueur)

    tableaux_actuel = creation_tableaux(debut_jeu, oeuvres, textures, positions_etage1, lambda e: affichage_clique(e, tableau_a_trouver, oeuvres, elt_jeu, joueur, on_finish, timer, debut_jeu, mauvais_clics), tableau_a_trouver)
    folder = "../assets/image"
    chemin_ascensceur = os.path.join(folder, "ascensceur.jpg")
    ascenseur = load_texture(chemin_ascensceur)
    bouton_etage = Button(parent=debut_jeu, model='quad', texture=ascenseur, rotation=Vec3(0, 90, 0), position=(4.49, 2.5, 0), scale=(5, 5, 0.1), on_click=lambda: changer_etage(), double_sided=True, highlight_color=color.white)

    def changer_etage():
        nonlocal tableaux_actuel
        for tableau in tableaux_actuel.values():
            destroy(tableau)
        if terrain_actuel['num'] == 1:
            destroy(terrain_actuel['terrain'])
            destroy(terrain_actuel['collider'])
            terrain_actuel['terrain'], terrain_actuel['collider'] = chargement_modele(debut_jeu, 2)
            terrain_actuel['num'] = 2
            tableaux_actuel = creation_tableaux(debut_jeu, oeuvres, textures, positions_etage2, lambda e: affichage_clique(e, tableau_a_trouver, oeuvres, elt_jeu, joueur, on_finish, timer, debut_jeu, mauvais_clics), tableau_a_trouver)
        else:
            destroy(terrain_actuel['terrain'])
            destroy(terrain_actuel['collider'])
            terrain_actuel['terrain'], terrain_actuel['collider'] = chargement_modele(debut_jeu, 1)
            terrain_actuel['num'] = 1
            tableaux_actuel = creation_tableaux(debut_jeu, oeuvres, textures, positions_etage1, lambda e: affichage_clique(e, tableau_a_trouver, oeuvres, elt_jeu, joueur, on_finish, timer, debut_jeu, mauvais_clics), tableau_a_trouver)
    joueur.position = (0, 0, 0)
    fenetre_tableau = Entity(parent=elt_jeu['elt_jeu'], model="quad", color=color.white, position=(0, 0), enabled=True, texture=textures.get(tableau_a_trouver, "white_cube"))
    musique_fond = Audio("../assets/musique/speedrun.mp3", loop=True, autoplay=True)

    def reduire_fenetre():
        fenetre_tableau.animate_scale((0.2, 0.2), duration=1)
        fenetre_tableau.animate_position((-0.75, 0.35), duration=1)
        fenetre_tableau.color = color.white66
        invoke(lambda: deblocage_controle(joueur), delay=1)

    invoke(reduire_fenetre, delay=4)
    return debut_jeu

def main():
    """
    Fonction principale du programme. Initialise l'application Ursina et démarre le mode speedrun.
    """
    app = Ursina()

    def on_finish(timer, juste):
        if juste:
            print(f"Partie terminée en {timer[0]:.2f} s. Bravo !")
        else:
            print(f"Partie terminée en {timer[0]:.2f} s. Mauvaise réponse.")

    jeu_principal_speedrun(on_finish)
    app.run()
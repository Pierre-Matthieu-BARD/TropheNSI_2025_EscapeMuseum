from ursina import *
from exploration import jeu_principal_exploration
from speedrun import jeu_principal_speedrun
import sqlite3
from ursina.audio import Audio
import math

# Connexion à la base de données SQLite
connexion = sqlite3.connect(r'sources\data\musee.db')
curseur = connexion.cursor()

# Création de la table 'score' si elle n'existe pas
curseur.execute('''
    CREATE TABLE IF NOT EXISTS score (
        nom TEXT,
        score INTEGER
    )
''')
connexion.commit()
print("Base de données initialisée")

# Variable globale pour la musique du menu
musique_menu = None

def afficher_leaderboard():
    """
    Affiche le leaderboard avec les trois meilleurs scores enregistrés dans la base de données.
    Crée une interface utilisateur avec un fond noir, une fenêtre blanche, et un texte indiquant les scores.
    Un bouton "Retour" permet de revenir au menu principal.
    """
    global musique_menu
    leaderboard_fond = Entity(parent=camera.ui, model="quad", color=color.black, scale=(2, 1), position=(0, 0))
    leaderboard_fenetre = Entity(parent=camera.ui, model="quad", texture="white_cube", color=color.white, scale=(0.7, 0.65), position=(0, 0))
    Text(parent=leaderboard_fenetre, text="LEADERBOARD", font='../polices/Poppins-Bold.ttf', position=(0, 0.27), color=color.hex("#8a0000"), scale=2.5, origin=(0, 0), background=True, background_color=color.white)
    logo_leaderboard = Entity(parent=camera.ui, model="quad", texture="../assets/image/Escape.png", scale=(0.3, 0.3), position=(-0.75, 0.4))

    # Récupération des trois meilleurs scores
    curseur.execute("SELECT nom, score FROM score ORDER BY score DESC LIMIT 3")
    scores = curseur.fetchall()

    y_offset = 0.06
    start_y = 0.15

    # Affichage des scores
    for i, (nom, score) in enumerate(scores):
        ligne = f"{i+1}. {nom} - {score}"
        Text(parent=leaderboard_fenetre, text=ligne, font='../polices/Poppins-Bold.ttf', position=(0, start_y - i * y_offset), color=color.black, scale=1.3, origin=(0, 0))

    def retour_menu():
        """Fonction pour revenir au menu principal."""
        destroy(leaderboard_fenetre)
        destroy(leaderboard_fond)
        destroy(logo_leaderboard)
        afficher_menu_principal()
    Button(parent=leaderboard_fenetre, text="Retour", scale=(0.3, 0.1), position=(0, -0.25), color=color.hex("#8a0000"), on_click=retour_menu, highlight_color=color.hex("#5f0303"))

    # Animation d'apparition de la fenêtre
    leaderboard_fenetre.scale = (0, 0)
    leaderboard_fenetre.animate_scale((0.7, 0.65), duration=0.01, curve=curve.out_back)

def afficher_menu_principal():
    """
    Affiche le menu principal du jeu. Crée une interface utilisateur avec un fond noir, un logo,
    des images de règles et de commandes, ainsi que des boutons pour accéder aux différents modes de jeu
    (SpeedRun, Exploration) et au leaderboard. La musique du menu est également jouée.
    """
    global musique_menu
    menu_fenetre = Entity(parent=camera.ui, model="quad", texture="white_cube", color=color.black, scale=(2, 1), position=(0, 0))
    logo = Entity(parent=camera.ui, model="quad", texture="../assets/image/Escape.png", scale=(0.3, 0.3), position=(-0.75, 0.4), z=-1)
    regles_image = Entity(parent=camera.ui, model="quad", texture="../assets/image/menu.png", scale=(1, 1), position=(-0.3, -0.2), z=-1)
    ligne_haut = Entity(parent=camera.ui, model="quad", texture="../assets/image/ligne_haut.png", scale=(1.1, 0.06), position=(0.21, 0.4), z=-1)
    ligne_droite = Entity(parent=camera.ui, model="quad", texture="../assets/image/ligne_droite.png", scale=(0.06, 0.8), position=(0.8, -0.02), z=-1)

    commandes = Entity(parent=camera.ui,model="quad",texture="../assets/image/commandes.png",scale=(0.55, 1.05),position=(0.48, -0.23),z=-1,  )
    musique_menu = Audio("../assets/musique/menu.mp3", autoplay=True, loop=True)

    # Bouton pour le mode SpeedRun
    Button(parent=menu_fenetre,text="SpeedRun",text_color=color.black,scale=(0.15, 0.1),position=(-0.28, -0.35),color=color.white,highlight_color=color.hex("#8a0000"),z=-2,on_click=lambda: (destroy(menu_fenetre), destroy(logo), destroy(regles_image), destroy(ligne_haut), destroy(ligne_droite), destroy(commandes), jeu_principal_speedrun(menu_principal, 0, 0), musique_menu.stop()))
    # Bouton pour le mode Exploration
    Button(parent=menu_fenetre,text="Exploration",text_color=color.black,scale=(0.15, 0.1),position=(-0.02, -0.35),color=color.white,highlight_color=color.hex("#8a0000"),z=-2,on_click=lambda: (destroy(menu_fenetre), destroy(logo), destroy(regles_image), destroy(ligne_haut), destroy(ligne_droite), destroy(commandes), jeu_principal_exploration(), musique_menu.stop()))
    # Bouton pour afficher le leaderboard
    Button(parent=menu_fenetre,text="Leaderboard",text_color=color.black,scale=(0.15, 0.1),position=(0.24, -0.23),color=color.white,highlight_color=color.hex("#8a0000"),z=-2,on_click=lambda: (destroy(menu_fenetre), destroy(logo), destroy(regles_image), destroy(ligne_haut), destroy(ligne_droite), destroy(commandes), afficher_leaderboard()))
    
def demander_nom_joueur(timer, juste):
    """
    Demande au joueur d'entrer son nom après avoir terminé une partie. Affiche une fenêtre avec un champ
    de saisie pour le nom du joueur. Si le nom est valide, le score est calculé et enregistré dans la
    base de données. Un bouton "Valider" permet de confirmer la saisie.

    Args:
        timer (float): Le temps écoulé pendant la partie, utilisé pour calculer le score.
        juste (bool): Indique si le joueur a réussi la partie ou non.
    """
    fond_noire = Entity(parent=camera.ui, model="quad",color=color.black,scale=(2, 1),position=(0, 0))
    score_fenetre = Entity(parent=camera.ui,model="quad",texture="white_cube",color=color.white,scale=(0.7, 0.65),position=(0, 0))
    Text(parent=score_fenetre,text="Entrez votre nom :",position=(0, 0.27),color=color.hex("#8a0000"),scale=2.5,origin=(0, 0),background=True,background_color=color.white)
    nom_input = InputField(parent=score_fenetre,scale=(0.4, 0.1),position=(0, 0),color=color.black,)
    logo_score_fenetre = Entity(parent=camera.ui,model="quad",texture="../assets/image/Escape.png",scale=(0.3, 0.3),position=(-0.75, 0.4))
    error_text = Text(parent=score_fenetre,text="",scale=1,position=(-0.175, 0.15),color=color.red)
    
    def calculer_score_log(timer):
        """
        Calcule le score en fonction du temps écoulé en utilisant une fonction logarithmique.

        Args:
            timer (float): Le temps écoulé pendant la partie.

        Returns:
            int: Le score calculé.
        """
        global points
        a = -100  # Amplitude de la réduction des points
        b = 1.5   # Vitesse de réduction
        c = 1     # Évite les valeurs infinies ou négatives
        d = 1000  # Score de base

        points = a * math.log(b * timer + c) + d
        points = max(0, round(points))  # Assurer que le score n'est pas négatif
        return points

    def valider_nom(timer):
        """
        Valide le nom du joueur et enregistre le score dans la base de données.

        Args:
            timer (float): Le temps écoulé pendant la partie.
        """
        global points
        points = calculer_score_log(timer)
        nom = nom_input.text
        if nom.strip() == "":
            error_text.text = "Le nom ne peut pas être vide."
            return    
        curseur.execute("INSERT INTO score (nom, score) VALUES (?, ?)", (nom, points))
        connexion.commit()
        print("entrée ajoutée à la base de données")
        destroy(score_fenetre)
        destroy(logo_score_fenetre)
        destroy(fond_noire)
        afficher_menu_principal()

    Button(parent=score_fenetre,text="Valider",scale=(0.3, 0.1),position=(0, -0.25),color=color.hex("#8a0000"),highlight_color=color.hex("#5f0303"),on_click=lambda: valider_nom(timer))

def menu_principal(timer=0, juste=False, trouve=True):
    """
    Fonction principale du menu. Nettoie l'interface utilisateur actuelle et affiche soit le menu principal,
    soit la fenêtre de saisie du nom du joueur en fonction du temps écoulé et de l'état de la partie.

    Args:
        timer (float, optional): Le temps écoulé pendant la partie. Par défaut à 0.
        juste (bool, optional): Indique si le joueur a réussi la partie. Par défaut à False.
        trouve (bool, optional): Indique si le joueur a trouvé la solution. Par défaut à True.
    """
    for child in list(camera.ui.children):
        destroy(child)
    if isinstance(timer, list) and timer:
        timer = timer[0]  # Prendre le premier élément
    if isinstance(timer, (str, int, float)):
        timer = float(timer)  # Conversion sécurisée si c'est un nombre ou une chaîne convertible
    if timer > 0:
        if trouve:
            demander_nom_joueur(timer, juste)
        else:
            afficher_menu_principal()  # DEBUG
    else:
        afficher_menu_principal()

def fermer_bd():
    """
    Ferme la connexion à la base de données. Cette fonction est appelée lors de la fermeture de
    l'application pour s'assurer que la connexion à la base de données est correctement fermée.
    """
    connexion.close()
    print("Connexion à la base de données fermée.")

application.quit_event = fermer_bd

def main():
    global app
    
    # Définir le dossier des assets correctement
    base_path = Path(__file__).parent
    application.asset_folder = base_path
    
    app = Ursina()
    afficher_menu_principal()
    app.run()
if __name__ == '__main__':
    main()
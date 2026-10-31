# =====================================================================
#  SIMULER DES PARTIES ET ENREGISTRER LES DONNÉES
# =====================================================================
#  Ce script fait jouer plein de parties entre bots avec ton moteur,
#  et il enregistre une ligne par joueur et par manche dans manches.csv.
#  Ce fichier, c'est tes données pour la phase 1 (Pandas) et la phase 2 (IA).
#
#  Lancement : python simuler.py
#  (il faut que tarot.py soit dans le même dossier)
# =====================================================================

import csv
import io
import random
from contextlib import redirect_stdout

import tarot   # ton moteur de jeu

NB_PARTIES = 3000   # avec les bots bon sens, les parties durent plus longtemps : 3000 suffisent
NB_JOUEURS = 4

lignes = []          # toutes les lignes du tableau, qu'on écrira à la fin
numero_partie = 0    # pour savoir à quelle partie appartient chaque ligne
numero_manche = 0    # numéro de la manche dans la partie en cours


# ---------------------------------------------------------------------
# On "espionne" la manche pour noter ce qui se passe, SANS toucher à tarot.py.
# On garde la vraie méthode jouer() de côté, et on la remplace par une version
# qui fait exactement pareil, mais qui note les infos au passage.
# ---------------------------------------------------------------------
jouer_original = tarot.Manche.jouer


def jouer_en_notant(manche):
    global numero_manche
    numero_manche = numero_manche + 1

    # on note les vies de chacun AVANT la manche
    vies_avant = {}
    for joueur in manche.joueurs:
        vies_avant[joueur.nom] = joueur.vies

    # pareil pour la distribution : on note la main de chacun juste après,
    # parce que pendant la manche les cartes partent sur la table
    distribution_originale = manche.distribution
    mains = {}

    def distribution_en_notant():
        distribution_originale()
        for joueur in manche.joueurs:
            mains[joueur.nom] = list(joueur.main)

    manche.distribution = distribution_en_notant

    # on joue la manche normalement
    jouer_original(manche)

    # la position de chacun dans l'ordre des annonces (1 = premier, dernier = donneur)
    ordre = manche.ordre()

    for joueur in manche.joueurs:
        main = mains[joueur.nom]
        atouts = []
        for carte in main:
            if not carte.est_excuse():
                atouts.append(carte.valeur)
        a_excuse = len(atouts) < len(main)
        position = ordre.index(joueur) + 1

        lignes.append({
            "partie": numero_partie,
            "manche": numero_manche,
            "nb_joueurs": len(manche.joueurs),
            "nb_cartes": manche.nb_carte,
            "joueur": joueur.nom,
            "position_annonce": position,
            "est_donneur": joueur is manche.donneur,
            # la main, écrite comme "3 12 19 Excuse"
            "main": " ".join(c.texte() for c in main),
            "plus_forte": max(atouts) if atouts else 0,
            "a_le_21": 21 in atouts,
            "a_excuse": a_excuse,
            "nb_atouts_sup_15": len([v for v in atouts if v > 15]),
            "somme_atouts": sum(atouts),
            "annonce": joueur.pli_annonce,
            "plis_faits": joueur.pli_fait,
            "vies_avant": vies_avant[joueur.nom],
            "vies_perdues": abs(joueur.pli_annonce - joueur.pli_fait),
        })


tarot.Manche.jouer = jouer_en_notant


# ---------------------------------------------------------------------
# On lance les parties
# ---------------------------------------------------------------------
random.seed(42)   # même graine = mêmes parties à chaque lancement (résultats reproductibles)
noms = ["Awa", "Kofi", "Zaïna", "Malik", "Nadia", "Sékou"][:NB_JOUEURS]

for i in range(NB_PARTIES):
    numero_partie = i + 1
    numero_manche = 0
    partie = tarot.Partie(noms)
    # redirect_stdout cache tous les print du moteur, sinon ça afficherait des millions de lignes
    with redirect_stdout(io.StringIO()):
        partie.jouer()
    if numero_partie % 1000 == 0:
        print(numero_partie, "parties jouées...")

# ---------------------------------------------------------------------
# On écrit le tableau dans manches.csv
# ---------------------------------------------------------------------
with open("manches.csv", "w", newline="", encoding="utf-8") as f:
    ecrivain = csv.DictWriter(f, fieldnames=list(lignes[0].keys()))
    ecrivain.writeheader()
    ecrivain.writerows(lignes)

print("Terminé :", len(lignes), "lignes enregistrées dans manches.csv")

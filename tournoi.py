# =====================================================================
#  TOURNOI ENTRE DEUX STRATÉGIES DE BOT
# =====================================================================
#  Pour savoir si une nouvelle règle rend le bot meilleur, on le fait
#  jouer plein de parties contre l'ancienne version, et on compte qui gagne.
#  À 2 contre 2, une stratégie aussi forte que l'autre gagne ~50 % des parties.
#
#  Lancement : python tournoi.py
# =====================================================================

import io
import random
from contextlib import redirect_stdout

import tarot

STRATEGIE_A = "malin"
STRATEGIE_B = "bon_sens"
NB_PARTIES = 4000

victoires = {STRATEGIE_A: 0, STRATEGIE_B: 0}
vies_perdues = {STRATEGIE_A: [], STRATEGIE_B: []}

# on espionne la fin de chaque manche pour noter les vies perdues (sans toucher à tarot.py)
retirer_vies_original = tarot.Manche.retirer_vies


def retirer_vies_en_notant(manche):
    for joueur in manche.joueurs:
        vies_perdues[joueur.strategie].append(abs(joueur.pli_annonce - joueur.pli_fait))
    retirer_vies_original(manche)


tarot.Manche.retirer_vies = retirer_vies_en_notant

for i in range(NB_PARTIES):
    random.seed(i)
    # 2 contre 2, assis en alternance (A B A B), et on échange les places une partie sur deux
    # pour que personne soit avantagé par sa place autour de la table
    if i % 2 == 0:
        strategies = {"Awa": STRATEGIE_A, "Kofi": STRATEGIE_B, "Zaïna": STRATEGIE_A, "Malik": STRATEGIE_B}
    else:
        strategies = {"Awa": STRATEGIE_B, "Kofi": STRATEGIE_A, "Zaïna": STRATEGIE_B, "Malik": STRATEGIE_A}
    partie = tarot.Partie(["Awa", "Kofi", "Zaïna", "Malik"], strategies=strategies)
    with redirect_stdout(io.StringIO()):   # on cache les print du moteur
        gagnants = partie.jouer()
    for joueur in gagnants:
        # en cas d'égalité, chaque gagnant récupère une part de la victoire
        victoires[joueur.strategie] = victoires[joueur.strategie] + 1 / len(gagnants)

for strategie in [STRATEGIE_A, STRATEGIE_B]:
    taux = 100 * victoires[strategie] / NB_PARTIES
    moyenne = sum(vies_perdues[strategie]) / len(vies_perdues[strategie])
    print(strategie, ": gagne", round(taux, 1), "% des parties, perd", round(moyenne, 2), "vie par manche en moyenne")

# Attention au hasard : sur 4000 parties, un écart de 1 ou 2 points peut être de la chance.
# Pour être sûr qu'une règle aide, il faut un écart net, ou plus de parties.

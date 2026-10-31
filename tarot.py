# =====================================================================
#  TAROT AFRICAIN - le moteur du jeu
# =====================================================================
#  En gros, le fichier marche comme ça :
#   - Carte   : une carte du paquet (un atout de 1 à 21, ou l'Excuse)
#   - Joueur  : un joueur, avec ses vies, sa main, son annonce et ses plis
#   - Manche  : une donne complète (on distribue, on annonce, on joue
#               tous les plis, et on retire les vies)
#   - Partie  : enchaîne les manches jusqu'à ce qu'il en reste qu'un
#  Tout en bas, y'a les fonctions pour toi quand tu joues au clavier,
#  et le lancement du jeu.
# =====================================================================

import random   # pour mélanger le paquet et faire jouer les bots au hasard


# =====================================================================
#  CARTE
# =====================================================================
class Carte:
    def __init__(self, valeur):
        # la valeur c'est soit un nombre de 1 à 21, soit le mot "excuse"
        self.valeur = valeur

    def est_excuse(self):
        # renvoie True si c'est l'Excuse, False sinon
        # du coup partout dans le code on écrit carte.est_excuse()
        # au lieu de carte.valeur == "excuse", c'est plus lisible
        return self.valeur == "excuse"

    def texte(self):
        # sert juste à afficher la carte à l'écran
        # str(...) transforme le nombre en texte, genre 7 devient "7"
        if self.est_excuse():
            return "Excuse"
        return str(self.valeur)


# =====================================================================
#  JOUEUR
# =====================================================================
class Joueur:
    def __init__(self, nom, humain=False, strategie="malin"):
        # le nom on le reçoit, c'est le seul truc qui change d'un joueur à l'autre
        self.nom = nom
        # humain=False veut dire : si on précise rien, c'est un bot
        # si humain vaut True, c'est toi qui joues au clavier
        self.humain = humain
        # pour un bot : "hasard" (joue n'importe comment), "bon_sens" (tes règles de base)
        # ou "malin" (bon sens + mémoire des cartes tombées, total des annonces, vol de pli)
        self.strategie = strategie
        # tout le reste c'est pareil pour tout le monde au départ
        self.vies = 10
        self.main = []            # les cartes qu'il a en main, vide au début
        self.pli_annonce = None   # None = il a pas encore annoncé
        self.pli_fait = 0

    def nouvelle_manche(self):
        # appelée au début de chaque manche
        # on remet à zéro tout ce qui dure qu'une manche :
        # la main, l'annonce, et les plis faits
        # par contre on touche PAS aux vies, elles durent toute la partie
        self.main = []
        self.pli_annonce = None
        self.pli_fait = 0

    def annoncer(self, manche, interdite):
        # le joueur dit combien de plis il pense faire
        # "manche" c'est la manche en cours, ça lui permet de savoir
        #   combien y'a de cartes, ce que les autres ont annoncé, etc.
        # "interdite" c'est le nombre qu'il a pas le droit de dire
        #   (ou None si y'a pas d'interdiction)
        if self.humain:
            # c'est toi : on te demande au clavier (fonction tout en bas)
            self.pli_annonce = annonce_humain(self, manche, interdite)
        elif self.strategie in ("bon_sens", "malin"):
            # c'est un bot qui applique tes règles (voir plus bas)
            self.pli_annonce = self.annonce_bon_sens(manche, interdite)
        else:
            # c'est un bot au hasard : il fait la liste de tout ce qu'il peut annoncer...
            possibles = []
            for n in range(manche.nb_carte + 1):   # de 0 à nb_carte inclus
                if n != interdite:                 # ... sauf la valeur interdite
                    possibles.append(n)
            # ... et il en choisit un au pif
            self.pli_annonce = random.choice(possibles)
        return self.pli_annonce

    def jouer(self, manche):
        # le joueur pose une carte
        # ça renvoie DEUX choses : la carte posée, et sa valeur
        # (la valeur c'est la même que la carte, sauf pour l'Excuse : 0 ou 22)

        # 1) on choisit quelle carte poser
        if self.humain:
            carte = choix_carte_humain(self, manche)   # c'est toi qui choisis
        elif self.strategie in ("bon_sens", "malin"):
            carte = self.carte_bon_sens(manche)        # le bot applique tes règles
        else:
            carte = random.choice(self.main)           # le bot pose au pif

        # 2) on enlève la carte de la main, elle est sur la table maintenant
        self.main.remove(carte)

        # 3) on renvoie la carte et sa valeur
        if not carte.est_excuse():
            # carte normale : la valeur c'est juste son nombre
            return carte, carte.valeur
        # si on arrive ici c'est l'Excuse : on choisit 0 ou 22
        if self.humain:
            return carte, choix_excuse_humain()
        if self.strategie in ("bon_sens", "malin"):
            # s'il lui manque des plis, il la joue à 22 pour gagner, sinon à 0 pour perdre
            if self.plis_manquants() > 0:
                return carte, 22
            return carte, 0
        return carte, random.choice([0, 22])

    # =================================================================
    #  LE BOT « BON SENS » : TES RÈGLES, TRADUITES EN CODE
    # =================================================================
    def plis_manquants(self):
        # combien de plis il lui reste à faire pour tomber pile sur son annonce
        # positif = il en veut encore ; 0 ou négatif = il veut plus en prendre
        return self.pli_annonce - self.pli_fait

    def annonce_bon_sens(self, manche, interdite):
        nb_joueurs = len(manche.joueurs)

        if manche.nb_carte == 1:
            # MANCHE À 1 CARTE : on voit les cartes des autres, pas la sienne
            # on regarde la plus forte carte visible (l'Excuse visible = perdu, il la jouera à 22)
            plus_forte_visible = 0
            for autre in manche.joueurs:
                if autre is not self:
                    if autre.main[0].est_excuse():
                        plus_forte_visible = 22
                    elif autre.main[0].valeur > plus_forte_visible:
                        plus_forte_visible = autre.main[0].valeur
            # les cartes qui battent la plus forte visible : de plus_forte+1 à 21, plus l'Excuse
            cartes_gagnantes = 22 - plus_forte_visible
            # ma carte est une des cartes que je vois pas, au hasard
            cartes_invisibles = 22 - (nb_joueurs - 1)
            chance = cartes_gagnantes / cartes_invisibles
            if chance >= 0.5:
                annonce = 1
            else:
                annonce = 0
        else:
            # PLUSIEURS CARTES : un pli par carte au-dessus d'un seuil
            # le seuil dépend du nombre de cartes en jeu (ta remarque) :
            # 20 cartes en jeu → seuil 16, 8 cartes en jeu → seuil 13
            cartes_en_jeu = nb_joueurs * manche.nb_carte
            seuil = 11 + cartes_en_jeu / 4
            annonce = 0
            for carte in self.main:
                # l'Excuse compte pas : il la garde pour la fin, pour ajuster
                if not carte.est_excuse() and carte.valeur > seuil:
                    annonce = annonce + 1

        # si l'annonce choisie est interdite, on se décale d'un cran
        # en priorité vers le bas, parce que c'est plus facile de ne pas faire un pli
        if annonce == interdite:
            if annonce > 0:
                annonce = annonce - 1
            else:
                annonce = annonce + 1
        return annonce

    def carte_bon_sens(self, manche):
        # on met l'Excuse de côté : il la garde pour le dernier tour (ta règle)
        cartes = []
        for carte in self.main:
            if not carte.est_excuse():
                cartes.append(carte)
        if len(cartes) == 0:
            return self.main[0]   # il reste que l'Excuse, il la joue

        # on trie ses cartes de la plus petite à la plus grosse
        cartes.sort(key=lambda c: c.valeur)
        plus_petite = cartes[0]
        plus_grosse = cartes[-1]

        # ce qui est déjà sur la table dans ce pli, et qui gagne pour l'instant
        meilleure_sur_table = None
        gagnant_actuel = None
        for joueur, carte, valeur in manche.pli_en_cours:
            if meilleure_sur_table is None or valeur > meilleure_sur_table:
                meilleure_sur_table = valeur
                gagnant_actuel = joueur
        j_ouvre = (meilleure_sur_table is None)
        je_suis_dernier = (len(manche.pli_en_cours) == len(manche.joueurs) - 1)

        # le bot « malin » ajoute tes 3 règles en plus (voir plus bas)
        if self.strategie == "malin":
            choix = self.carte_malin(manche, cartes, meilleure_sur_table, gagnant_actuel, j_ouvre, je_suis_dernier)
            if choix is not None:
                return choix
            # si carte_malin a rien de spécial à proposer, on applique les règles de base ci-dessous

        if self.plis_manquants() <= 0:
            # IL VEUT PLUS DE PLI
            if j_ouvre:
                # il ouvre : sa plus petite carte
                return plus_petite
            # sinon : sa plus grosse carte qui prend pas le pli
            perdantes = []
            for carte in cartes:
                if carte.valeur < meilleure_sur_table:
                    perdantes.append(carte)
            if perdantes:
                return perdantes[-1]   # la plus grosse des perdantes
            return plus_petite         # aucune ne perd : la plus petite, en espérant qu'un suivant prenne

        # IL LUI MANQUE DES PLIS
        if j_ouvre:
            # il ouvre : petite carte, parce qu'en premier on se fait voler le pli (ta règle)
            return plus_petite
        gagnantes = []
        for carte in cartes:
            if carte.valeur > meilleure_sur_table:
                gagnantes.append(carte)
        if not gagnantes:
            return plus_petite         # il peut pas prendre : il garde ses grosses
        if je_suis_dernier:
            return gagnantes[0]        # dernier : la plus petite qui suffit à prendre
        return gagnantes[-1]           # pas dernier : sa plus grosse, pour pas se faire voler

    # =================================================================
    #  LE BOT « MALIN » : bon sens + tes 3 règles en plus
    # =================================================================
    def cartes_dehors(self, manche):
        # RÈGLE 1 : retenir ce qui est tombé
        # renvoie les valeurs des cartes que d'autres joueurs ont peut-être encore en main :
        # tout le paquet, moins ma main, moins tout ce qui est déjà tombé dans la manche
        # ("excuse" est dans la liste si elle est pas encore sortie et que je l'ai pas)
        connues = []
        for carte in self.main:
            connues.append(carte.valeur)
        for joueur, carte, valeur in manche.carte_tombee:
            connues.append(carte.valeur)
        dehors = []
        for v in list(range(1, 22)) + ["excuse"]:
            if v not in connues:
                dehors.append(v)
        return dehors

    def est_maitresse(self, carte, manche):
        # une carte est « maîtresse » si aucune carte encore dehors peut la battre
        # (l'Excuse dehors peut toujours la battre en étant jouée à 22)
        for v in self.cartes_dehors(manche):
            if v == "excuse" or v > carte.valeur:
                return False
        return True

    def tension(self, manche):
        # RÈGLE 2 : le total des annonces
        # total des annonces moins le nombre de cartes :
        #  - négatif → sous-annonce : y'a des plis en trop, tout le monde va chercher à les refiler
        #  - positif → sur-annonce : pas assez de plis pour tout le monde, ça va se battre
        total = 0
        for joueur, annonce in manche.annonces:
            total = total + annonce
        return total - manche.nb_carte

    def carte_malin(self, manche, cartes, meilleure_sur_table, gagnant_actuel, j_ouvre, je_suis_dernier):
        # renvoie une carte si une des 3 règles s'applique, sinon None (→ règles de base)
        manquants = self.plis_manquants()
        plis_restants = len(self.main)          # un pli par carte qu'il me reste
        gagnantes = []
        for carte in cartes:
            if not j_ouvre and carte.valeur > meilleure_sur_table:
                gagnantes.append(carte)

        if manquants > 0:
            # ---------- IL LUI MANQUE DES PLIS ----------

            # RÈGLE 1 : s'il ouvre avec une carte maîtresse et que ça se bat (sur-annonce),
            # il la joue tout de suite : pli garanti, personne peut la battre
            if j_ouvre:
                maitresses = [c for c in cartes if self.est_maitresse(c, manche)]
                if maitresses and self.tension(manche) > 0:
                    return maitresses[0]
                return None

            # RÈGLE 3 : voler. Celui qui gagne le pli en ce moment en a besoin,
            # et je peux le battre → je le prends : je gagne un pli ET il en perd un
            if gagnantes and gagnant_actuel.plis_manquants() > 0:
                if je_suis_dernier:
                    return gagnantes[0]
                # pas dernier : la plus petite carte qui est maîtresse si y'en a une, sinon la plus grosse
                for carte in gagnantes:
                    if self.est_maitresse(carte, manche):
                        return carte
                return gagnantes[-1]

            # RÈGLE 2 + 3 testée puis RETIRÉE : « le gagnant actuel veut pas ce pli,
            # je lui laisse pour qu'il se le mange, je me rattraperai plus tard ».
            # Résultat sur 3000 parties : le bot gagnait 46,8 % au lieu de 50 %.
            # En vrai, souvent on se rattrape pas, et on perd soi-même une vie.

            # pas dernier mais j'ai une carte gagnante maîtresse : la plus petite suffit, pas besoin de gâcher la plus grosse
            if gagnantes and not je_suis_dernier:
                for carte in gagnantes:
                    if self.est_maitresse(carte, manche):
                        return carte
            return None

        # ---------- IL VEUT PLUS DE PLI ----------
        # RÈGLE 1 : s'il ouvre, il évite d'ouvrir avec une carte maîtresse (pli forcé),
        # il prend la plus petite qui l'est pas
        if j_ouvre:
            non_maitresses = [c for c in cartes if not self.est_maitresse(c, manche)]
            if non_maitresses:
                return non_maitresses[0]
            return None

        # RÈGLE 2 : en sous-annonce, tout le monde refile ses grosses cartes.
        # s'il est obligé de prendre (aucune carte perdante), il prend avec sa PLUS GROSSE :
        # tant qu'à se faire avoir, il se débarrasse d'une carte dangereuse pour la suite
        perdantes = [c for c in cartes if c.valeur < meilleure_sur_table]
        if not perdantes and je_suis_dernier:
            return cartes[-1]
        return None


# =====================================================================
#  MANCHE
# =====================================================================
class Manche:
    def __init__(self, nombre_de_carte, joueurs, donneur):
        # ces 3 trucs on les connaît quand on crée la manche
        self.nb_carte = nombre_de_carte   # combien de cartes PAR joueur (5, 4, 3, 2 ou 1)
        self.joueurs = joueurs            # la liste des joueurs encore en vie
        self.donneur = donneur            # celui qui distribue

        # le paquet c'est toujours les mêmes 22 cartes, on le fabrique ici
        self.paquet = []
        for v in range(1, 22):            # de 1 à 21 (le 22 est exclu dans range)
            self.paquet.append(Carte(v))
        self.paquet.append(Carte("excuse"))

        # ça c'est vide au début et ça se remplit pendant la manche
        # chaque élément c'est une petite liste [joueur, carte, valeur jouée]
        self.carte_tombee = []    # toutes les cartes posées depuis le début de la manche
        self.pli_en_cours = []    # seulement les cartes du pli qu'on est en train de jouer
        # chaque élément c'est [joueur, annonce], dans l'ordre où ils ont annoncé
        self.annonces = []

    def distribution(self):
        # on mélange, puis on donne les cartes une par une comme en vrai
        random.shuffle(self.paquet)
        for tour in range(self.nb_carte):          # autant de tours de table que de cartes par joueur
            for joueur in self.joueurs:            # à chaque tour, une carte à chacun
                joueur.main.append(self.paquet[-1])   # on donne la carte du dessus...
                self.paquet.pop()                     # ... et on l'enlève du paquet

    def ordre(self, premier=None):
        # renvoie les joueurs dans l'ordre de jeu
        # - si on précise pas "premier" : on commence à gauche du donneur,
        #   et le donneur parle en dernier (c'est le cas des annonces et du 1er pli)
        #   ex : [Ramzy, Yanis, Inès, Hugo] avec Inès qui donne → [Hugo, Ramzy, Yanis, Inès]
        # - si on précise "premier" : on commence par lui, puis on tourne vers la gauche
        #   (c'est le cas des plis suivants : le gagnant du pli d'avant commence)
        if premier is None:
            a = self.joueurs.index(self.donneur) + 1    # la position juste après le donneur
        else:
            a = self.joueurs.index(premier)             # la position du premier joueur
        # on coupe la liste à cette position et on recolle les deux bouts
        return self.joueurs[a:] + self.joueurs[:a]

    # ------------------------------------------------------------------
    # CODÉE PAR RAMZY
    # ------------------------------------------------------------------
    def valeur_interdite(self, est_dernier):
        # renvoie le nombre que le joueur a PAS le droit d'annoncer,
        # ou None s'il y a pas d'interdiction

        # y'a que le dernier à annoncer qui a une interdiction
        if not est_dernier:
            return None

        # on additionne toutes les annonces déjà faites dans la manche
        # (même chose qu'une boucle : total = 0, puis total = total + annonce pour chaque paire)
        total = sum(annonce for joueur, annonce in self.annonces)

        # la valeur qui ferait tomber le total pile sur le nombre de cartes
        valeur = self.nb_carte - total

        # si elle est négative, personne peut l'annoncer de toute façon : pas d'interdiction
        if valeur < 0:
            return None

        return valeur
    # ------------------------------------------------------------------

    def tour_annonces(self):
        # tout le monde annonce, dans l'ordre (à gauche du donneur d'abord)
        ordre = self.ordre()
        for i in range(len(ordre)):
            joueur = ordre[i]
            # le dernier c'est celui qui est à la dernière position de la liste
            # (len(ordre) - 1, parce que les positions commencent à 0)
            est_dernier = (i == len(ordre) - 1)
            interdite = self.valeur_interdite(est_dernier)   # ta fonction !
            annonce = joueur.annoncer(self, interdite)
            self.annonces.append([joueur, annonce])          # on garde l'annonce en mémoire
            print("   " + joueur.nom + " annonce " + texte_plis(annonce))

    def jouer_pli(self, premier):
        # un pli : chacun pose une carte, la plus forte gagne
        # "premier" c'est celui qui ouvre le pli :
        # à gauche du donneur pour le 1er pli, puis le gagnant du pli d'avant
        # la méthode renvoie le gagnant, pour savoir qui ouvre le pli suivant
        self.pli_en_cours = []    # nouveau pli, la table est vide

        for joueur in self.ordre(premier):
            carte, valeur = joueur.jouer(self)   # le joueur pose sa carte
            # on note la carte posée dans le pli ET dans toute la manche
            self.pli_en_cours.append([joueur, carte, valeur])
            self.carte_tombee.append([joueur, carte, valeur])
            # on affiche ce qui s'est passé
            if carte.est_excuse():
                print("   " + joueur.nom + " pose l'Excuse, qui vaut " + str(valeur))
            else:
                print("   " + joueur.nom + " pose la carte " + carte.texte())

        # on cherche qui a posé la plus forte valeur
        # au départ on dit que c'est le premier qui a posé...
        gagnant = self.pli_en_cours[0][0]    # [0] = le premier élément, puis [0] = le joueur
        meilleure = self.pli_en_cours[0][2]  # [0] = le premier élément, puis [2] = la valeur
        # ... puis on regarde chaque carte posée, et si y'a mieux, on change de gagnant
        for joueur, carte, valeur in self.pli_en_cours:
            if valeur > meilleure:
                gagnant = joueur
                meilleure = valeur
        # le gagnant prend le pli
        gagnant.pli_fait = gagnant.pli_fait + 1
        print("   → " + gagnant.nom + " remporte le pli avec " + str(meilleure))
        # récap des plis faits après chaque pli
        textes = []
        for joueur in self.joueurs:
            textes.append(joueur.nom + " " + str(joueur.pli_fait) + "/" + str(joueur.pli_annonce))
        print("   Plis faits / annoncés : " + ", ".join(textes) + "\n")
        return gagnant

    def retirer_vies(self):
        # à la fin de la manche, chacun perd autant de vies que son écart
        # abs(...) c'est la valeur absolue : ça rend toujours positif
        # parce que annoncer 3 et en faire 1, ou annoncer 1 et en faire 3,
        # dans les deux cas tu t'es trompé de 2, donc tu perds 2 vies
        for joueur in self.joueurs:
            ecart = abs(joueur.pli_annonce - joueur.pli_fait)
            joueur.vies = joueur.vies - ecart
            print("   " + joueur.nom + " avait annoncé " + texte_plis(joueur.pli_annonce)
                  + ", en a fait " + str(joueur.pli_fait)
                  + " → perd " + str(ecart) + " vie(s), il lui en reste " + str(joueur.vies))

    def jouer(self):
        # la manche complète, dans l'ordre que t'avais décrit :
        for joueur in self.joueurs:
            joueur.nouvelle_manche()   # 0) chacun repart avec une main vide
        self.distribution()            # 1) on distribue
        print("\nANNONCES")
        self.tour_annonces()           # 2) tout le monde annonce
        # 3) on joue autant de plis que de cartes en main
        # le 1er pli est ouvert par le joueur à gauche du donneur...
        premier = self.ordre()[0]
        for tour in range(self.nb_carte):
            print("\nPLI " + str(tour + 1) + " sur " + str(self.nb_carte) + " - " + premier.nom + " commence")
            gagnant = self.jouer_pli(premier)
            # ... puis c'est le gagnant du pli qui ouvre le suivant
            premier = gagnant
        print("BILAN DE LA MANCHE")
        self.retirer_vies()            # 4) on compte et on retire les vies


# =====================================================================
#  PARTIE
# =====================================================================
class Partie:
    def __init__(self, nom_joueurs, nom_humain=None, strategies=None):
        # nom_joueurs : la liste des noms, dans l'ordre autour de la table
        # nom_humain  : ton nom si tu joues, None si c'est que des bots
        # strategies  : facultatif, pour choisir la stratégie de certains bots
        #               ex : {"Awa": "hasard"} → Awa joue au hasard, les autres en malin
        if strategies is None:
            strategies = {}
        self.joueurs = []
        for i in range(len(nom_joueurs)):
            nom = nom_joueurs[i]
            # humain vaut True seulement pour le joueur qui a ton nom
            humain = (nom == nom_humain)
            # .get(nom, "bon_sens") : la stratégie demandée pour ce nom, sinon "bon_sens"
            strategie = strategies.get(nom, "malin")
            self.joueurs.append(Joueur(nom, humain, strategie))

        # combien de cartes au départ ?
        # y'a que 22 cartes, donc il faut que tout le monde puisse être servi
        # 22 // nb_joueurs c'est la division entière (ex : 22 // 6 = 3)
        # min(5, ...) prend le plus petit des deux : jamais plus de 5
        # → à 4 joueurs : min(5, 5) = 5 cartes
        # → à 6 joueurs : min(5, 3) = 3 cartes
        self.nb_carte_max = min(5, 22 // len(self.joueurs))
        self.nb_carte = self.nb_carte_max
        self.donneur = self.joueurs[0]   # le premier de la liste distribue en premier
        self.numero_manche = 0

    def en_vie(self):
        # renvoie la liste des joueurs qui ont encore des vies
        vivants = []
        for joueur in self.joueurs:
            if joueur.vies > 0:
                vivants.append(joueur)
        return vivants

    def donneur_suivant(self):
        # le donneur passe à gauche, mais on saute ceux qui sont éliminés
        i = self.joueurs.index(self.donneur)
        for k in range(1, len(self.joueurs) + 1):
            # le % c'est le reste de la division : ça fait "tourner" autour de la table
            # ex à 4 joueurs : si i + k = 4, alors 4 % 4 = 0 → on revient au premier
            candidat = self.joueurs[(i + k) % len(self.joueurs)]
            if candidat.vies > 0:
                return candidat

    def jouer(self):
        # tant qu'il reste plus d'un joueur en vie, on joue une nouvelle manche
        while len(self.en_vie()) > 1:
            self.numero_manche = self.numero_manche + 1
            vivants = self.en_vie()
            # si le donneur vient de se faire éliminer, on passe au suivant
            if self.donneur not in vivants:
                self.donneur = self.donneur_suivant()

            print("=" * 50)   # "=" * 50 ça fait une ligne de 50 signes égal
            print("Manche", self.numero_manche, "-", self.nb_carte, "carte(s) - donneur :", self.donneur.nom)
            print("=" * 50)

            # on crée la manche avec seulement les joueurs encore en vie, et on la joue
            manche = Manche(self.nb_carte, vivants, self.donneur)
            manche.jouer()

            # manche suivante : une carte de moins (5, 4, 3, 2, 1)
            # et quand on arrive à 0, on recommence au début
            self.nb_carte = self.nb_carte - 1
            if self.nb_carte == 0:
                self.nb_carte = self.nb_carte_max
            # et le donneur passe à gauche
            self.donneur = self.donneur_suivant()

        # la partie est finie, on cherche le gagnant
        vivants = self.en_vie()
        if len(vivants) == 1:
            return vivants   # cas normal : il en reste un seul
        # cas rare : les derniers sont tombés à 0 en même temps
        # → gagne celui qui a le moins de vies en négatif
        meilleur = self.joueurs[0].vies
        for joueur in self.joueurs:
            if joueur.vies > meilleur:
                meilleur = joueur.vies
        gagnants = []
        for joueur in self.joueurs:
            if joueur.vies == meilleur:
                gagnants.append(joueur)   # s'il y a égalité, ils gagnent tous les deux
        return gagnants


def texte_plis(n):
    # écrit "0 pli", "1 pli", "3 plis" pour que ce soit clair que c'est un nombre de plis
    if n <= 1:
        return str(n) + " pli"
    return str(n) + " plis"


# =====================================================================
#  TOI AU CLAVIER
#  Ces fonctions servent seulement quand c'est un humain qui joue.
#  Elles sont en dehors des classes parce que c'est juste de l'affichage
#  et des questions, pas des règles du jeu.
# =====================================================================
def afficher_situation(joueur, manche):
    # affiche ce que t'as le droit de voir avant de choisir
    print("\n--- À toi,", joueur.nom, "---")

    if manche.nb_carte == 1:
        # manche à 1 carte : tu vois les cartes des autres, mais pas la tienne
        print("Ta carte : ?")
        for autre in manche.joueurs:
            if autre is not joueur:   # "is not" = c'est pas le même joueur que toi
                if autre.main:        # s'il a encore sa carte en main
                    print("  ", autre.nom, "a le", autre.main[0].texte())
                else:                 # sinon il l'a déjà posée
                    print("  ", autre.nom, "a déjà joué")
    else:
        # sinon tu vois ta main normalement
        textes = []
        for carte in joueur.main:
            textes.append(carte.texte())
        # ", ".join(...) colle les textes avec une virgule entre chaque
        print("Ta main :", ", ".join(textes))

    # le tableau des scores : TOUS les joueurs de la manche, dans l'ordre de jeu
    # (même ceux qui ont pas encore annoncé, sinon on croit qu'ils ont disparu)
    print("Scores :")
    for j in manche.ordre():
        if j.pli_annonce is None:
            # il a pas encore annoncé
            print("   " + j.nom + " : pas encore annoncé - " + str(j.vies) + " vies")
            continue
        # il lui manque combien de plis pour tomber juste ?
        reste = j.pli_annonce - j.pli_fait
        if reste > 0:
            etat = "il lui en manque " + str(reste)
        elif reste == 0:
            etat = "pile juste pour l'instant"
        else:
            etat = "déjà " + str(-reste) + " de trop"
        print("   " + j.nom + " : annoncé " + str(j.pli_annonce) + ", fait " + str(j.pli_fait)
              + " (" + etat + ") - " + str(j.vies) + " vies")

    # les cartes déjà posées dans ce pli (s'il y en a)
    if manche.pli_en_cours:
        textes = []
        for j, c, v in manche.pli_en_cours:
            if c.est_excuse():
                textes.append(j.nom + " a posé l'Excuse à " + str(v))
            else:
                textes.append(j.nom + " a posé " + str(v))
        print("Sur la table :", ", ".join(textes))


def demander_nombre(question, minimum, maximum, interdit=None):
    # pose une question au clavier jusqu'à ce que tu tapes un nombre valable
    # while True = on boucle à l'infini, et on sort avec le return
    while True:
        reponse = input(question)       # ce que tu tapes, c'est toujours du texte
        if not reponse.isdigit():       # si c'est pas que des chiffres...
            print("Tape un nombre.")
            continue                    # ... on repose la question
        n = int(reponse)                # on transforme le texte en nombre
        if n < minimum or n > maximum:
            print("Entre", minimum, "et", maximum, ".")
        elif n == interdit:
            print("Interdit : le total des annonces tomberait pile.")
        else:
            return n                    # c'est bon, on renvoie le nombre


def annonce_humain(joueur, manche, interdite):
    # c'est à toi d'annoncer : on te montre la situation puis on te demande
    afficher_situation(joueur, manche)
    question = "Combien de plis annonces-tu (0 à " + str(manche.nb_carte) + ") ? "
    if interdite is not None:
        question = "Combien de plis annonces-tu (0 à " + str(manche.nb_carte) + ", sauf " + str(interdite) + ") ? "
    return demander_nombre(question, 0, manche.nb_carte, interdite)


def choix_carte_humain(joueur, manche):
    # c'est à toi de poser une carte
    afficher_situation(joueur, manche)
    if len(joueur.main) == 1:
        # t'as plus qu'une carte, pas besoin de demander
        print("Tu poses ta dernière carte :", joueur.main[0].texte())
        return joueur.main[0]
    # on numérote tes cartes à partir de 1 (plus naturel que 0 pour toi)
    # le numéro entre crochets c'est ce que tu tapes, la carte c'est après
    for i in range(len(joueur.main)):
        carte = joueur.main[i]
        if carte.est_excuse():
            print("   [" + str(i + 1) + "] → l'Excuse (0 ou 22, tu choisiras)")
        else:
            print("   [" + str(i + 1) + "] → la carte " + carte.texte())
    n = demander_nombre("Tape le numéro entre crochets de la carte à poser : ", 1, len(joueur.main))
    return joueur.main[n - 1]   # n - 1 parce que dans la liste ça commence à 0


def choix_excuse_humain():
    # t'as posé l'Excuse : tu choisis si elle vaut 0 ou 22
    while True:
        reponse = input("L'Excuse vaut 0 ou 22 ? ")
        if reponse == "0":
            return 0
        if reponse == "22":
            return 22
        print("Tape 0 ou 22.")


# =====================================================================
#  LANCEMENT DU JEU
#  Ce bloc tourne seulement quand tu lances le fichier directement
#  (python tarot.py). Si un autre fichier fait "import tarot",
#  il tourne pas : ça servira pour les simulations et l'IA plus tard.
# =====================================================================
if __name__ == "__main__":
    nb_joueurs = demander_nombre("Combien de joueurs (2 à 11) ? ", 2, 11)
    tu_joues = input("Tu joues contre les bots ? (o/n) ")

    noms = []
    nom_humain = None
    if tu_joues == "o":
        nom_humain = input("Ton nom : ")
        noms.append(nom_humain)   # toi t'es en premier, donc tu distribues en premier

    # on complète avec des bots jusqu'à avoir le bon nombre de joueurs
    # ils ont des prénoms (pas des numéros) pour pas confondre avec les cartes
    prenoms_bots = ["Awa", "Kofi", "Zaïna", "Malik", "Nadia", "Sékou",
                    "Fatou", "Idris", "Mariam", "Tidiane", "Lina"]
    i = 0
    while len(noms) < nb_joueurs:
        if prenoms_bots[i] != nom_humain:   # au cas où t'aurais le même prénom qu'un bot
            noms.append(prenoms_bots[i])
        i = i + 1

    partie = Partie(noms, nom_humain)
    gagnants = partie.jouer()

    textes = []
    for j in gagnants:
        textes.append(j.nom)
    print("\nGagnant :", ", ".join(textes), "en", partie.numero_manche, "manches")

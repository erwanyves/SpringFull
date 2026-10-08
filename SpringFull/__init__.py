# -*- coding: utf-8 -*-
"""
SpringFull - Package de calcul et génération de ressorts de compression

Macro FreeCAD complète pour:
- Calcul de ressorts selon EN 13906-1
- Génération de géométrie 3D détaillée ou simplifiée
- Stockage des données dans les propriétés du Body

Version: 1.5.2 - Modifications:
- v1.1: Suppression des propriétés doublées, correction deadTurnsQty et onLoadHight
- v1.2: Correction duplication LCS lors changement de représentation
- v1.2.1: Gestion des fichiers multi-ressorts (LCS avec suffixes numériques)
- v1.3.0: Calcul nt différencié selon type d'extrémité (meulées vs non meulées)
         Stockage L0, H_charge, Lc_max pour les 3 modes de représentation
         Positionnement Z du sketch selon type d'extrémité
         Nouveau type MEULEES (remplace MEULEES_PLANES)
- v1.4.0: Propriétés visibles regroupées dans "Spring Params" en lecture seule
         Ajout propriétés calculées: internalDiameter (Di), externalDiameter (De)
         Propriétés internes masquées dans "Internal"
         Seules données visibles pour l'utilisateur:
           - configuration, load, loadType, extremeTurns
           - internalDiameter, meanDiameter, externalDiameter
           - onLoadHight, freeLength, material
- v1.4.1: Sélection de langue contrôlée par fichiers timestamps
- v1.4.2: Correction du bug "nouveau ressort sans modification"
         Le ressort est maintenant calculé et représenté même si l'utilisateur
         ne modifie pas le template par défaut lors de la création.
         Ajout de la fonction isBodyEmpty() pour détecter les Bodies sans géométrie.
- v1.5.0: Corrections issues de l'audit UX (voir SpringFull_Audit_UX.docx)
         - Langue mémorisée dans lang.txt (dialogue affiché une seule fois,
           au premier lancement), remplace le mécanisme par timestamps
           Translate_on.txt/Translate_off.txt.
         - Messages d'erreur/confirmation du calculateur, descriptions des
           propriétés FreeCAD et messages de construction désormais traduits
           dans les 5 langues (auparavant figés en français).
         - Nouveau code interne configurationMode (indépendant de la langue)
           pour le mode de représentation, remplace la ré-interprétation
           fragile du texte affiché par correspondance de sous-chaînes.
         - Accusé de succès en barre de statut au lieu d'un dialogue modal
           supplémentaire ; barre de progression en mode indéterminé.
         - Retour visuel lors de la resélection automatique du diamètre de
           fil ; protection de la reconstruction géométrique contre les
           échecs (message clair au lieu d'une trace Python brute).
         - Nettoyage de code mort (on_recalculate, dialogSpringCreated,
           confirmReconstructDialog).
- v1.5.1: Diamètres incompatibles visibles directement dans la liste
         déroulante du calculateur : au lieu d'être retirés de la liste
         quand un paramètre (force, dimension...) les rend trop petits,
         ils restent affichés en rouge et désactivés (non sélectionnables).
         Correctif : la couleur de texte des diamètres compatibles était
         remise à noir par erreur (au lieu de la couleur du thème),
         illisible en thème sombre. Le reset du rôle Qt se fait désormais
         via setData(None, role) au lieu de setForeground/setBackground(QBrush()).
- v1.5.2: Le dialogue "Calcul Ressort Compression" s'ouvre désormais à une
         hauteur adaptée à son contenu réel au lieu de rester collé à une
         hauteur minimale fixe (650 px, un peu juste pour ce formulaire
         dense). Hauteur calculée dynamiquement, plafonnée à la hauteur
         disponible de l'écran (le défilement reste disponible en secours
         sur un petit écran).
"""

__version__ = "1.5.2"
__author__ = "Yves Guillou"
__licence__ = "LGPL-2.1"

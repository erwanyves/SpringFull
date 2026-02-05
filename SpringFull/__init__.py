# -*- coding: utf-8 -*-
"""
SpringFull - Package de calcul et génération de ressorts de compression

Macro FreeCAD complète pour:
- Calcul de ressorts selon EN 13906-1
- Génération de géométrie 3D détaillée ou simplifiée
- Stockage des données dans les propriétés du Body

Version: 1.4.2 - Modifications:
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
"""

__version__ = "1.4.2"
__author__ = "Yves Guillou"
__licence__ = "GPL"

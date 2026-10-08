# Chemin : SpringFullDialogsModule.py
# -*- coding: utf-8 -*-
"""
SpringFullDialogsModule - Dialogues pour SpringFull
Version sans LibreOffice, avec intégration du calculateur

Version: 1.1 - Correction du bug onLoadHight: séparation hauteur calcul/affichage
"""

__author__ = "Yves Guillou"
__licence__ = "LGPL-2.1"

# Import compatible PySide2/PySide6
try:
    from PySide6 import QtCore
    from PySide6 import QtWidgets as QtGui  # Alias pour compatibilité avec le code existant
    from PySide6.QtWidgets import QMessageBox, QDialog
    # PySide6: les constantes sont dans des sous-classes
    QMsgBoxOk = QMessageBox.StandardButton.Ok
    QMsgBoxYes = QMessageBox.StandardButton.Yes
    QMsgBoxNo = QMessageBox.StandardButton.No
    QMsgBoxInformation = QMessageBox.Icon.Information
    QDialogAccepted = QDialog.DialogCode.Accepted
    QDialogRejected = QDialog.DialogCode.Rejected
    PYSIDE6 = True
except ImportError:
    from PySide import QtCore
    from PySide import QtGui
    from PySide.QtWidgets import QMessageBox, QDialog
    # PySide2: les constantes sont directement sur les classes
    QMsgBoxOk = QMessageBox.Ok
    QMsgBoxYes = QMessageBox.Yes
    QMsgBoxNo = QMessageBox.No
    QMsgBoxInformation = QMessageBox.Information
    QDialogAccepted = QDialog.Accepted
    QDialogRejected = QDialog.Rejected
    PYSIDE6 = False

# Import du module d'internationalisation
from SpringFull.SpringFullI18nModule import tr


def _config_mode_to_display(mode, custom_height=0.0, custom_force=0.0):
    """
    Construit le texte affiché (traduit, dans la langue active) pour un
    mode de configuration interne indépendant de la langue.

    Remplace l'ancienne fonction translate_config(), qui était dupliquée
    dans configuration() et springUpdateDialog() et devait re-parser par
    correspondance de sous-chaînes un texte déjà traduit pour retrouver le
    mode d'origine - une opération fragile (termes ambigus entre "sous
    charge" et "charge définie", par exemple) qui pouvait, dans certains
    cas, faire pré-cocher le mauvais mode. Voir audit UX finding #4 : le
    mode réel est maintenant stocké tel quel (data.configurationMode),
    cette fonction ne fait plus que le traduire pour l'affichage.

    Args:
        mode: code interne ("FREE", "LOADED", "SOLID", "CUSTOM_HEIGHT",
            "CUSTOM_FORCE"), ou toute autre valeur (traité comme "LOADED")
        custom_height: valeur à afficher pour le mode CUSTOM_HEIGHT (mm)
        custom_force: valeur à afficher pour le mode CUSTOM_FORCE (daN)

    Returns:
        str: texte traduit prêt à afficher
    """
    if mode == "FREE":
        return tr("repr.config_free")
    if mode == "SOLID":
        return tr("repr.config_solid")
    if mode == "CUSTOM_HEIGHT":
        return tr("repr.config_custom_height").format(custom_height or 0.0)
    if mode == "CUSTOM_FORCE":
        return tr("repr.config_custom_force").format(custom_force or 0.0)
    # "LOADED" et toute valeur inconnue/absente (compatibilité) -> défaut
    return tr("repr.config_loaded")


# NOTE (audit UX finding #9, v1.5): dialogSpringCreated() a été retirée -
# elle était entièrement écrite (traduite, stylée) mais n'était appelée
# nulle part dans le flux réel. Les clés de traduction dlg.spring_created_*
# restent dans les fichiers de locale si l'on souhaite la réintroduire.


def dialogMissingProperties(count, body_name):
    """
    Dialogue informant que des propriétés manquantes ont été créées.
    
    Args:
        count: Nombre de propriétés créées
        body_name: Nom du Body
    """
    msgBox = QtGui.QMessageBox()
    msgBox.setWindowTitle(tr("dlg.props_init_title"))
    msgBox.setText(f"<center>{tr('dlg.props_init_msg').format(count=count, name=body_name)}</center>")
    msgBox.setInformativeText(f"<center>{tr('dlg.props_init_info')}</center>")
    msgBox.setStandardButtons(QMsgBoxOk)
    msgBox.exec()


def dialogInitialSaveAlert():
    """
    Dialogue demandant la sauvegarde initiale du fichier.
    """
    msgBox = QtGui.QMessageBox()
    msgBox.setWindowTitle(tr("dlg.save_required_title"))
    msgBox.setText(f"<center>{tr('dlg.save_required_msg')}</center>")
    msgBox.setStandardButtons(QMsgBoxOk)
    msgBox.exec()


def showBuildErrorDialog(spring_name, error, restaure=False):
    """
    Dialogue affiché quand la reconstruction géométrique du ressort échoue
    (ex: paramètres qui passent les vérifications du calculateur mais
    restent géométriquement irréalisables).

    Avant v1.5, ce cas remontait la trace Python brute de FreeCAD (voir
    reconstructSpring() dans SpringFull.FCMacro, qui n'était entouré
    d'aucun try/except) - une chute brutale de perception de qualité au
    pire moment. Voir audit UX finding #8.

    Args:
        spring_name: Nom du ressort concerné
        error: exception d'origine (str(error) inséré dans le message)
        restaure: True si l'appelant a ABANDONNÉ une transaction avant
            d'ouvrir cette boîte — le document est alors revenu à son
            état d'avant l'actualisation, et le message peut le dire.
            False (défaut) : aucune transaction n'était ouverte (son
            ouverture a échoué), le message d'origine reste le seul
            honnête. Promettre une restauration qui n'a pas eu lieu
            serait pire que l'ancien message (motif ORing, 13/09/2026).
    """
    msgBox = QtGui.QMessageBox()
    msgBox.setWindowTitle(tr("dlg.build_error_title"))
    msgBox.setIcon(QMessageBox.Icon.Critical if PYSIDE6 else QMessageBox.Critical)
    msgBox.setText(f"<b>{spring_name}</b>")
    msgBox.setInformativeText(
        tr("dlg.build_error_msg_restored" if restaure
           else "dlg.build_error_msg").format(error=str(error)))
    msgBox.setStandardButtons(QMsgBoxOk)
    msgBox.exec()


# ---------------------------------------------------------------------------
# Hauteur definie par une arete — decision metier, sortie du Qt pour etre
# eprouvable hors FreeCAD (mecanismes_partages.md 2.2 point 11).
# Specification : claude/spec_springfull_hauteur_depuis_arete.md
# ---------------------------------------------------------------------------

# Codes d'etat internes, independants de la langue — meme principe que
# configurationMode (audit UX finding #4) : on ne reparse jamais un texte
# traduit pour retrouver un etat.
HAUTEUR_OK            = "OK"
HAUTEUR_INDETERMINEE  = "INDETERMINEE"
HAUTEUR_SOUS_ORIGINE  = "SOUS_ORIGINE"
HAUTEUR_TROP_COMPRIME = "TROP_COMPRIME"
HAUTEUR_DECOLLE       = "DECOLLE"


def hauteurDepuisArete(centre_monde, sommets_monde, placement_ressort):
    """
    Hauteur du point d'appui, exprimee dans le repere du ressort.

    Le ressort est construit depuis Local_Bottom (z = 0) vers +Z. La hauteur
    cherchee est donc la coordonnee Z, DANS LE REPERE DU RESSORT, du point
    designe : il n'y a pas d'axe a construire separement, et le signe vient
    gratuitement — une arete situee sous l'origine rend un Z negatif.

    Args:
        centre_monde: centre de gravite de l'arete, coordonnees MONDE.
        sommets_monde: sommets de l'arete, coordonnees MONDE. Liste
            eventuellement vide (arete fermee sans sommet distinct).
        placement_ressort: placement MONDE du ressort — origine sur
            Local_Bottom, axe Z sur l'axe du ressort.

    Returns:
        (hauteur, etalement) en mm, ou (None, None) si rien d'exploitable.
        - hauteur  : Z du centre de gravite dans le repere du ressort.
        - etalement: max(Z) - min(Z) sur le centre ET les sommets. Vaut 0.0
          quand l'arete est perpendiculaire a l'axe. C'est ce qui permet de
          REFUSER de moyenner en silence une arete oblique, au lieu de rendre
          une valeur plausible et arbitraire.

    CONTRAT D'API SUPPOSE, non prouve par la contre-epreuve sur faux objets
    (cf. spec 7) : placement_ressort.inverse() rend un placement dont
    .multVec(v) transforme un vecteur monde en coordonnees locales.
    """
    if centre_monde is None or placement_ressort is None:
        return (None, None)

    vers_local = placement_ressort.inverse()

    hauteur = vers_local.multVec(centre_monde).z
    zs = [hauteur]
    for sommet in (sommets_monde or []):
        zs.append(vers_local.multVec(sommet).z)

    return (hauteur, max(zs) - min(zs))


def verdictHauteur(hauteur, etalement, solid_height, free_length,
                   tol_etalement=0.01):
    """
    Confronte une hauteur mesuree aux bornes physiques du ressort.

    Rend DEUX informations distinctes, et c'est deliberе :
      - `etat`    : ce que vaut la HAUTEUR (bornes physiques) ;
      - `oblique` : ce que vaut la MESURE (l'arete etait-elle perpendiculaire
                    a l'axe du ressort).
    Les fondre dans un code unique ferait porter a un meme indicateur deux
    choses differentes — c'est exactement le defaut du 14/09 sur le libelle de
    la liste de choix (mecanismes_partages.md 3.8).

    Returns:
        dict {etat, bloquant, oblique, ecart}
        - etat    : un des codes HAUTEUR_* ci-dessus.
        - bloquant: True si la validation doit etre REFUSEE. Decision de
          l'utilisateur du 15/09 : hors bornes = bloquant, jamais de bornage
          silencieux (a la difference du mode CUSTOM_FORCE existant, qui
          borne sans le dire — divergence assumee, spec 5).
        - oblique : True si l'etalement depasse la tolerance. INFORMATIF,
          jamais bloquant : c'est a l'utilisateur de trancher.
        - ecart   : de combien on sort de la borne franchie (mm), sinon None.
    """
    oblique = etalement is not None and etalement > tol_etalement

    if hauteur is None:
        return {"etat": HAUTEUR_INDETERMINEE, "bloquant": True,
                "oblique": oblique, "ecart": None}

    # L'ORDRE COMPTE. Une hauteur negative est AUSSI inferieure a
    # solid_height, mais ce n'est pas un ressort trop comprime : c'est une
    # arete designee sous l'origine du ressort (spec 4.3). Deux causes
    # differentes exigent deux messages differents ; tester les bornes
    # d'abord afficherait "trop comprime" sur une erreur de designation.
    if hauteur <= 0:
        return {"etat": HAUTEUR_SOUS_ORIGINE, "bloquant": True,
                "oblique": oblique, "ecart": None}

    if hauteur < solid_height:
        return {"etat": HAUTEUR_TROP_COMPRIME, "bloquant": True,
                "oblique": oblique, "ecart": solid_height - hauteur}

    if hauteur > free_length:
        return {"etat": HAUTEUR_DECOLLE, "bloquant": True,
                "oblique": oblique, "ecart": hauteur - free_length}

    return {"etat": HAUTEUR_OK, "bloquant": False,
            "oblique": oblique, "ecart": None}


# ---------------------------------------------------------------------------
# Designation d'une arete depuis le dialogue — socle
# Specification : claude/spec_springfull_hauteur_depuis_arete.md §3 et §11
# ---------------------------------------------------------------------------

_TYPES_LIENS_DLG = ('App::Link', 'App::LinkElement', 'App::LinkGroup')


def _afficherNonModal3D(dlg, widget_appelant):
    """
    Affiche `dlg` en laissant la vue 3D de FreeCAD INTERACTIVE, alors que
    `widget_appelant` a ete ouvert par exec() — donc ApplicationModal.

    GESTE transpose d'ORing (`ORing/modules/dialogue.py::
    _afficher_dialogue_non_modal_3d`), en service et valide, et deja porte
    une fois dans StandardPartSelector/insertion.py. Le raisonnement passe,
    pas le code : ce projet n'importe jamais entre macros.

    Trois points sans lesquels cela ne marche pas, chacun paye :

    1. Masquer le dialogue appelant NE SUFFIT PAS. L'attribut WA_ShowModal
       pose par son exec() reste actif et fige la fenetre principale
       FreeCAD, vue 3D comprise (defaut ORing du 05/09/2026, signale par
       l'utilisateur : « la vue 3D est totalement figee pendant
       l'assistant »). Il faut sortir explicitement de l'etat modal, et le
       retablir ensuite.
    2. Le sous-dialogue se rattache a la FENETRE PRINCIPALE, jamais au
       dialogue appelant : une fenetre Qt.Tool suit la visibilite de son
       parent, et ce parent vient d'etre masque.
    3. On ne rend JAMAIS la main a la boucle de l'appelant. Une QEventLoop
       locale tient l'execution ici. Mesure du 15/09/2026 : une sonde qui
       faisait hide() puis RETOURNAIT de son slot voyait exec() rendre la
       main aussitot et filait jusqu'a son rapport, sans avoir rien lu.

    ATTENTION — DANS SpringFull, `widget_appelant` EST TOUJOURS None, ET
    C'EST DELIBERE. Le masquage du dialogue appelant a ete essaye le
    15/09/2026 et abandonne : `hide()` sur un dialogue en cours d'`exec()`
    termine sa boucle modale, `configuration()` rendait None, `main()`
    rebouclait, et DEUX fenetres « Representation du ressort » restaient a
    l'ecran (constat de l'utilisateur, capture a l'appui). Ici le dialogue
    est FERME volontairement par `done(CODE_DESIGNER_ARETE)` avant d'appeler
    cette fonction : aucun modal n'est vivant, la vue 3D est libre par
    construction, et tout le bloc de modalite ci-dessous est inerte.
    Il est conserve pour le jour ou un appelant non modal en aurait besoin.

    Retourne dlg.result().
    """
    try:
        import FreeCADGui as Gui
    except ImportError:
        return QDialogRejected

    appelant = widget_appelant.window() if widget_appelant is not None else None
    etait_visible = bool(appelant.isVisible()) if appelant is not None else False
    modalite_avant = None

    attr_modal = getattr(QtCore.Qt, 'WA_ShowModal',
                         getattr(getattr(QtCore.Qt, 'WidgetAttribute', None),
                                 'WA_ShowModal', None))

    if etait_visible:
        appelant.hide()
        if attr_modal is not None:
            try:
                modalite_avant = (appelant.windowModality(),
                                  bool(appelant.testAttribute(attr_modal)))
                appelant.setAttribute(attr_modal, False)
                appelant.setWindowModality(QtCore.Qt.NonModal)
            except Exception as e:
                # Pas de except muet : si la sortie de modalite echoue, la
                # vue 3D restera figee et l'utilisateur doit savoir pourquoi.
                _journal("sortie de modalite impossible : %s" % e)
                modalite_avant = None

    try:
        dlg.setParent(Gui.getMainWindow(),
                      QtCore.Qt.Tool | QtCore.Qt.WindowStaysOnTopHint)
    except Exception:
        dlg.setWindowFlags(dlg.windowFlags()
                           | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
    try:
        dlg.setWindowModality(QtCore.Qt.NonModal)
    except Exception as e:
        _journal("sous-dialogue non demodalise : %s" % e)

    boucle = QtCore.QEventLoop()
    dlg.finished.connect(boucle.quit)
    dlg.show()
    dlg.raise_()
    dlg.activateWindow()
    (boucle.exec if hasattr(boucle, 'exec') else boucle.exec_)()

    if modalite_avant is not None and attr_modal is not None:
        try:
            appelant.setWindowModality(modalite_avant[0])
            appelant.setAttribute(attr_modal, modalite_avant[1])
        except Exception as e:
            _journal("modalite non retablie : %s" % e)
    if etait_visible:
        appelant.show()
        appelant.raise_()
        appelant.activateWindow()
    return dlg.result()


def _journal(msg):
    """Trace qui doit ARRIVER : print() est masque module par module ici."""
    try:
        import FreeCAD as App
        App.Console.PrintMessage("[SpringFull] %s\n" % msg)
    except Exception:
        pass


def _placementMondeRessort(piece, lien_impose=None):
    """
    Placement MONDE de l'INSTANCE du ressort. Rend (placement, info) ou
    (None, raison).

    MESURE DU 15/09/2026 (spec §11), sur `test liens.FCStd` :
      - `body.Placement` et `body.getGlobalPlacement()` rendent le placement
        dans le DOCUMENT SOURCE : faux de 132,5 mm en assemblage ;
      - `LinkTransform` vaut False (defaut) : le lien REMPLACE le placement
        du corps. Composer lien x body est donc une FAUTE, mesuree a
        133,6 mm — pas une approximation ;
      - le placement du LIEN SEUL etait exact sur ce document, mais
        seulement parce que l'assemblage y est a l'origine. Tete deplacee
        de (10,20,30) : 37,4 mm d'ecart. Il est ecarte pour cette raison ;
      - seul le CHEMIN DEPUIS LA RACINE est juste dans les deux cas.

    La cible du chemin est le LIEN, pas le corps : un PartDesign::Body
    n'apparait jamais comme sous-objet (getSubObjects() rend un tuple vide),
    donc aucun chemin ne peut l'atteindre. Ce qui est adressable depuis la
    racine, c'est l'INSTANCE.
    """
    import FreeCAD as App
    if piece is None:
        return (None, "aucun ressort")
    doc = App.ActiveDocument
    if doc is None:
        return (None, "aucun document actif")

    # Mono-document : le corps vit dans le document actif, son placement
    # propre EST son placement monde.
    if piece.Document is doc:
        return (piece.Placement, "mono-document")

    if lien_impose is not None:
        liens = [lien_impose]
    else:
        liens = [obj for obj in doc.Objects
                 if getattr(obj, 'TypeId', '') in _TYPES_LIENS_DLG
                 and _lienMeneA(obj, piece)]

    if not liens:
        return (None, "aucun lien de ce document n'amene ce ressort")
    if len(liens) > 1:
        # NE PAS choisir arbitrairement (defaut ORing du 13/09 : le premier
        # rendu par parts.values(), donc n'importe lequel). Mais on n'arrive
        # ici QUE si la selection de lancement n'a pas designe d'instance.
        return (None, "instances multiples:%d" % len(liens))

    lien = liens[0]
    cle = (lien.Document.Name, lien.Name)
    for tete in doc.Objects:
        if tete is lien:
            continue
        chemin = _cheminVersDlg(tete, cle)
        if chemin is None:
            continue
        try:
            m = tete.getSubObject(chemin, 4)
        except Exception as e:
            _journal("getSubObject(%r, 4) sur %s : %s" % (chemin, tete.Name, e))
            continue
        if m is not None:
            return (App.Placement(m), "chemin %s.%s" % (tete.Name, chemin))

    return (None, "aucun chemin depuis la racine vers l'instance")


def _instanceDepuisSelection(piece):
    """
    Le lien par lequel l'utilisateur a designe CE ressort, lu sur la
    selection 3D courante. Rend le lien, ou None.

    POURQUOI (defaut du 15/09/2026, signale par l'utilisateur) : quand un
    meme corps est instancie plusieurs fois, `_placementMondeRessort` s'est
    d'abord contente de COMPTER les liens et de refuser au-dela d'un. Or
    l'information existait deja : la macro journalise « Element de ressort
    selectionne, Body parent: Spring003 » — l'utilisateur a designe UNE
    instance pour lancer la macro. Refuser revenait a jeter sa reponse.

    C'est la regle du projet (mecanismes_partages.md §3.1) etendue au
    multi-instance : cliquer n'importe quel element d'un composant, c'est
    designer CE composant — et en assemblage, CETTE instance.

    On resout les prefixes du chemin de selection et on retient le premier
    qui est un lien menant a `piece`. Jamais de comparaison de chaines :
    l'identite se fait sur les objets (le lien et le corps portent parfois
    le MEME Name dans deux documents differents).
    """
    if piece is None:
        return None
    try:
        import FreeCADGui as Gui
    except ImportError:
        return None
    try:
        sel = Gui.Selection.getSelectionEx('', 0)
    except Exception as e:
        _journal("selection illisible : %s" % e)
        return None
    if not sel:
        return None

    s = sel[0]
    noms = list(getattr(s, 'SubElementNames', ()) or ())
    if not noms:
        return None
    tete, chemin = s.Object, noms[0]

    for i, c in enumerate(chemin):
        if c != '.':
            continue
        try:
            obj = tete.getSubObject(chemin[:i + 1], 1)
        except Exception:
            continue
        if obj is None or getattr(obj, 'TypeId', '') not in _TYPES_LIENS_DLG:
            continue
        if _lienMeneA(obj, piece):
            return obj
    return None


def _lienMeneA(lien, piece):
    """Ce lien resout-il vers `piece` ? Identite sur (Document, Name)."""
    cible = lien
    for _ in range(10):
        if getattr(cible, 'TypeId', '') not in _TYPES_LIENS_DLG:
            break
        suivant = cible.getLinkedObject(True)
        if suivant is None or suivant is cible:
            break
        cible = suivant
    for c in [cible] + list(getattr(cible, 'Group', None) or []):
        if getattr(c, 'Document', None) is piece.Document \
                and getattr(c, 'Name', None) == piece.Name:
            return True
    return False


def _cheminVersDlg(tete, cle_cible, profondeur_max=6):
    """Parcours EN LARGEUR : chemin le plus court, donc deterministe."""
    file_attente = [(tete, "", 0)]
    vus = set()
    while file_attente:
        obj, chemin, prof = file_attente.pop(0)
        try:
            cle = (obj.Document.Name, obj.Name)
        except Exception:
            continue
        if cle in vus:
            continue
        vus.add(cle)
        if chemin and cle == cle_cible:
            return chemin
        if prof >= profondeur_max:
            continue
        try:
            noms = list(obj.getSubObjects() or [])
        except Exception:
            noms = []
        for nom in noms:
            try:
                enfant = obj.getSubObject(nom, 1)
            except Exception:
                continue
            if enfant is not None:
                file_attente.append((enfant, chemin + nom, prof + 1))
    return None


def _areteSelectionneeMonde():
    """
    Arete actuellement selectionnee, en coordonnees MONDE.
    Rend (centre, sommets, info) ou (None, None, raison).

    MESURE DU 15/09/2026 — ET RECTIFICATION D'UNE ERREUR DE CE MODULE.

    La premiere version multipliait les points par la matrice accumulee du
    chemin (`tete.getSubObject(chemin, 4)`). Elle rendait EXACTEMENT LE
    DOUBLE de la distance reelle : 117,2 mm pour 58,6 mesures par
    l'utilisateur dans FreeCAD. Releve de `SONDE_arete_mesure_springfull.py`
    sur un fichier mono-document :

        tete = Body, son placement            z = 58,6
        matrice du chemin                     z = 58,6
        A) points bruts                       z = 58,6   <- JUSTE
        B) points x matrice du chemin         z = 117,2  <- ce qu'on faisait
        C) points x placement de la tete      z = 117,2

    CAUSE : `Gui.Selection.getSelectionEx('', 0)` rend des `SubObjects`
    DEJA exprimes en coordonnees monde, transformations accumulees
    comprises. Les multiplier par la matrice du chemin compte le trajet
    deux fois.

    ⚠ `mecanismes_partages.md` §4.4 affirme l'inverse — « les SubObjects
    sont dans le repere LOCAL ». Cette affirmation vaut pour la selection
    RESOLUE (`getSelectionEx()`, ou `Object` est l'objet profond du document
    source), PAS pour l'appel non resolu utilise ici. Deux appels, deux
    contrats ; le document n'en distingue qu'un. A rectifier la-bas.

    CONSEQUENCE VISIBLE : une rotation appliquee deux fois decoplanarise des
    points qui l'etaient — d'ou l'« arete non perpendiculaire a l'axe,
    etalement 9,96 mm » signale sur une arete parfaitement circulaire.

    RESTE A CONFIRMER EN ASSEMBLAGE : la mesure ci-dessus est
    mono-document. Rien ne prouve encore que les SubObjects soient monde
    quand la tete est un Assembly deplace. Le panneau affiche les
    coordonnees du centre pour que l'ecart se voie au premier essai.
    """
    import FreeCAD as App
    try:
        import FreeCADGui as Gui
    except ImportError:
        return (None, None, "pas d'interface graphique")

    try:
        sel = Gui.Selection.getSelectionEx('', 0)
    except Exception as e:
        return (None, None, "selection illisible : %s" % e)
    if not sel:
        return (None, None, "aucune selection")

    s = sel[0]
    formes = list(getattr(s, 'SubObjects', ()) or ())
    noms = list(getattr(s, 'SubElementNames', ()) or ())
    if not formes or not noms:
        return (None, None, "selection sans sous-element")

    forme = formes[0]
    if getattr(forme, 'ShapeType', '') != 'Edge':
        return (None, None, "l'element designe est un %s, pas une arete"
                % getattr(forme, 'ShapeType', '?'))

    # AUCUNE transformation : les points sont deja en monde (voir ci-dessus).
    centre = forme.CenterOfMass
    sommets = [v.Point for v in (forme.Vertexes or [])]
    return (centre, sommets, "%s.%s" % (s.Object.Name, noms[0]))



def messageVerdictHauteur(hauteur, etalement, verdict, solid_height, free_length):
    """
    Texte destine a l'UTILISATEUR pour un verdict de mesure.

    Classe A du memorandum : ce message decrit ce que l'utilisateur VOIT et
    ce qu'il doit faire, pas ce que le code a calcule. Les quatre etats
    bloquants ont chacun leur message : une hauteur negative n'est PAS un
    ressort trop comprime, c'est une arete designee sous l'origine.
    """
    etat = verdict.get("etat")
    if etat == HAUTEUR_INDETERMINEE:
        return tr("repr.h_unknown")
    if etat == HAUTEUR_SOUS_ORIGINE:
        return tr("repr.h_below", h=hauteur)
    if etat == HAUTEUR_TROP_COMPRIME:
        return tr("repr.h_low", h=hauteur, b=solid_height, e=verdict.get("ecart") or 0.0)
    if etat == HAUTEUR_DECOLLE:
        return tr("repr.h_high", h=hauteur, b=free_length, e=verdict.get("ecart") or 0.0)
    texte = tr("repr.h_measured", h=hauteur)
    if verdict.get("oblique"):
        texte += "  " + tr("repr.h_oblique", s=etalement or 0.0)
    return texte


def _panneauDesignationArete(placement_ressort, solid_height, free_length,
                             tol_etalement=0.01):
    """
    Petit panneau NON MODAL de designation d'arete.

    Il ne calcule rien lui-meme : il appelle hauteurDepuisArete() et
    verdictHauteur(), les deux fonctions pures eprouvees hors FreeCAD.

    Il affiche AUSSI les coordonnees monde du centre de l'arete. Ce n'est
    pas de la decoration : la transformation vers le repere monde est le
    seul maillon que la contre-epreuve ne prouve pas (elle travaille sur de
    faux objets, classe D). L'afficher rend une transformation fausse
    visible au premier essai, au lieu de produire un nombre plausible.

    L'objet rendu porte `mesure` = (hauteur, etalement, verdict) ou None.
    """
    dlg = QtGui.QDialog()
    dlg.setWindowTitle(tr("repr.pick_title"))
    dlg.setMinimumWidth(440)
    dlg.mesure = None

    lay = QtGui.QVBoxLayout()
    lay.addWidget(QtGui.QLabel(tr("repr.pick_hint")))
    lbl = QtGui.QLabel(tr("repr.pick_none"))
    lbl.setWordWrap(True)
    lbl.setStyleSheet("padding: 6px;")
    lay.addWidget(lbl)

    boutons = QtGui.QHBoxLayout()
    btn_ok = QtGui.QPushButton(tr("common.ok"))
    btn_annuler = QtGui.QPushButton(tr("common.cancel"))
    btn_ok.setEnabled(False)
    boutons.addStretch()
    boutons.addWidget(btn_ok)
    boutons.addWidget(btn_annuler)
    lay.addLayout(boutons)
    dlg.setLayout(lay)

    btn_ok.clicked.connect(dlg.accept)
    btn_annuler.clicked.connect(dlg.reject)

    def rafraichir():
        centre, sommets, info = _areteSelectionneeMonde()
        if centre is None:
            dlg.mesure = None
            btn_ok.setEnabled(False)
            lbl.setText(tr("repr.pick_none") + "  (" + str(info) + ")")
            return
        hauteur, etalement = hauteurDepuisArete(centre, sommets, placement_ressort)
        verdict = verdictHauteur(hauteur, etalement, solid_height, free_length,
                                 tol_etalement)
        dlg.mesure = (hauteur, etalement, verdict)
        btn_ok.setEnabled(True)
        lbl.setText(
            messageVerdictHauteur(hauteur, etalement, verdict,
                                  solid_height, free_length)
            + "<br><i>" + tr("repr.pick_centre",
                             x=centre.x, y=centre.y, z=centre.z) + "</i>")

    # Sondage periodique plutot qu'un SelectionObserver : il n'y a rien a
    # previsualiser en continu ici, et un observateur doit etre retire, ce
    # qui est un chemin d'oubli de plus. « Pas de symetrie si inutile. »
    minuterie = QtCore.QTimer(dlg)
    minuterie.setInterval(300)
    minuterie.timeout.connect(rafraichir)
    dlg.finished.connect(minuterie.stop)
    minuterie.start()
    rafraichir()
    return dlg


# Code de sortie propre du dialogue quand l'utilisateur demande a designer
# une arete. Distinct d'Accepted et de Rejected : on FERME volontairement.
CODE_DESIGNER_ARETE = 1234


def configuration(data):
    """
    Dialogue de representation, en une ou plusieurs PASSES.

    POURQUOI UNE ENVELOPPE (defaut du 15/09/2026, deux fenetres a l'ecran,
    constate par l'utilisateur) : la premiere version masquait le dialogue
    (`hide()`) le temps de la designation, en transposant le motif d'ORing.
    Or `hide()` sur un dialogue en cours d'`exec()` TERMINE sa boucle
    modale. La boucle imbriquee retardait la sortie, mais des que le
    gestionnaire rendait la main, `exec()` retournait Rejected :
    `configuration()` rendait None, `main()` rebouclait et reconstruisait un
    dialogue — pendant que l'ancien, reaffiche par `show()`, restait
    orphelin a l'ecran. Deux fenetres « Representation du ressort ».

    La manipulation de modalite est donc SUPPRIMEE plutot que rafistolee.
    Le dialogue se ferme VOLONTAIREMENT (`done(CODE_DESIGNER_ARETE)`) ; la
    designation se fait alors qu'aucun dialogue modal n'est vivant, donc
    avec une vue 3D libre par construction ; puis le dialogue est
    reconstruit avec son etat et la hauteur mesuree.

    Signature et valeur de retour INCHANGEES pour l'appelant
    (SpringFull.FCMacro:1518) : un tuple, ou None si annule.
    """
    # L'instance designee par la selection QUI A LANCE LA MACRO, capturee
    # UNE SEULE FOIS : des la premiere designation d'arete, la selection
    # aura change et l'information serait perdue.
    instance = _instanceDepuisSelection(getattr(data, 'body', None))
    report = None

    while True:
        resultat = _configurationUnePasse(data, report, instance)
        if not (isinstance(resultat, dict)
                and resultat.get("action") == "arete"):
            return resultat

        report = dict(resultat)
        report["action"] = None

        placement, info = _placementMondeRessort(
            getattr(data, 'body', None), instance)
        if placement is None:
            if str(info).startswith("instances multiples:"):
                msg = tr("repr.h_instances", n=str(info).split(":")[-1])
            else:
                msg = tr("repr.h_unknown") + "  (" + str(info) + ")"
            _journal("placement du ressort indisponible : %s" % info)
            report["message"] = msg
            _avertir(msg)
            continue

        _journal("repere du ressort obtenu par : %s" % info)
        panneau = _panneauDesignationArete(placement,
                                           resultat["lc_min"], resultat["l0"])
        # Aucun dialogue modal n'est vivant ici : la vue 3D est libre par
        # construction, sans toucher a WA_ShowModal ni masquer quoi que ce soit.
        if _afficherNonModal3D(panneau, None) == QDialogAccepted \
                and panneau.mesure is not None:
            report["mesure"] = panneau.mesure


def _avertir(message):
    """Un refus s'annonce. Une etiquette grise ne se voit pas (15/09/2026)."""
    boite = QtGui.QMessageBox()
    boite.setWindowTitle(tr("repr.pick_title"))
    boite.setIcon(QMsgBoxInformation)
    boite.setText(message)
    boite.setStandardButtons(QMsgBoxOk)
    boite.exec()


def _configurationUnePasse(data, report=None, instance=None):
    """
    Dialogue de configuration de la représentation du ressort.
    Permet de choisir le mode de représentation et le type simplifié/complet.
    
    CORRECTION v1.3: Utilise les 3 hauteurs stockées:
    - freeLength (L0): mode libre
    - onLoadHight (H): mode sous charge  
    - minHeight (Lc_max): mode bloc
    
    CORRECTION v1.4: Ajout hauteur définie par l'utilisateur
    CORRECTION v1.4.1: Ajout charge définie par l'utilisateur avec liaison hauteur/charge
    
    Args:
        data: DataSet object avec les données du ressort
        
    Returns:
        tuple: (displayHeight, displayActiveTurnsHight, turnsPitch, config_name) ou None si annulé
        - displayHeight: hauteur totale pour la représentation (position LCS Top)
        - displayActiveTurnsHight: hauteur des spires actives pour la représentation
        - turnsPitch: pas des spires actives
        - config_name: nom de la configuration choisie
    """
    dialog = QtGui.QDialog()
    dialog.setWindowTitle(tr("repr.window_title"))
    dialog.setMinimumWidth(480)
    
    layout = QtGui.QVBoxLayout()
    
    # Titre
    title = QtGui.QLabel(tr("repr.title"))
    title.setAlignment(QtCore.Qt.AlignCenter)
    title.setStyleSheet("font-weight: bold; font-size: 12pt;")
    layout.addWidget(title)
    
    # Configuration actuelle - lue depuis le code interne indépendant de la
    # langue (configurationMode), pas depuis le texte affiché stocké. Voir
    # _config_mode_to_display() et audit UX finding #4.
    current_mode = getattr(data, 'configurationMode', "LOADED") or "LOADED"
    if report and report.get("mode"):
        current_mode = report["mode"]
    current_config = _config_mode_to_display(
        current_mode,
        getattr(data, 'customHeight', 0.0),
        getattr(data, 'customForce', 0.0),
    )
    current_label = QtGui.QLabel(tr("repr.current") + " <b>" + current_config + "</b>")
    current_label.setAlignment(QtCore.Qt.AlignCenter)
    layout.addWidget(current_label)
    
    # Info sur les hauteurs
    L0 = getattr(data, 'freeLength', data.onLoadHight + 20)
    H = data.onLoadHight
    Lc_max = data.minHeight
    
    # Longueur spires jointes (solidHeight)
    Lc_min = getattr(data, 'solidHeight', Lc_max * 0.8)
    
    # Récupérer les données pour calculer la raideur
    d = getattr(data, 'wireDiameter', 4.0)
    Dm = getattr(data, 'meanDiameter', 20.0)
    n = getattr(data, 'activeTurnsQty', 7.0)
    
    # Récupérer le module G depuis la base de données ou utiliser une valeur par défaut
    material = getattr(data, 'material', 'CORDE A PIANO')
    
    # Importer DB pour obtenir le module G
    try:
        from SpringFull.SpringFullCalculatorModule import DB
        if DB.loaded:
            G = DB.get_module_G(material)
        else:
            G = 8150  # Valeur par défaut pour acier (daN/mm²)
    except:
        G = 8150  # Valeur par défaut
    
    # Calculer la raideur: R = (G × d⁴) / (8 × Dm³ × n) en daN/mm
    if Dm > 0 and n > 0:
        spring_rate = (G * (d ** 4)) / (8 * (Dm ** 3) * n)
    else:
        spring_rate = 1.0
    
    # Calculer la force nominale (à H sous charge)
    # F = R × (L0 - H)
    F_nominal = spring_rate * (L0 - H) if L0 > H else 0
    
    # Calculer la force max (à Lc_min - spires jointes)
    F_max = spring_rate * (L0 - Lc_min) if L0 > Lc_min else F_nominal * 2
    
    # Hauteur personnalisée précédente (si définie et valide)
    # Valeur par défaut = H (hauteur sous charge)
    previous_custom = getattr(data, 'customHeight', 0.0)
    if previous_custom <= 0 or previous_custom < Lc_min or previous_custom > L0:
        previous_custom = H  # Valeur par défaut = hauteur sous charge
    
    # Charge personnalisée précédente (si définie et valide)
    # Valeur par défaut = F_nominal (charge nominale à H)
    previous_custom_force = getattr(data, 'customForce', 0.0)
    if previous_custom_force <= 0:
        previous_custom_force = F_nominal  # Valeur par défaut = charge nominale
    if previous_custom_force > F_max:
        previous_custom_force = F_max
    
    # S'assurer que les valeurs sont synchronisées si aucune n'a été définie
    # (première utilisation ou valeurs non initialisées)
    stored_height = getattr(data, 'customHeight', 0.0)
    stored_force = getattr(data, 'customForce', 0.0)
    
    if stored_height <= 0 and stored_force <= 0:
        # Aucune valeur stockée: utiliser H et F_nominal (synchronisés)
        previous_custom = H
        previous_custom_force = F_nominal
    elif stored_height > 0 and stored_force <= 0:
        # Hauteur stockée mais pas la charge: calculer la charge correspondante
        previous_custom_force = spring_rate * (L0 - previous_custom) if spring_rate > 0 else F_nominal
    elif stored_force > 0 and stored_height <= 0:
        # Charge stockée mais pas la hauteur: calculer la hauteur correspondante
        previous_custom = L0 - stored_force / spring_rate if spring_rate > 0 else H
        if previous_custom < Lc_min:
            previous_custom = Lc_min
        if previous_custom > L0:
            previous_custom = L0
    
    # Reprise de la passe precedente : l'utilisateur ne doit rien retrouver
    # de change hormis ce qu'il a demande.
    if report:
        if report.get("hauteur"):
            previous_custom = report["hauteur"]
        if report.get("force"):
            previous_custom_force = report["force"]
        _m = report.get("mesure")
        if _m and not _m[2].get("bloquant"):
            previous_custom = _m[0]

    info_text = "<i>" + tr("repr.info_heights").format(L0=L0, H=H, Lc=Lc_max) + "</i>"
    info_label = QtGui.QLabel(info_text)
    info_label.setAlignment(QtCore.Qt.AlignCenter)
    info_label.setStyleSheet("color: #666;")
    layout.addWidget(info_label)
    
    layout.addSpacing(15)
    
    # === GROUPE TYPE DE REPRÉSENTATION ===
    config_group = QtGui.QGroupBox(tr("repr.type_group"))
    config_layout = QtGui.QVBoxLayout()
    
    radio_libre = QtGui.QRadioButton(tr("repr.free").format(L0=L0))
    radio_sous_charge = QtGui.QRadioButton(tr("repr.loaded").format(H=H))
    radio_bloc = QtGui.QRadioButton(tr("repr.solid").format(Lc=Lc_max))
    
    # Option hauteur personnalisée
    radio_custom = QtGui.QRadioButton(tr("repr.custom_height"))
    
    # Layout horizontal pour le spinbox hauteur
    custom_layout = QtGui.QHBoxLayout()
    custom_layout.addSpacing(25)  # Indentation
    spin_custom = QtGui.QDoubleSpinBox()
    spin_custom.setRange(Lc_min, L0)  # Entre longueur spires jointes et longueur libre
    spin_custom.setDecimals(2)
    spin_custom.setSingleStep(1.0)
    spin_custom.setValue(previous_custom)  # Valeur précédente ou H par défaut
    spin_custom.setSuffix(" mm")
    spin_custom.setMinimumWidth(120)
    spin_custom.setEnabled(False)  # Désactivé par défaut
    custom_layout.addWidget(spin_custom)
    btn_arete = QtGui.QPushButton(tr("repr.pick_edge"))
    btn_arete.setToolTip(tr("repr.pick_edge_tooltip"))
    btn_arete.setEnabled(False)
    custom_layout.addWidget(btn_arete)
    custom_layout.addStretch()
    
    # Option charge personnalisée
    radio_custom_force = QtGui.QRadioButton(tr("repr.custom_force"))
    
    # Layout horizontal pour le spinbox charge
    custom_force_layout = QtGui.QHBoxLayout()
    custom_force_layout.addSpacing(25)  # Indentation
    spin_custom_force = QtGui.QDoubleSpinBox()
    spin_custom_force.setRange(0, F_max)  # Entre 0 et force max
    spin_custom_force.setDecimals(2)
    spin_custom_force.setSingleStep(1.0)
    spin_custom_force.setValue(previous_custom_force)
    spin_custom_force.setSuffix(" daN")
    spin_custom_force.setMinimumWidth(120)
    spin_custom_force.setEnabled(False)  # Désactivé par défaut
    custom_force_layout.addWidget(spin_custom_force)
    custom_force_layout.addStretch()
    
    # Variable pour éviter les boucles infinies lors de la mise à jour
    updating_values = [False]
    
    # Sélection selon le mode de configuration actuel (code interne
    # indépendant de la langue - voir audit UX finding #4). Comparaison
    # directe, sans plus jamais reparser un texte affiché traduit.
    if current_mode == "FREE":
        radio_libre.setChecked(True)
    elif current_mode == "SOLID":
        radio_bloc.setChecked(True)
    elif current_mode == "CUSTOM_FORCE":
        radio_custom_force.setChecked(True)
        spin_custom_force.setEnabled(True)
    elif current_mode == "CUSTOM_HEIGHT":
        radio_custom.setChecked(True)
        spin_custom.setEnabled(True)
    else:
        # "LOADED" et toute valeur inconnue/absente (compatibilité)
        radio_sous_charge.setChecked(True)
    
    # Connecter les signaux pour activer/désactiver les spinbox
    # Etat de la derniere mesure. `bloquant` interdit la validation tant
    # qu'il tient ; il est leve des que l'utilisateur reprend la main sur la
    # valeur (saisie au clavier) ou change de mode — sans quoi un refus
    # resterait colle a un chiffre qu'il vient de corriger.
    etat_mesure = {"bloquant": False}
    # Etat rendu a l'enveloppe quand l'utilisateur demande une designation.
    sortie = {}

    def on_radio_changed():
        spin_custom.setEnabled(radio_custom.isChecked())
        spin_custom_force.setEnabled(radio_custom_force.isChecked())
        btn_arete.setEnabled(radio_custom.isChecked())
        if not radio_custom.isChecked():
            etat_mesure["bloquant"] = False
            lbl_mesure.setVisible(False)
    
    # Liaison charge <-> hauteur
    def on_height_changed(value):
        if updating_values[0]:
            return
        updating_values[0] = True
        # Calculer la force correspondante: F = k * (L0 - H)
        force = spring_rate * (L0 - value)
        if force < 0:
            force = 0
        if force > F_max:
            force = F_max
        spin_custom_force.setValue(force)
        updating_values[0] = False
    
    def on_force_changed(value):
        if updating_values[0]:
            return
        updating_values[0] = True
        # Calculer la hauteur correspondante: H = L0 - F/k
        if spring_rate > 0:
            height = L0 - value / spring_rate
        else:
            height = L0
        if height < Lc_min:
            height = Lc_min
        if height > L0:
            height = L0
        spin_custom.setValue(height)
        updating_values[0] = False
    
    radio_libre.toggled.connect(on_radio_changed)
    radio_sous_charge.toggled.connect(on_radio_changed)
    radio_bloc.toggled.connect(on_radio_changed)
    radio_custom.toggled.connect(on_radio_changed)
    radio_custom_force.toggled.connect(on_radio_changed)
    
    def on_saisie_manuelle(_valeur):
        # La valeur ne vient plus de la mesure : le verdict qui la bloquait
        # ne la concerne plus.
        etat_mesure["bloquant"] = False

    spin_custom.valueChanged.connect(on_height_changed)
    spin_custom.valueChanged.connect(on_saisie_manuelle)
    spin_custom_force.valueChanged.connect(on_force_changed)
    
    def _mode_courant():
        if radio_libre.isChecked():
            return "FREE"
        if radio_bloc.isChecked():
            return "SOLID"
        if radio_custom.isChecked():
            return "CUSTOM_HEIGHT"
        if radio_custom_force.isChecked():
            return "CUSTOM_FORCE"
        return "LOADED"

    def on_choisir_arete():
        # On FERME la passe : c'est l'enveloppe qui mene la designation,
        # hors de toute modalite. Ne jamais masquer un dialogue en exec().
        sortie["action"] = "arete"
        sortie["mode"] = _mode_courant()
        sortie["hauteur"] = spin_custom.value()
        sortie["force"] = spin_custom_force.value()
        sortie["detaille"] = checkbox_detailed.isChecked()
        dialog.done(CODE_DESIGNER_ARETE)

    btn_arete.clicked.connect(on_choisir_arete)

    # === SYNCHRONISATION INITIALE ===
    # Recalculer les valeurs initiales basées sur les données actuelles du ressort
    # La hauteur personnalisée par défaut est H (sous charge)
    initial_height = previous_custom if previous_custom >= Lc_min and previous_custom <= L0 else H
    initial_force = spring_rate * (L0 - initial_height) if spring_rate > 0 else F_nominal
    
    # Borner les valeurs
    if initial_force < 0:
        initial_force = 0
    if initial_force > F_max:
        initial_force = F_max
    
    # Mettre à jour les spinbox sans déclencher les callbacks
    updating_values[0] = True
    spin_custom.setValue(initial_height)
    spin_custom_force.setValue(initial_force)
    updating_values[0] = False
    
    config_layout.addWidget(radio_libre)
    config_layout.addWidget(radio_sous_charge)
    config_layout.addWidget(radio_bloc)
    config_layout.addWidget(radio_custom)
    config_layout.addLayout(custom_layout)
    lbl_mesure = QtGui.QLabel("")
    lbl_mesure.setWordWrap(True)
    lbl_mesure.setStyleSheet("color: #888; padding-left: 25px;")
    lbl_mesure.setVisible(False)
    config_layout.addWidget(lbl_mesure)
    config_layout.addSpacing(5)
    config_layout.addWidget(radio_custom_force)
    config_layout.addLayout(custom_force_layout)
    config_group.setLayout(config_layout)
    layout.addWidget(config_group)
    
    layout.addSpacing(10)
    
    # === GROUPE MODE SIMPLIFIÉ ===
    simplified_group = QtGui.QGroupBox(tr("repr.mode_group"))
    simplified_layout = QtGui.QVBoxLayout()
    
    checkbox_detailed = QtGui.QCheckBox(tr("repr.detailed"))
    checkbox_detailed.setToolTip(tr("repr.detailed_tooltip"))
    
    # État actuel (par défaut simplifié)
    simplified = getattr(data, 'simplified', True)
    if report and report.get("detaille") is not None:
        simplified = not report["detaille"]
    checkbox_detailed.setChecked(not simplified)
    
    simplified_layout.addWidget(checkbox_detailed)
    simplified_group.setLayout(simplified_layout)
    layout.addWidget(simplified_group)
    
    layout.addSpacing(20)
    
    # === ETAT INITIAL DES COMMANDES ===
    # DERIVER l'etat des widgets des boutons radio, au lieu de le recopier a
    # la main dans chaque branche de mode.
    #
    # POURQUOI (defaut du 15/09/2026, signale par l'utilisateur : « le bouton
    # Selectionnez une arete est desactive, il faut passer dans un autre mode
    # puis revenir pour le reactiver ») : `on_radio_changed` est branche sur
    # `toggled`, donc APRES les `setChecked()` d'initialisation. A l'ouverture
    # il ne tourne jamais. `spin_custom` s'en tirait parce que sa branche de
    # mode l'active explicitement ; le bouton d'arete, ajoute plus tard, ne
    # beneficiait pas de cette redondance — et c'est la redondance, pas
    # l'oubli, qui etait le vrai defaut.
    #
    # Un seul appel ici, une fois tous les widgets construits, et l'etat
    # initial decoule du meme critere que l'etat courant. Placé AVANT la
    # restitution, qui doit garder le dernier mot.
    on_radio_changed()

    # === RESTITUTION DE LA PASSE PRECEDENTE ===
    # Ici et pas plus haut : lbl_mesure n'existe qu'a partir du groupe
    # « type de representation », donc apres les gestionnaires.
    if report and report.get("message"):
        lbl_mesure.setVisible(True)
        lbl_mesure.setText("<b>" + report["message"] + "</b>")
        lbl_mesure.setStyleSheet("color: #c0392b; padding-left: 25px;")
    elif report and report.get("mesure"):
        _h, _eta, _verdict = report["mesure"]
        _texte = messageVerdictHauteur(_h, _eta, _verdict, Lc_min, L0)
        _bloquant = bool(_verdict.get("bloquant"))
        lbl_mesure.setVisible(True)
        lbl_mesure.setText(("<b>" + _texte + "</b>") if _bloquant else _texte)
        lbl_mesure.setStyleSheet(
            "color: #c0392b; padding-left: 25px;" if _bloquant
            else "color: #888; padding-left: 25px;")
        etat_mesure["bloquant"] = _bloquant
        if not _bloquant:
            # REGLE DU §2 : une valeur hors bornes ne touche JAMAIS le
            # spinbox — setRange() l'ecreterait en silence et l'alerte
            # deviendrait structurellement inatteignable.
            radio_custom.setChecked(True)
            spin_custom.setEnabled(True)
            btn_arete.setEnabled(True)
            updating_values[0] = True
            spin_custom.setValue(_h)
            spin_custom_force.setValue(
                spring_rate * (L0 - _h) if spring_rate > 0 else 0.0)
            updating_values[0] = False
            etat_mesure["bloquant"] = False

    # === BOUTONS ===
    button_layout = QtGui.QHBoxLayout()
    ok_button = QtGui.QPushButton(tr("common.ok"))
    cancel_button = QtGui.QPushButton(tr("common.cancel"))
    
    def on_valider():
        # Decision de l'utilisateur du 15/09 : hors bornes = BLOQUANT.
        # On affiche toujours, on n'actualise que sur une base saine.
        if radio_custom.isChecked() and etat_mesure.get("bloquant"):
            lbl_mesure.setVisible(True)
            lbl_mesure.setText(lbl_mesure.text() + "<br><b>"
                               + tr("repr.h_blocked") + "</b>")
            return
        dialog.accept()

    ok_button.clicked.connect(on_valider)
    cancel_button.clicked.connect(dialog.reject)
    
    button_layout.addStretch()
    button_layout.addWidget(ok_button)
    button_layout.addWidget(cancel_button)
    layout.addLayout(button_layout)
    
    dialog.setLayout(layout)
    
    # Exécution
    result = dialog.exec()

    if result == CODE_DESIGNER_ARETE:
        # Pas une annulation : une demande de designation. On rend l'etat
        # des widgets pour que la passe suivante le restitue a l'identique.
        sortie["lc_min"] = Lc_min
        sortie["l0"] = L0
        return sortie
    
    if result == QDialogAccepted:
        # CORRECTION v1.3: Utiliser directement les hauteurs stockées
        # - displayHeight = position du LCS Top
        # - displayActiveTurnsHight = hauteur des spires actives (pour calcul du pas)
        
        d = data.wireDiameter
        nm = data.deadTurnsQty
        n = data.activeTurnsQty

        # Déterminer si meulées
        is_ground = getattr(data, 'grinded', False)
        if not is_ground and hasattr(data, 'extremeTurns'):
            is_ground = "MEULEES" in data.extremeTurns.upper()

        # v1.5: deadTurnsQty = valeur de fabrication (inclut +0.25 par côté pour
        # les types meulés). La hauteur VISIBLE des spires mortes après meulage
        # est basée sur la valeur mécanique nm_mech = nm_manuf - 0.25.
        EXTRA_DEAD_TURNS_270 = 0.25
        if is_ground:
            nm_mech = max(0.0, nm - EXTRA_DEAD_TURNS_270)
        else:
            nm_mech = nm

        # Hauteur des spires mortes visibles (total 2 faces, après meulage)
        deadTurnsHightTotal = 2 * nm_mech * d
        
        if radio_libre.isChecked():
            # Mode libre: LCS à L0
            displayHeight = L0
            config_name = tr("repr.config_free")
            data.configurationMode = "FREE"
        elif radio_bloc.isChecked():
            # Mode bloc: LCS à Lc_max
            displayHeight = Lc_max
            config_name = tr("repr.config_solid")
            data.configurationMode = "SOLID"
        elif radio_custom.isChecked():
            # Mode hauteur personnalisée
            displayHeight = spin_custom.value()
            config_name = tr("repr.config_custom_height").format(displayHeight)
            data.configurationMode = "CUSTOM_HEIGHT"
            # Sauvegarder les deux valeurs synchronisées pour la prochaine fois
            data.customHeight = displayHeight
            # Calculer et sauvegarder la charge correspondante
            if spring_rate > 0:
                data.customForce = spring_rate * (L0 - displayHeight)
            else:
                data.customForce = F_nominal
        elif radio_custom_force.isChecked():
            # Mode charge personnalisée
            custom_force = spin_custom_force.value()
            # Calculer la hauteur correspondante
            if spring_rate > 0:
                displayHeight = L0 - custom_force / spring_rate
            else:
                displayHeight = H
            # Borner la hauteur
            if displayHeight < Lc_min:
                displayHeight = Lc_min
            if displayHeight > L0:
                displayHeight = L0
            config_name = tr("repr.config_custom_force").format(custom_force)
            data.configurationMode = "CUSTOM_FORCE"
            # Sauvegarder les deux valeurs synchronisées pour la prochaine fois
            data.customForce = custom_force
            data.customHeight = displayHeight
        else:
            # Mode sous charge: LCS à H
            displayHeight = H
            config_name = tr("repr.config_loaded")
            data.configurationMode = "LOADED"
        
        # Calculer displayActiveTurnsHight selon le type d'extrémité
        # Pour MEULEES et RAPPROCHEES_MEULEES: displayHeight = nt * d
        # Pour COUPEES et RAPPROCHEES: displayHeight = (nt + 1) * d
        if is_ground:
            displayActiveTurnsHight = displayHeight - deadTurnsHightTotal
        else:
            displayActiveTurnsHight = displayHeight - deadTurnsHightTotal - d
        
        # Mode simplifié (inversé: checkbox cochée = détaillé = NOT simplified)
        data.simplified = not checkbox_detailed.isChecked()
        
        # Mettre à jour la configuration (c'est juste le nom, pas les données de calcul)
        data.configuration = config_name
        
        # Calculer le pas
        turnsPitch = displayActiveTurnsHight / n if n > 0 else 0
        
        return (displayHeight, displayActiveTurnsHight, turnsPitch, config_name)
    else:
        # Annulé
        return None


def springUpdateDialog(data, piece, on_recalculate_callback=None):
    """
    Dialogue principal d'actualisation du ressort.
    Remplace l'ancien dialogue avec LibreOffice.
    
    Args:
        data: DataSet avec les données du ressort
        piece: Body FreeCAD du ressort
        on_recalculate_callback: Fonction à appeler pour ouvrir le calculateur
        
    Returns:
        str: Action choisie ('ok', 'recalculate', 'cancel')
    """
    # Déterminer le message selon l'état
    is_new = getattr(data, 'newSpring', False)
 
    if is_new:
        msg = tr("update.msg_create")
        button_text = tr("update.btn_create")
    else:
        msg = tr("update.msg_update")
        button_text = tr("update.btn_ok")
 
    dialog = QtGui.QDialog()
    dialog.setWindowTitle(tr("update.window_title"))
    dialog.setMinimumWidth(500)
    
    layout = QtGui.QVBoxLayout()
    
    # Message principal - entièrement traduit
    message = QtGui.QLabel(
        f"<center>{tr('update.main_msg').format(name=piece.Label.upper(), action=msg)}</center>"
    )
    message.setWordWrap(True)
    layout.addWidget(message)
    
    layout.addSpacing(10)
    
    # Configuration actuelle - lue depuis le code interne indépendant de la
    # langue (configurationMode). Voir _config_mode_to_display() et audit
    # UX finding #4.
    config_text = _config_mode_to_display(
        getattr(data, 'configurationMode', "LOADED") or "LOADED",
        getattr(data, 'customHeight', 0.0),
        getattr(data, 'customForce', 0.0),
    )
    config_label = QtGui.QLabel(
        f"<center>{tr('update.current_repr')} <font size=+1><b>{config_text}</b></font></center>"
    )
    layout.addWidget(config_label)
    
    # Info H sous charge
    h_sous_charge = getattr(data, 'onLoadHight', 0)
    h_label = QtGui.QLabel(
        f"<center><i>{tr('update.h_label').format(H=h_sous_charge)}</i></center>"
    )
    h_label.setStyleSheet("color: #666;")
    layout.addWidget(h_label)
    
    layout.addSpacing(20)
    
    # === BOUTONS ===
    button_layout = QtGui.QHBoxLayout()
    
    # Bouton Recalculer (remplace "Éditer données" -> LibreOffice)
    recalc_button = QtGui.QPushButton("🔢 " + tr("update.btn_recalc"))
    recalc_button.setToolTip(tr("update.btn_recalc_tooltip"))
    recalc_button.setMinimumWidth(120)
    
    # Bouton OK
    ok_button = QtGui.QPushButton(button_text)
    ok_button.setMinimumWidth(150)
    
    # Bouton Annuler
    cancel_button = QtGui.QPushButton(tr("update.btn_cancel"))
    cancel_button.setMinimumWidth(100)
    
    # Variable pour stocker le résultat
    dialog.result_action = 'cancel'
    
    def on_recalc():
        dialog.result_action = 'recalculate'
        dialog.accept()
    
    def on_ok():
        dialog.result_action = 'ok'
        dialog.accept()
    
    def on_cancel():
        dialog.result_action = 'cancel'
        dialog.reject()
    
    recalc_button.clicked.connect(on_recalc)
    ok_button.clicked.connect(on_ok)
    cancel_button.clicked.connect(on_cancel)
    
    button_layout.addWidget(recalc_button)
    button_layout.addStretch()
    button_layout.addWidget(ok_button)
    button_layout.addWidget(cancel_button)
    
    layout.addLayout(button_layout)
    dialog.setLayout(layout)
    
    # Exécution
    dialog.exec()
    
    return dialog.result_action


def entreesSelectionRessort(springs, links, doc_actif_nom):
    """Construit les entrées de la liste de choix : (libellé, objet, indenté).

    RÈGLE (14/09/2026, demande de l'utilisateur) : **on ne propose que ce qui
    est présent dans le document où l'utilisateur travaille.**

    Auparavant, chaque ressort était listé avec ses liens indentés dessous.
    Depuis un assemblage qui n'instancie qu'un ressort, cela donnait :

        📦 Spring003
            🔗 Spring003 (link)

    Deux entrées pour une seule chose — le Body source n'est pas dans
    l'assemblage, et le sélectionner ou sélectionner son lien mène au même
    Body de toute façon (`selectSpringDialog` résout le lien). L'utilisateur
    l'a dit sans détour : « une entrée est superflue ».

    D'où la règle :

      * un ressort **du document actif** est listé tel quel ;
      * un ressort atteint **par des liens** est représenté par **ses liens**,
        pas par son Body source — c'est le lien que l'utilisateur voit dans
        son arbre, et c'est son libellé qu'il reconnaît ;
      * plusieurs liens vers le même ressort restent plusieurs entrées : ce
        sont des instances distinctes de l'assemblage ;
      * un ressort hors document actif et sans aucun lien — cas qui ne
        devrait pas se produire — est listé quand même plutôt que perdu.

    Fonction séparée du dialogue pour être éprouvable hors FreeCAD
    (`_outils_claude/ESSAI_entrees_selection_springfull.py`).

    Args:
        springs: Bodies ressort (voir findSpringBodies)
        links: dict {body: [liens]} (voir findSpringLinks)
        doc_actif_nom: nom du document actif, ou None

    Returns:
        list de tuples (libellé_sans_icone, objet, est_un_lien)
    """
    links = links or {}
    entrees = []
    for spring in springs:
        try:
            local = (getattr(spring.Document, 'Name', None) == doc_actif_nom)
        except Exception:
            local = True
        liens = list(links.get(spring, []) or [])
        if local or not liens:
            entrees.append((spring.Label, spring, False))
            # Un ressort local n'a pas de lien vers lui-même ; s'il en a,
            # ils désignent la même chose et n'ajoutent rien.
            continue
        for lien in liens:
            entrees.append((lien.Label, lien, True))
    return entrees


def libelleSelectionRessort(entrees):
    """Rend (clé i18n, arguments) décrivant le CONTENU de la liste.

    CORRECTIF (14/09/2026, signalé par l'utilisateur) : le libellé annonçait
    « 1 ressort et 1 lien détecté » alors que la liste ne contenait **qu'une**
    entrée — le lien. Il décrivait ce que la macro avait *trouvé*, pas ce
    qu'elle *montrait*.

    Un compteur au-dessus d'une liste décrit la liste. S'il compte autre
    chose, il n'informe pas : il contredit ce que l'utilisateur a sous les
    yeux, et c'est lui qu'on croit avant le compteur.

    Trois cas, donc trois clés — dont `select.info_links`, ajoutée ce jour
    dans les cinq catalogues.
    """
    n_liens = sum(1 for _l, _o, k in entrees if k)
    n_ressorts = len(entrees) - n_liens
    if n_ressorts and n_liens:
        return 'select.info_with_links', {'springs': n_ressorts,
                                          'links': n_liens}
    if n_liens:
        return 'select.info_links', {'links': n_liens}
    return 'select.info_springs', {'springs': n_ressorts}


def selectSpringDialog(springs, links=None, geo_info=None):
    """
    Dialogue de sélection d'un ressort parmi plusieurs.
    Avec highlight du ressort via la sélection FreeCAD lors du survol.
    Affiche aussi les liens (App::Link) indentés sous leur ressort parent.

    Args:
        springs: Liste des Bodies ressorts disponibles
        links: Dict {body: [link1, link2, ...]} des liens vers les ressorts
        geo_info: dict optionnel {diameter, center, axis, is_arc}, issu de
                  SpringFull.FCMacro::detectSpringInsertionGeometry() — si
                  fourni, une option « créer un nouveau ressort positionné
                  sur cette géométrie » est ajoutée EN PREMIER dans la
                  liste (avant les ressorts existants), pour rester visible
                  même quand plusieurs ressorts existent déjà dans le
                  document. L'option « créer sans positionnement » reste
                  disponible séparément, en fin de liste, pour permettre de
                  créer un ressort à l'origine même si une géométrie a été
                  détectée. Si ``geo_info['is_lcs']`` est vrai (repère LCS
                  sélectionné directement plutôt qu'un arc/cercle), le
                  libellé de cette option omet le diamètre (non pertinent).

    Returns:
        tuple: (body_sélectionné, is_new, use_geo) ou (None, None, None) si
               annulé. ``use_geo`` n'a de sens que si ``is_new`` est True :
               indique si le nouveau ressort doit être positionné sur
               ``geo_info`` (True) ou créé sans positionnement particulier
               (False, Placement identité).
    """
    import FreeCAD as App
    import FreeCADGui as Gui

    if links is None:
        links = {s: [] for s in springs}

    if len(springs) == 0:
        return None, True, (geo_info is not None)

    # Sentinelles distinctes de None (déjà utilisé comme itemData pour les
    # ressorts/liens réels) pour distinguer les deux variantes de création.
    _NEW_ON_GEO = 'NEW_ON_GEO'
    _NEW_PLAIN = 'NEW_PLAIN'

    dialog = QtGui.QDialog()
    dialog.setWindowTitle(tr("select.window_title"))
    dialog.setMinimumWidth(450)

    # Les entrées d'abord : le libellé les décrit, le combo les affiche.
    # L'ordre compte — c'est en comptant autre chose que la liste que le
    # libellé annonçait « 1 ressort et 1 lien » pour une seule entrée.
    try:
        _doc_actif_nom = getattr(App.ActiveDocument, 'Name', None)
    except Exception:
        _doc_actif_nom = None
    _entrees = entreesSelectionRessort(springs, links, _doc_actif_nom)

    def select_object(obj):
        """Sélectionne un objet dans FreeCAD (highlight natif) — ignore les
        sentinelles de création (chaînes), qui ne sont pas des objets
        FreeCAD."""
        if obj is None or isinstance(obj, str):
            return
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(obj)
        try:
            Gui.ActiveDocument.ActiveView.viewSelection()
        except:
            pass
    
    def on_item_highlighted(index):
        """Appelé quand un item est survolé dans la liste déroulante"""
        if index >= 0:
            obj = combo.itemData(index)
            if obj is not None:
                select_object(obj)
    
    def on_selection_changed(index):
        """Appelé quand la sélection change (clic)"""
        obj = combo.itemData(index)
        select_object(obj)
    
    layout = QtGui.QVBoxLayout()
    
    # Label info avec compte ressorts et liens
    _cle_info, _args_info = libelleSelectionRessort(_entrees)
    info_text = tr(_cle_info).format(**_args_info)
    label = QtGui.QLabel(info_text)
    label.setAlignment(QtCore.Qt.AlignCenter)
    layout.addWidget(label)
    
    # Info survol
    hint_label = QtGui.QLabel(f"<i>{tr('select.hint_hover')}</i>")
    hint_label.setAlignment(QtCore.Qt.AlignCenter)
    hint_label.setStyleSheet("color: #888;")
    layout.addWidget(hint_label)
    
    layout.addSpacing(10)
    
    # ComboBox de sélection
    combo = QtGui.QComboBox()
    combo.setMinimumHeight(30)

    # Option « créer sur la géométrie détectée » — EN PREMIER dans la
    # liste, avant les ressorts existants, pour rester immédiatement
    # visible (demande utilisateur : ne pas la reléguer en fin de liste
    # derrière tous les ressorts déjà présents).
    if geo_info is not None:
        if geo_info.get('is_lcs'):
            _on_geo_label = tr('select.create_new_on_lcs')
        else:
            _on_geo_label = tr('select.create_new_on_geo').format(
                diam=geo_info.get('diameter', '?'))
        combo.addItem(f"🎯 {_on_geo_label}", _NEW_ON_GEO)
        combo.insertSeparator(combo.count())

    # Ajouter les entrées — un ressort local tel quel, un ressort lié
    # représenté par SES LIENS (voir entreesSelectionRessort).
    for _libelle, _obj, _est_lien in _entrees:
        combo.addItem(f"{'🔗' if _est_lien else '📦'} {_libelle}", _obj)

    # Option créer nouveau (sans positionnement particulier si une
    # géométrie a déjà été proposée en tête de liste — sinon seule option
    # de création disponible)
    combo.insertSeparator(combo.count())
    if geo_info is not None:
        combo.addItem(f"➕ {tr('select.create_new_no_geo')}", _NEW_PLAIN)
    else:
        combo.addItem(f"➕ {tr('select.create_new')}", _NEW_PLAIN)
    
    # Connecter le signal highlighted (survol dans la liste déroulante)
    combo.highlighted.connect(on_item_highlighted)
    
    # Connecter le signal de changement de sélection
    combo.currentIndexChanged.connect(on_selection_changed)
    
    layout.addWidget(combo)
    
    layout.addSpacing(10)
    
    # Boutons
    button_layout = QtGui.QHBoxLayout()
    ok_button = QtGui.QPushButton(tr("common.ok"))
    cancel_button = QtGui.QPushButton(tr("common.cancel"))
    
    ok_button.clicked.connect(dialog.accept)
    cancel_button.clicked.connect(dialog.reject)
    
    button_layout.addStretch()
    button_layout.addWidget(ok_button)
    button_layout.addWidget(cancel_button)
    layout.addLayout(button_layout)
    
    dialog.setLayout(layout)

    # Highlight initial : le premier ressort réel (select_object ignore
    # silencieusement l'entrée géométrie en tête de liste, qui est une
    # sentinelle et non un objet FreeCAD).
    if len(springs) > 0:
        first_obj = combo.itemData(0)
        if first_obj is not None:
            select_object(first_obj)

    # Exécuter le dialogue
    result = dialog.exec()

    if result == QDialogAccepted:
        selected = combo.itemData(combo.currentIndex())
        if selected == _NEW_ON_GEO:
            Gui.Selection.clearSelection()
            return None, True, True
        elif selected == _NEW_PLAIN:
            Gui.Selection.clearSelection()
            return None, True, False
        else:
            # Ressort existant - GARDER la sélection (highlight)
            # Si c'est un Link, retourner le Body source mais garder le link sélectionné
            body = selected
            if selected.TypeId == 'App::Link':
                body = getattr(selected, 'LinkedObject', selected)
            return body, False, False
    else:
        # Annulé - effacer la sélection
        Gui.Selection.clearSelection()
        return None, None, None


# NOTE (audit UX finding #9, v1.5): confirmReconstructDialog() a été
# retirée pour la même raison que dialogSpringCreated() ci-dessus - définie
# mais jamais appelée. Les clés dlg.confirm_rebuild_* restent disponibles.


def showStatusMessage(message, timeout=5000):
    """
    Affiche un message transitoire dans la barre de statut de FreeCAD, au
    lieu d'un dialogue modal à fermer par un clic.

    Utilisée depuis v1.5 pour l'accusé de succès après actualisation d'un
    ressort : la boucle principale peut déjà enchaîner "choix de
    représentation" -> reconstruction -> "succès" à chaque itération, ce
    qui fait beaucoup de clics pour un usage itératif typique (ajuster,
    observer, ajuster à nouveau). Voir audit UX finding #5. Inspirée du
    helper _status() de StandardPartSelector/config.py. showSuccessMessage()
    ci-dessous reste disponible si une confirmation modale est un jour
    nécessaire ailleurs.

    Args:
        message: texte déjà traduit à afficher
        timeout: durée d'affichage en millisecondes (0 = permanent)
    """
    try:
        import FreeCADGui as Gui
        mw = Gui.getMainWindow()
        if mw is not None:
            mw.statusBar().showMessage(message, timeout)
    except Exception:
        pass


def showSuccessMessage(spring_name):
    """
    Message de succes apres actualisation (dialogue modal).

    Conservée pour compatibilité / réutilisation éventuelle, mais n'est
    plus appelée dans le flux principal de SpringFull.FCMacro depuis
    v1.5 - voir showStatusMessage() ci-dessus.

    Args:
        spring_name: Nom du ressort
    """
    import FreeCADGui as Gui
    
    msgBox = QtGui.QMessageBox()
    msgBox.setWindowTitle(tr("dlg.success_title"))
    msgBox.setText(f"<center>{tr('dlg.success_msg').format(name=spring_name)}</center>")
    msgBox.setIcon(QMsgBoxInformation)
    msgBox.setStandardButtons(QMsgBoxOk)
    
    # Centrer sur la fenetre FreeCAD
    try:
        main_window = Gui.getMainWindow()
        if main_window:
            # Ramener FreeCAD au premier plan
            main_window.raise_()
            main_window.activateWindow()
            
            # Calculer la position centrale apres avoir defini la taille
            msgBox.adjustSize()
            main_geo = main_window.geometry()
            box_size = msgBox.sizeHint()
            x = main_geo.x() + (main_geo.width() - box_size.width()) // 2
            y = main_geo.y() + (main_geo.height() - box_size.height()) // 2
            msgBox.move(x, y)
    except:
        pass
    
    msgBox.exec()


class ProgressDialog(QtGui.QDialog):
    """
    Dialogue de progression pour les operations longues (reconstruction
    detaillee du ressort).

    Barre INDÉTERMINÉE ("marquee"), pas un pourcentage chiffré: pendant la
    reconstruction, le thread FreeCAD est bloqué, donc aucune mesure
    d'avancement réel n'est disponible. Un pourcentage animé par des
    pauses scriptées (comme précédemment) ajoute une latence artificielle
    à chaque reconstruction et peut donner une fausse impression de
    précision ("presque fini" alors que rien n'a commencé, ou l'inverse).
    Voir audit UX finding #6. Qt anime nativement une QProgressBar dont
    min == max == 0, sans code de minuterie ni time.sleep() ici.
    """

    def __init__(self, parent=None, title=None, message=None):
        super().__init__(parent)
        if title is None:
            title = tr("progress.title")
        if message is None:
            message = tr("progress.message")
        self.setWindowTitle(title)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowTitleHint)
        self.setFixedSize(420, 140)

        # Layout principal
        layout = QtGui.QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(25, 20, 25, 20)

        # Label message
        self.label = QtGui.QLabel(message)
        self.label.setWordWrap(True)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 10pt;")
        layout.addWidget(self.label)

        # Barre de progression indéterminée (convention Qt: min == max == 0)
        self.progress = QtGui.QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(20)
        layout.addWidget(self.progress)

        self.setLayout(layout)

        # Centrer sur FreeCAD
        self._center_on_freecad()

    def _center_on_freecad(self):
        """Centre le dialogue sur la fenetre FreeCAD."""
        import FreeCADGui as Gui
        try:
            main_window = Gui.getMainWindow()
            if main_window:
                main_geo = main_window.geometry()
                x = main_geo.x() + (main_geo.width() - self.width()) // 2
                y = main_geo.y() + (main_geo.height() - self.height()) // 2
                self.move(x, y)
        except:
            pass

    def finish(self):
        """Bascule en mode déterminé à 100% juste avant la fermeture."""
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        QtGui.QApplication.processEvents()

    def set_message(self, message):
        """Met a jour le message affiche."""
        self.label.setText(message)
        QtGui.QApplication.processEvents()


def showProgressDialog(title=None, message=None):
    """
    Cree et affiche un dialogue de progression (barre indéterminée).

    Args:
        title: Titre de la fenetre
        message: Message a afficher

    Returns:
        ProgressDialog: Le dialogue (a fermer avec .close())
    """
    import FreeCADGui as Gui

    if title is None:
        title = tr("progress.title")
    if message is None:
        message = tr("progress.message")

    dialog = ProgressDialog(Gui.getMainWindow(), title, message)

    # Afficher et mettre au premier plan
    dialog.show()
    dialog.raise_()
    dialog.activateWindow()
    # Laisser Qt peindre la fenêtre et démarrer l'animation de la barre
    # indéterminée avant que le thread ne se bloque pour la reconstruction.
    QtGui.QApplication.processEvents()

    return dialog

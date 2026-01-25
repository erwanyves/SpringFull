# -*- coding: utf-8 -*-
"""
SpringFullDialogsModule - Dialogues pour SpringFull
Version sans LibreOffice, avec intégration du calculateur

Version: 1.1 - Correction du bug onLoadHight: séparation hauteur calcul/affichage
"""

__author__ = "Yves Guillou"
__licence__ = "GPL"

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
    PYSIDE6 = False

# Import du module d'internationalisation
from SpringFull.SpringFullI18nModule import tr


def dialogSpringCreated(spring_name):
    """
    Dialogue affiché après la création d'un nouveau ressort.
    
    Args:
        spring_name: Nom du ressort créé
    """
    msgBox = QtGui.QMessageBox()
    msgBox.setWindowTitle(tr("dlg.spring_created_title"))
    msgBox.setText(f"<center>{tr('dlg.spring_created_msg').format(name=spring_name)}</center>")
    msgBox.setInformativeText(f"<center>{tr('dlg.spring_created_info')}</center>")
    msgBox.setStandardButtons(QMsgBoxOk)
    msgBox.exec()


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


def configuration(data):
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
    
    # Configuration actuelle - traduire si nécessaire
    current_config_raw = getattr(data, 'configuration', "")
    
    # Fonction pour traduire une configuration stockée
    def translate_config(config_str):
        """Traduit une configuration stockée vers la langue courante.
        
        Reconnaît les termes dans toutes les langues supportées:
        - FR: libre, bloc, sous charge, hauteur définie, charge définie
        - EN: free, solid, loaded, custom height, custom load/force
        - DE: frei, block, belastet, benutzerdefiniert
        - ES: libre, bloque, bajo carga, personalizada
        - IT: libera, blocco, sotto carico, personalizzata
        """
        if not config_str:
            return tr("repr.config_loaded")
        config_lower = config_str.lower()
        
        # === FREE SPRING ===
        # FR: libre | EN: free | DE: frei | ES: libre | IT: libera
        free_terms = ["libre", "free", "frei", "libera"]
        if any(term in config_lower for term in free_terms):
            return tr("repr.config_free")
        
        # === SOLID HEIGHT ===
        # FR: bloc | EN: solid | DE: block | ES: bloque | IT: blocco
        solid_terms = ["bloc", "solid", "block", "bloque", "blocco"]
        if any(term in config_lower for term in solid_terms):
            return tr("repr.config_solid")
        
        # === CUSTOM FORCE/LOAD ===
        # FR: charge définie | EN: custom load/force | DE: benutzerdefinierte last
        # ES: carga personalizada | IT: carico personalizzato
        force_terms = ["charge definie", "custom load", "custom force", "defined load",
                       "benutzerdefinierte last", "carga personalizada", "carico personalizzato"]
        if any(term in config_lower for term in force_terms):
            import re
            match = re.search(r'[\d.,]+', config_str)
            if match:
                value = float(match.group().replace(',', '.'))
                return tr("repr.config_custom_force").format(value)
            return tr("repr.config_custom_force").format(0)
        
        # === CUSTOM HEIGHT ===
        # FR: hauteur définie | EN: custom height | DE: benutzerdefinierte höhe
        # ES: altura personalizada | IT: altezza personalizzata
        height_terms = ["hauteur", "height", "höhe", "altura", "altezza", 
                        "personnalis", "custom", "benutzerdefiniert", "personaliza"]
        if any(term in config_lower for term in height_terms):
            import re
            match = re.search(r'[\d.,]+', config_str)
            if match:
                value = float(match.group().replace(',', '.'))
                return tr("repr.config_custom_height").format(value)
            return tr("repr.config_custom_height").format(0)
        
        # === LOADED SPRING (default) ===
        # FR: sous charge | EN: loaded | DE: belastet | ES: bajo carga | IT: sotto carico
        # Si rien d'autre ne correspond, c'est probablement "loaded"
        return tr("repr.config_loaded")
    
    current_config = translate_config(current_config_raw)
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
    
    # Sélection selon configuration actuelle (utilise current_config qui est déjà traduit)
    # On compare avec les termes de la langue courante
    config_lower = current_config.lower()
    
    # Termes pour chaque type dans toutes les langues
    free_terms = ["libre", "free", "frei", "libera"]
    solid_terms = ["bloc", "solid", "block", "bloque", "blocco"]
    force_terms = ["charge", "force", "load", "last", "carga", "carico"]
    height_terms = ["hauteur", "height", "höhe", "altura", "altezza"]
    
    if any(term in config_lower for term in free_terms):
        radio_libre.setChecked(True)
    elif any(term in config_lower for term in solid_terms):
        radio_bloc.setChecked(True)
    elif any(term in config_lower for term in force_terms) and "personnalis" not in config_lower:
        # Force/charge définie (mais pas "sous charge")
        if any(term in config_lower for term in ["definie", "custom", "defined", "benutzerdefiniert", "personaliza"]):
            radio_custom_force.setChecked(True)
            spin_custom_force.setEnabled(True)
        else:
            radio_sous_charge.setChecked(True)
    elif any(term in config_lower for term in height_terms) or "personnalis" in config_lower or "custom" in config_lower or "benutzerdefiniert" in config_lower:
        radio_custom.setChecked(True)
        spin_custom.setEnabled(True)
    else:
        radio_sous_charge.setChecked(True)
    
    # Connecter les signaux pour activer/désactiver les spinbox
    def on_radio_changed():
        spin_custom.setEnabled(radio_custom.isChecked())
        spin_custom_force.setEnabled(radio_custom_force.isChecked())
    
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
    
    spin_custom.valueChanged.connect(on_height_changed)
    spin_custom_force.valueChanged.connect(on_force_changed)
    
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
    checkbox_detailed.setChecked(not simplified)
    
    simplified_layout.addWidget(checkbox_detailed)
    simplified_group.setLayout(simplified_layout)
    layout.addWidget(simplified_group)
    
    layout.addSpacing(20)
    
    # === BOUTONS ===
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
    
    # Exécution
    result = dialog.exec()
    
    if result == QDialogAccepted:
        # CORRECTION v1.3: Utiliser directement les hauteurs stockées
        # - displayHeight = position du LCS Top
        # - displayActiveTurnsHight = hauteur des spires actives (pour calcul du pas)
        
        d = data.wireDiameter
        nm = data.deadTurnsQty
        n = data.activeTurnsQty
        
        # Hauteur des spires mortes (total 2 faces)
        deadTurnsHightTotal = 2 * nm * d
        
        # Déterminer si meulées
        is_ground = getattr(data, 'grinded', False)
        if not is_ground and hasattr(data, 'extremeTurns'):
            is_ground = "MEULEES" in data.extremeTurns.upper()
        
        if radio_libre.isChecked():
            # Mode libre: LCS à L0
            displayHeight = L0
            config_name = tr("repr.config_free")
        elif radio_bloc.isChecked():
            # Mode bloc: LCS à Lc_max
            displayHeight = Lc_max
            config_name = tr("repr.config_solid")
        elif radio_custom.isChecked():
            # Mode hauteur personnalisée
            displayHeight = spin_custom.value()
            config_name = tr("repr.config_custom_height").format(displayHeight)
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
            # Sauvegarder les deux valeurs synchronisées pour la prochaine fois
            data.customForce = custom_force
            data.customHeight = displayHeight
        else:
            # Mode sous charge: LCS à H
            displayHeight = H
            config_name = tr("repr.config_loaded")
        
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
    
    # Configuration actuelle - traduire si nécessaire
    config_raw = getattr(data, 'configuration', "")
    
    def translate_config(config_str):
        """Traduit une configuration stockée vers la langue courante.
        
        Reconnaît les termes dans toutes les langues supportées:
        - FR: libre, bloc, sous charge, hauteur définie, charge définie
        - EN: free, solid, loaded, custom height, custom load/force
        - DE: frei, block, belastet, benutzerdefiniert
        - ES: libre, bloque, bajo carga, personalizada
        - IT: libera, blocco, sotto carico, personalizzata
        """
        if not config_str:
            return tr("repr.config_loaded")
        config_lower = config_str.lower()
        
        # === FREE SPRING ===
        free_terms = ["libre", "free", "frei", "libera"]
        if any(term in config_lower for term in free_terms):
            return tr("repr.config_free")
        
        # === SOLID HEIGHT ===
        solid_terms = ["bloc", "solid", "block", "bloque", "blocco"]
        if any(term in config_lower for term in solid_terms):
            return tr("repr.config_solid")
        
        # === CUSTOM FORCE/LOAD ===
        force_terms = ["charge definie", "custom load", "custom force", "defined load",
                       "benutzerdefinierte last", "carga personalizada", "carico personalizzato"]
        if any(term in config_lower for term in force_terms):
            import re
            match = re.search(r'[\d.,]+', config_str)
            if match:
                value = float(match.group().replace(',', '.'))
                return tr("repr.config_custom_force").format(value)
            return tr("repr.config_custom_force").format(0)
        
        # === CUSTOM HEIGHT ===
        height_terms = ["hauteur", "height", "höhe", "altura", "altezza", 
                        "personnalis", "custom", "benutzerdefiniert", "personaliza"]
        if any(term in config_lower for term in height_terms):
            import re
            match = re.search(r'[\d.,]+', config_str)
            if match:
                value = float(match.group().replace(',', '.'))
                return tr("repr.config_custom_height").format(value)
            return tr("repr.config_custom_height").format(0)
        
        # === LOADED SPRING (default) ===
        return tr("repr.config_loaded")
    
    config_text = translate_config(config_raw)
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
    recalc_button.setToolTip(tr("update.btn_recalc_tooltip") if tr("update.btn_recalc_tooltip") != "update.btn_recalc_tooltip" else "Ouvrir le calculateur de ressort pour modifier les paramètres")
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


def selectSpringDialog(springs, links=None):
    """
    Dialogue de sélection d'un ressort parmi plusieurs.
    Avec highlight du ressort via la sélection FreeCAD lors du survol.
    Affiche aussi les liens (App::Link) indentés sous leur ressort parent.
    
    Args:
        springs: Liste des Bodies ressorts disponibles
        links: Dict {body: [link1, link2, ...]} des liens vers les ressorts
        
    Returns:
        tuple: (body_sélectionné, is_new) ou (None, None) si annulé
    """
    import FreeCAD as App
    import FreeCADGui as Gui
    
    if links is None:
        links = {s: [] for s in springs}
    
    if len(springs) == 0:
        return None, True
    
    dialog = QtGui.QDialog()
    dialog.setWindowTitle(tr("select.window_title"))
    dialog.setMinimumWidth(450)
    
    # Compter les liens
    total_links = sum(len(v) for v in links.values())
    
    def select_object(obj):
        """Sélectionne un objet dans FreeCAD (highlight natif)"""
        if obj is None:
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
    if total_links > 0:
        info_text = tr("select.info_with_links").format(springs=len(springs), links=total_links)
    else:
        info_text = tr("select.info_springs").format(springs=len(springs))
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
    
    # Ajouter les ressorts et leurs liens (indentés)
    for spring in springs:
        # Ajouter le ressort
        combo.addItem(f"📦 {spring.Label}", spring)
        
        # Ajouter les liens indentés
        for link in links.get(spring, []):
            combo.addItem(f"    🔗 {link.Label}", link)
    
    # Option créer nouveau
    combo.insertSeparator(combo.count())
    combo.addItem(f"➕ {tr('select.create_new')}", None)
    
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
    
    # Highlight initial du premier ressort
    if len(springs) > 0:
        first_obj = combo.itemData(0)
        if first_obj is not None:
            select_object(first_obj)
    
    # Exécuter le dialogue
    result = dialog.exec()
    
    if result == QDialogAccepted:
        selected = combo.itemData(combo.currentIndex())
        if selected is None:
            # Créer nouveau - effacer la sélection
            Gui.Selection.clearSelection()
            return None, True
        else:
            # Ressort existant - GARDER la sélection (highlight)
            # Si c'est un Link, retourner le Body source mais garder le link sélectionné
            body = selected
            if selected.TypeId == 'App::Link':
                body = getattr(selected, 'LinkedObject', selected)
            return body, False
    else:
        # Annulé - effacer la sélection
        Gui.Selection.clearSelection()
        return None, None


def confirmReconstructDialog(spring_name, changes_count):
    """
    Dialogue de confirmation avant reconstruction du ressort.
    
    Args:
        spring_name: Nom du ressort
        changes_count: Nombre de paramètres modifiés
        
    Returns:
        bool: True si confirmé
    """
    msgBox = QtGui.QMessageBox()
    msgBox.setWindowTitle(tr("dlg.confirm_rebuild_title"))
    msgBox.setText(f"<center>{tr('dlg.confirm_rebuild_msg').format(count=changes_count, name=spring_name)}</center>")
    msgBox.setInformativeText(f"<center>{tr('dlg.confirm_rebuild_info')}</center>")
    msgBox.setStandardButtons(QMsgBoxYes | QMsgBoxNo)
    msgBox.setDefaultButton(QMsgBoxYes)
    
    result = msgBox.exec()
    return result == QMsgBoxYes


def showSuccessMessage(spring_name):
    """
    Message de succes apres actualisation.
    Centre sur la fenetre FreeCAD.
    
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
    Dialogue de progression pour les operations longues.
    Affiche un message et une barre de progression animee.
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
        
        # Barre de progression
        self.progress = QtGui.QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFixedHeight(20)
        layout.addWidget(self.progress)
        
        self.setLayout(layout)
        
        # Timer pour l'animation
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._increment_progress)
        self.current_value = 0
        self.target_value = 90  # S'arrete a 90%
        
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
    
    def _increment_progress(self):
        """Incremente la barre de progression."""
        if self.current_value < self.target_value:
            self.current_value += 10
            self.progress.setValue(self.current_value)
            QtGui.QApplication.processEvents()
        else:
            self.timer.stop()
    
    def start_animation(self, interval_ms=800):
        """Demarre l'animation de la barre de progression."""
        self.current_value = 0
        self.progress.setValue(0)
        self.timer.start(interval_ms)
    
    def finish(self):
        """Termine la progression a 100% avec animation."""
        import time
        self.timer.stop()
        current = self.progress.value()
        # Animer de la valeur actuelle vers 100%
        for i in range(current, 105, 5):
            val = min(i, 100)
            self.progress.setValue(val)
            self.update()
            self.repaint()
            QtGui.QApplication.processEvents()
            time.sleep(0.05)
    
    def set_message(self, message):
        """Met a jour le message affiche."""
        self.label.setText(message)
        QtGui.QApplication.processEvents()
    
    def closeEvent(self, event):
        """Arrete le timer a la fermeture."""
        self.timer.stop()
        super().closeEvent(event)


def showProgressDialog(title=None, message=None):
    """
    Cree et affiche un dialogue de progression avec animation initiale.
    
    Args:
        title: Titre de la fenetre
        message: Message a afficher
        
    Returns:
        ProgressDialog: Le dialogue (a fermer avec .close())
    """
    import FreeCADGui as Gui
    import time
    
    if title is None:
        title = tr("progress.title")
    if message is None:
        message = tr("progress.message")
    
    dialog = ProgressDialog(Gui.getMainWindow(), title, message)
    
    # Afficher et mettre au premier plan
    dialog.show()
    dialog.raise_()
    dialog.activateWindow()
    
    # Animation initiale avant le travail lourd (0% -> 30%)
    # Car pendant la reconstruction, le thread est bloque
    for i in range(0, 35, 5):
        dialog.progress.setValue(i)
        dialog.update()
        dialog.repaint()
        QtGui.QApplication.processEvents()
        time.sleep(0.1)
    
    return dialog

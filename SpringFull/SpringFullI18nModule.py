# -*- coding: utf-8 -*-
"""
SpringFullI18nModule.py - Internationalization module for SpringFull

Manages English/French translations for all interface texts.
Automatic language detection from FreeCAD or system settings.

Reference language: English (en.json)
Translations: French (fr.json), and other languages

Version: 1.5.0 - Language choice persisted in lang.txt (single small config
file, inspired by ORing/lang.txt and StandardPartSelector/translate.txt):
the language dialog is now shown once, on first launch, then remembered
automatically. Replaces the previous Translate_on.txt/Translate_off.txt
timestamp mechanism (a developer-only switch that ended up exposed to end
users, and that reopened the dialog on every single launch unless a
developer kept "touching" one of the two files).
"""

import os
import json


# ---------------------------------------------------------------------------
# Traces de mise au point
# ---------------------------------------------------------------------------
# Quatre des neuf print() de ce module ne font que raconter le déroulement
# normal ("Language loaded", "Langue chargée depuis lang.txt", ...). Ils
# s'affichent à chaque lancement et noient les cinq autres, qui signalent de
# vrais problèmes : lang.txt illisible ou invalide, catalogue absent, écriture
# impossible.
#
# Porté d'ORing le 13/09/2026, mais PAS sous la même forme, et c'est
# délibéré. ORing filtre sur des sous-chaînes ("erreur", "AVERT", ...) parce
# qu'il compte plus de 300 appels et qu'on ne pouvait pas les trier un par un.
# Ce filtre est une heuristique : le relevé du 13/09/2026 a montré qu'il
# laissait tomber quinze avertissements réels d'ORing, et qu'appliqué ici il
# aurait éteint quatre des cinq lignes utiles ci-dessous ("valeur invalide",
# "Impossible d'ecrire", "Error loading", "File not found").
#
# Avec neuf appels, le critère juste est atteignable : c'est l'INTENTION DE
# L'AUTEUR qui décide, pas une loterie de sous-chaînes. Les lignes de
# déroulement passent par _trace(), les lignes de diagnostic restent en
# print(). Rien à deviner.
#
# La variable est lue À CHAQUE APPEL, pas à l'import : un module qui reste
# chargé entre deux lancements figerait sinon la valeur pour toute la session
# FreeCAD (défaut constaté sur ORing le même jour).
import os as _os_trace


def _trace(*args, **kwargs):
    """Trace de déroulement — silencieuse sauf si SPRINGFULL_DEBUG=1."""
    if _os_trace.environ.get('SPRINGFULL_DEBUG', '') not in (
            '', '0', 'false', 'False'):
        print(*args, **kwargs)


# Global variables for current language
_current_language = "en"
_translations = {}
_fallback_language = "en"  # English is the reference/fallback language


def get_module_path():
    """Retourne le chemin vers le dossier du module SpringFull."""
    return os.path.dirname(os.path.abspath(__file__))


def get_locales_path():
    """Retourne le chemin vers le dossier locales."""
    return os.path.join(get_module_path(), "locales")


def get_lang_file_path():
    """Retourne le chemin vers le fichier de préférence de langue (lang.txt)."""
    return os.path.join(get_module_path(), "lang.txt")


_LANG_FILE_HEADER = (
    "# SpringFull - language configuration / configuration de langue\n"
    "#\n"
    "# Language chosen the first time the macro ran; remembered automatically\n"
    "# from now on (no dialog on every launch).\n"
    "# Langue choisie au premier lancement de la macro ; memorisee\n"
    "# automatiquement (plus de dialogue a chaque lancement).\n"
    "#\n"
    "# To change the language: edit the code below directly\n"
    "# (en, fr, de, es, it), or set it to 'ask' to have the selection\n"
    "# dialog shown again on the next launch.\n"
    "# Pour changer de langue : modifiez directement le code ci-dessous\n"
    "# (en, fr, de, es, it), ou mettez 'ask' pour que le dialogue de\n"
    "# selection reapparaisse au prochain lancement.\n"
    "#\n"
)


def read_lang_preference():
    """
    Lit la préférence de langue stockée dans lang.txt.

    Returns:
        str ou None: le code langue (2 lettres), 'ask', ou None si le
        fichier est absent, vide, illisible ou contient une valeur
        invalide (dans ce dernier cas, on se rabat sur la detection
        automatique plutot que d'echouer silencieusement).
    """
    path = get_lang_file_path()
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                value = line.lower()
                if value == "ask":
                    return "ask"
                code = value[:2]
                if code.isalpha() and len(code) == 2:
                    return code
                print(f"[SpringFull I18n] lang.txt: valeur invalide '{line}' -> detection automatique")
                return None
        return None
    except OSError as e:
        print(f"[SpringFull I18n] Erreur lecture lang.txt: {e} -> detection automatique")
        return None


def write_lang_preference(lang):
    """
    Enregistre le code langue choisi dans lang.txt, avec un en-tête
    explicatif (bilingue, puisqu'écrit avant que la langue de
    l'utilisateur ne soit connue avec certitude).

    Args:
        lang: code langue à mémoriser (ex: "fr")
    """
    path = get_lang_file_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(_LANG_FILE_HEADER)
            f.write(lang + "\n")
        _trace(f"[SpringFull I18n] Langue enregistree dans lang.txt: {lang}")
    except OSError as e:
        print(f"[SpringFull I18n] Impossible d'ecrire lang.txt: {e}")


def detect_language():
    """
    Detects the language to use.
    Priority: FreeCAD > System > Default (en)
    
    Returns:
        str: Language code ("en", "fr", "de", "es", "it")
    """
    # Supported languages
    supported_languages = {
        "french": "fr", "français": "fr", "fr": "fr",
        "english": "en", "en": "en",
        "german": "de", "deutsch": "de", "de": "de",
        "spanish": "es", "español": "es", "es": "es",
        "italian": "it", "italiano": "it", "it": "it"
    }
    
    # Try to detect from FreeCAD
    try:
        import FreeCAD
        # FreeCAD parameters
        param = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/General")
        fc_language = param.GetString("Language", "")
        
        if fc_language:
            fc_lang_lower = fc_language.lower()
            # Check for exact match first
            for key, lang_code in supported_languages.items():
                if key in fc_lang_lower or fc_lang_lower.startswith(lang_code):
                    return lang_code
    except:
        pass
    
    # Try to detect from system
    try:
        import locale
        system_locale = locale.getdefaultlocale()[0]
        if system_locale:
            lang_prefix = system_locale[:2].lower()
            if lang_prefix in ["fr", "en", "de", "es", "it"]:
                return lang_prefix
    except:
        pass
    
    # Default: English
    return "en"


def load_translations(language=None):
    """
    Loads translations for a given language.
    
    Args:
        language: Language code ("en" or "fr"). If None, auto-detect.
    """
    global _current_language, _translations
    
    if language is None:
        language = detect_language()
    
    _current_language = language
    
    locales_path = get_locales_path()
    lang_file = os.path.join(locales_path, f"{language}.json")
    
    # Load the translation file
    if os.path.exists(lang_file):
        try:
            with open(lang_file, 'r', encoding='utf-8') as f:
                _translations = json.load(f)
            _trace(f"[SpringFull I18n] Language loaded: {language}")
        except Exception as e:
            print(f"[SpringFull I18n] Error loading {lang_file}: {e}")
            _translations = {}
    else:
        print(f"[SpringFull I18n] File not found: {lang_file}")
        _translations = {}
    
    # Load fallback (English) if different from current language
    if language != _fallback_language:
        fallback_file = os.path.join(locales_path, f"{_fallback_language}.json")
        if os.path.exists(fallback_file):
            try:
                with open(fallback_file, 'r', encoding='utf-8') as f:
                    fallback_trans = json.load(f)
                # Merge (current language has priority)
                for key, value in fallback_trans.items():
                    if key not in _translations:
                        _translations[key] = value
            except:
                pass


def tr(key, *args, **kwargs):
    """
    Traduit une clé en texte localisé.
    
    Args:
        key: Clé de traduction (ex: "dialog.ok")
        *args: Arguments pour le formatage (ex: tr("height.value", 50.0))
        **kwargs: Arguments nommés pour le formatage
        
    Returns:
        str: Texte traduit ou clé si non trouvée
    """
    global _translations
    
    # Charger les traductions si pas encore fait
    if not _translations:
        load_translations()
    
    # Récupérer la traduction
    text = _translations.get(key, key)
    
    # Appliquer le formatage si des arguments sont fournis
    if args or kwargs:
        try:
            text = text.format(*args, **kwargs)
        except:
            pass
    
    return text


def get_current_language():
    """Retourne la langue courante."""
    return _current_language


def set_language(language):
    """
    Change la langue courante.
    
    Args:
        language: Code langue ("fr" ou "en")
    """
    load_translations(language)


def get_available_languages():
    """
    Retourne la liste des langues disponibles.
    
    Returns:
        list: Liste des codes langue disponibles
    """
    locales_path = get_locales_path()
    languages = []
    
    if os.path.exists(locales_path):
        for filename in os.listdir(locales_path):
            if filename.endswith('.json'):
                lang_code = filename[:-5]  # Enlever .json
                languages.append(lang_code)
    
    return sorted(languages)


# === FONCTIONS UTILITAIRES POUR LES MATÉRIAUX ===

def tr_material(material_key):
    """
    Traduit un nom de matériau.
    
    Args:
        material_key: Clé du matériau (ex: "piano_wire")
        
    Returns:
        str: Nom traduit du matériau
    """
    return tr(f"material.{material_key}")


def tr_treatment(treatment_key):
    """
    Traduit un nom de traitement de surface.
    
    Args:
        treatment_key: Clé du traitement (ex: "shot_peening")
        
    Returns:
        str: Nom traduit du traitement
    """
    return tr(f"treatment.{treatment_key}")


def show_language_dialog():
    """
    Gère la sélection de langue au démarrage.

    Comportement (fichier SpringFull/lang.txt, voir get_lang_file_path()):
    - lang.txt absent (premier lancement) → le dialogue de choix de langue
      s'affiche ; le choix de l'utilisateur est ensuite mémorisé dans
      lang.txt et n'est plus redemandé aux lancements suivants.
    - lang.txt contient un code langue valide (en, fr, de, es, it) → ce
      code est utilisé directement, sans dialogue.
    - lang.txt contient 'ask' → le dialogue est affiché à chaque
      lancement (pratique en développement / pour retravailler les
      traductions).
    - lang.txt illisible ou code non reconnu → détection automatique
      (langue de FreeCAD ou du système), sans dialogue.

    Returns:
        bool: True si langue sélectionnée/détectée, False si annulé
    """
    stored_lang = read_lang_preference()

    if stored_lang is not None and stored_lang != "ask":
        # Préférence valide déjà mémorisée -> l'utiliser directement
        set_language(stored_lang)
        _trace(f"[SpringFull I18n] Langue chargee depuis lang.txt: {stored_lang}")
        return True

    is_first_run = stored_lang is None

    if not is_first_run:
        # lang.txt == 'ask': mode developpement, on redetecte la langue
        # systeme avant d'afficher le dialogue, pour une preselection
        # coherente dans la liste deroulante.
        set_language(detect_language())

    # Mode dialogue - afficher la sélection de langue
    # Import Qt
    try:
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
        from PySide6.QtCore import Qt
        QDialogAccepted = QDialog.DialogCode.Accepted
    except ImportError:
        from PySide.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
        from PySide.QtCore import Qt
        QDialogAccepted = QDialog.Accepted
    
    try:
        import FreeCADGui as Gui
        parent = Gui.getMainWindow()
    except:
        parent = None
    
    dialog = QDialog(parent)
    dialog.setWindowTitle("Language / Langue")
    dialog.setMinimumWidth(300)
    
    layout = QVBoxLayout(dialog)
    
    # Titre
    title = QLabel("Select language / Sélectionner la langue")
    title.setAlignment(Qt.AlignCenter)
    title.setStyleSheet("font-weight: bold; font-size: 11pt;")
    layout.addWidget(title)
    
    # Info sur la mémorisation du choix (bilingue: la langue n'est pas
    # encore connue à ce stade)
    if is_first_run:
        info_text = ("Your choice will be remembered automatically. / "
                     "Ce choix sera mémorisé automatiquement.")
    else:
        info_text = ("Dialog mode active (lang.txt = 'ask'). / "
                     "Mode dialogue actif (lang.txt = 'ask').")
    info = QLabel(info_text)
    info.setWordWrap(True)
    info.setAlignment(Qt.AlignCenter)
    info.setStyleSheet("color: #888; font-style: italic; font-size: 9pt;")
    layout.addWidget(info)
    
    layout.addSpacing(15)
    
    # Combo langue
    combo_layout = QHBoxLayout()
    combo_layout.addWidget(QLabel("Language / Langue:"))
    
    combo = QComboBox()
    languages = {
        "en": "English",
        "fr": "Français",
        "de": "Deutsch",
        "es": "Español",
        "it": "Italiano"
    }
    
    current_lang = get_current_language()
    
    for code, name in languages.items():
        combo.addItem(f"{name} ({code})", code)
    
    # Sélectionner la langue courante
    for i in range(combo.count()):
        if combo.itemData(i) == current_lang:
            combo.setCurrentIndex(i)
            break
    
    combo_layout.addWidget(combo)
    layout.addLayout(combo_layout)
    
    layout.addSpacing(15)
    
    # Boutons
    btn_layout = QHBoxLayout()
    btn_layout.addStretch()
    
    btn_ok = QPushButton("OK")
    btn_ok.setMinimumWidth(80)
    btn_ok.clicked.connect(dialog.accept)
    btn_layout.addWidget(btn_ok)
    
    btn_cancel = QPushButton("Cancel / Annuler")
    btn_cancel.setMinimumWidth(100)
    btn_cancel.clicked.connect(dialog.reject)
    btn_layout.addWidget(btn_cancel)
    
    layout.addLayout(btn_layout)
    
    # Exécution
    if dialog.exec() == QDialogAccepted:
        selected_lang = combo.currentData()
        if selected_lang != current_lang:
            set_language(selected_lang)
            _trace(f"[SpringFull I18n] Langue changée: {selected_lang}")
        if is_first_run:
            # Mémoriser le choix : plus jamais redemandé aux lancements
            # suivants (contrairement à l'ancien mécanisme par
            # timestamps, qui redemandait à chaque fois par défaut).
            write_lang_preference(selected_lang)
        return True

    return False


# Initialisation au chargement du module
load_translations()

# -*- coding: utf-8 -*-
"""
SpringFullI18nModule.py - Internationalization module for SpringFull

Manages English/French translations for all interface texts.
Automatic language detection from FreeCAD or system settings.

Reference language: English (en.json)
Translations: French (fr.json), and other languages

Version: 1.2.0 - Translation mode controlled by file timestamps
"""

import os
import json

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


def should_show_language_dialog():
    """
    Détermine si le dialogue de sélection de langue doit être affiché.
    
    Logique basée sur les timestamps de deux fichiers de contrôle:
    - Translate_on.txt  : Si plus récent → afficher le dialogue
    - Translate_off.txt : Si plus récent → utiliser la langue système automatiquement
    
    Returns:
        bool: True si le dialogue doit être affiché, False sinon
    """
    module_dir = get_module_path()
    translate_on_file = os.path.join(module_dir, "Translate_on.txt")
    translate_off_file = os.path.join(module_dir, "Translate_off.txt")
    
    # Vérifier l'existence des fichiers
    on_exists = os.path.exists(translate_on_file)
    off_exists = os.path.exists(translate_off_file)
    
    # Cas où un seul fichier existe
    if on_exists and not off_exists:
        print("[SpringFull I18n] Mode: dialogue (Translate_on.txt seul présent)")
        return True
    
    if off_exists and not on_exists:
        print("[SpringFull I18n] Mode: automatique (Translate_off.txt seul présent)")
        return False
    
    # Cas où aucun fichier n'existe - par défaut, afficher le dialogue
    if not on_exists and not off_exists:
        print("[SpringFull I18n] Mode: dialogue (fichiers de contrôle absents)")
        return True
    
    # Les deux fichiers existent - comparer les timestamps
    try:
        on_mtime = os.path.getmtime(translate_on_file)
        off_mtime = os.path.getmtime(translate_off_file)
        
        if on_mtime > off_mtime:
            print("[SpringFull I18n] Mode: dialogue (Translate_on.txt plus récent)")
            return True
        else:
            print("[SpringFull I18n] Mode: automatique (Translate_off.txt plus récent)")
            return False
    except OSError as e:
        print(f"[SpringFull I18n] Erreur lecture timestamps: {e}")
        # En cas d'erreur, afficher le dialogue par sécurité
        return True


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
            print(f"[SpringFull I18n] Language loaded: {language}")
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
    
    Comportement contrôlé par les timestamps des fichiers:
    - Translate_on.txt plus récent  → Affiche le dialogue de sélection
    - Translate_off.txt plus récent → Détection automatique (langue système)
    
    En mode automatique:
    - Détecte la langue de FreeCAD ou du système
    - Si langue non reconnue → anglais par défaut
    
    Returns:
        bool: True si langue sélectionnée/détectée, False si annulé
    """
    # Vérifier le mode de fonctionnement
    if not should_show_language_dialog():
        # Mode automatique - détecter la langue système
        detected_lang = detect_language()
        set_language(detected_lang)
        print(f"[SpringFull I18n] Langue détectée automatiquement: {detected_lang}")
        return True
    
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
    
    # Info sur le mode de contrôle
    info = QLabel("(To disable: touch Translate_off.txt)")
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
            print(f"[SpringFull I18n] Langue changée: {selected_lang}")
        return True
    
    return False


# Initialisation au chargement du module
load_translations()

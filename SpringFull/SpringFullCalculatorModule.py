#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SpringFullCalculatorModule - Calculateur de ressorts de compression
Conforme EN 13906-1, intégré à SpringFull

Version: 1.0 - Module intégré sans dépendance externe
"""

__author__ = "Yves Guillou"
__licence__ = "GPL"

import FreeCAD as App
import FreeCADGui as Gui
import math
import json
import os

# Import compatible PySide2/PySide6
try:
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
        QLabel, QDoubleSpinBox, QSpinBox, QComboBox, QPushButton,
        QScrollArea, QWidget, QMessageBox, QGroupBox
    )
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFontMetrics
    from PySide6.QtWidgets import QApplication
    # PySide6: constantes dans sous-classes
    QDialogAccepted = QDialog.DialogCode.Accepted
    QMsgBoxYes = QMessageBox.StandardButton.Yes
    QMsgBoxNo = QMessageBox.StandardButton.No
    PYSIDE6 = True
except ImportError:
    from PySide.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
        QLabel, QDoubleSpinBox, QSpinBox, QComboBox, QPushButton,
        QScrollArea, QWidget, QMessageBox, QGroupBox
    )
    from PySide.QtCore import Qt
    from PySide.QtGui import QFontMetrics
    from PySide.QtWidgets import QApplication
    # PySide2: constantes directes
    QDialogAccepted = QDialog.Accepted
    QMsgBoxYes = QMessageBox.Yes
    QMsgBoxNo = QMessageBox.No
    PYSIDE6 = False

# Import du module d'internationalisation
from SpringFull.SpringFullI18nModule import tr, get_current_language


# =============================================================================
# STYLES - Détection automatique du thème (clair/sombre)
# =============================================================================

def _is_dark_theme():
    """Détecte si FreeCAD utilise un thème sombre."""
    try:
        import FreeCADGui as Gui
        mw = Gui.getMainWindow()
        if mw:
            palette = mw.palette()
            # Compatibilité PySide2/PySide6 pour obtenir la couleur de fond
            try:
                # PySide6
                from PySide6.QtGui import QPalette
                bg_color = palette.color(QPalette.ColorRole.Window)
            except ImportError:
                # PySide2
                from PySide.QtGui import QPalette
                bg_color = palette.color(QPalette.Window)
            
            # Calculer la luminosité
            luminance = (bg_color.red() * 0.299 + bg_color.green() * 0.587 + bg_color.blue() * 0.114)
            App.Console.PrintMessage(f"[SpringFull] Theme detection: luminance={luminance:.0f}, dark={luminance < 128}\n")
            return luminance < 128
    except Exception as e:
        App.Console.PrintWarning(f"[SpringFull] Theme detection error: {e}\n")
    return False  # Par défaut, thème clair

def _get_styles():
    """Retourne les styles adaptés au thème actuel."""
    dark = _is_dark_theme()
    
    if dark:
        # Thème sombre
        BG_INPUT = "#3C3C3C"
        BG_INPUT_FOCUS = "#4A4A4A"
        BG_RESULT = "#2D2D2D"
        BG_RESULT_IMPORTANT = "#383838"
        BG_DROPDOWN = "#3C3C3C"
        BG_BUTTON = "#3C3C3C"
        BG_BUTTON_HOVER = "#4A4A4A"
        BG_BUTTON_PRESSED = "#555555"
        FG_COLOR = "#FFFFFF"
        BORDER_COLOR = "#555555"
        BORDER_FOCUS = "#888888"
        SELECTION_BG = "#0078D7"
        SELECTION_FG = "#FFFFFF"
        ALERT_OK_BG = "#2D4A2D"
        ALERT_OK_FG = "#90EE90"
        ALERT_OK_BORDER = "#3D6A3D"
        ALERT_WARN_BG = "#4A2D2D"
        ALERT_WARN_FG = "#FF9090"
        ALERT_WARN_BORDER = "#6A3D3D"
        SECTION_COLOR = "#AAAAAA"
    else:
        # Thème clair
        BG_INPUT = "#FFFFFF"
        BG_INPUT_FOCUS = "#FFFFF0"
        BG_RESULT = "#F5F5F5"
        BG_RESULT_IMPORTANT = "#E8E8E8"
        BG_DROPDOWN = "#FFFFFF"
        BG_BUTTON = "#FFFFFF"
        BG_BUTTON_HOVER = "#F0F0F0"
        BG_BUTTON_PRESSED = "#E0E0E0"
        FG_COLOR = "#000000"
        BORDER_COLOR = "#CCCCCC"
        BORDER_FOCUS = "#666666"
        SELECTION_BG = "#0078D7"
        SELECTION_FG = "#FFFFFF"
        ALERT_OK_BG = "#DFF0D8"
        ALERT_OK_FG = "#3C763D"
        ALERT_OK_BORDER = "#D6E9C6"
        ALERT_WARN_BG = "#F2DEDE"
        ALERT_WARN_FG = "#A94442"
        ALERT_WARN_BORDER = "#EBCCD1"
        SECTION_COLOR = "#555555"
    
    styles = {}
    
    # Style pour les champs de saisie
    styles['INPUT'] = f"""
        QDoubleSpinBox, QSpinBox {{
            background-color: {BG_INPUT};
            color: {FG_COLOR};
            border: 1px solid {BORDER_COLOR};
            border-radius: 3px;
            padding: 4px;
            font-weight: bold;
            min-width: 70px;
            max-width: 85px;
        }}
        QDoubleSpinBox:focus, QSpinBox:focus {{
            border: 1px solid {BORDER_FOCUS};
            background-color: {BG_INPUT_FOCUS};
        }}
    """
    
    # Style pour les ComboBox
    styles['COMBO'] = f"""
        QComboBox {{
            background-color: {BG_INPUT};
            color: {FG_COLOR};
            border: 1px solid {BORDER_COLOR};
            border-radius: 3px;
            padding: 4px;
            font-weight: bold;
            min-width: 70px;
            max-width: 85px;
        }}
        QComboBox:focus {{
            border: 1px solid {BORDER_FOCUS};
        }}
        QComboBox QAbstractItemView {{
            background-color: {BG_DROPDOWN};
            color: {FG_COLOR};
            selection-background-color: {SELECTION_BG};
            selection-color: {SELECTION_FG};
        }}
    """
    
    # Style pour le ComboBox du type de diamètre
    styles['COMBO_DIAMETER_TYPE'] = f"""
        QComboBox {{
            background-color: {BG_INPUT};
            color: {FG_COLOR};
            border: 1px solid {BORDER_COLOR};
            border-radius: 3px;
            padding: 4px;
            font-weight: bold;
            min-width: 100px;
            max-width: 110px;
        }}
        QComboBox:focus {{
            border: 1px solid {BORDER_FOCUS};
        }}
        QComboBox QAbstractItemView {{
            background-color: {BG_DROPDOWN};
            color: {FG_COLOR};
            selection-background-color: {SELECTION_BG};
            selection-color: {SELECTION_FG};
        }}
    """
    
    # Style pour les ComboBox larges
    styles['COMBO_WIDE'] = f"""
        QComboBox {{
            background-color: {BG_INPUT};
            color: {FG_COLOR};
            border: 1px solid {BORDER_COLOR};
            border-radius: 3px;
            padding: 4px;
            font-weight: bold;
            min-width: 250px;
        }}
        QComboBox:focus {{
            border: 1px solid {BORDER_FOCUS};
        }}
        QComboBox QAbstractItemView {{
            background-color: {BG_DROPDOWN};
            color: {FG_COLOR};
            selection-background-color: {SELECTION_BG};
            selection-color: {SELECTION_FG};
        }}
    """
    
    # Style pour le bouton matériau
    styles['MATERIAL_BUTTON'] = f"""
        QPushButton {{
            background-color: {BG_BUTTON};
            color: {FG_COLOR};
            border: 1px solid {BORDER_COLOR};
            border-radius: 3px;
            padding: 4px 8px;
            font-weight: bold;
            min-width: 180px;
            text-align: left;
        }}
        QPushButton:hover {{
            background-color: {BG_BUTTON_HOVER};
            border: 1px solid {BORDER_FOCUS};
        }}
        QPushButton:pressed {{
            background-color: {BG_BUTTON_PRESSED};
        }}
    """
    
    # Style pour les résultats
    styles['RESULT'] = f"""
        QLabel {{
            background-color: {BG_RESULT};
            color: {FG_COLOR};
            border: 1px solid {BORDER_COLOR};
            border-radius: 3px;
            padding: 4px;
            font-weight: bold;
            min-width: 70px;
            max-width: 85px;
        }}
    """
    
    # Style pour les résultats importants
    styles['RESULT_IMPORTANT'] = f"""
        QLabel {{
            background-color: {BG_RESULT_IMPORTANT};
            color: {FG_COLOR};
            border: 1px solid {BORDER_FOCUS};
            border-radius: 3px;
            padding: 4px;
            font-weight: bold;
            min-width: 70px;
            max-width: 85px;
        }}
    """
    
    # Style pour alertes OK
    styles['ALERT_OK'] = f"""
        QLabel {{
            background-color: {ALERT_OK_BG};
            color: {ALERT_OK_FG};
            border: 1px solid {ALERT_OK_BORDER};
            border-radius: 3px;
            padding: 8px;
            font-weight: bold;
        }}
    """
    
    # Style pour alertes Warning
    styles['ALERT_WARN'] = f"""
        QLabel {{
            background-color: {ALERT_WARN_BG};
            color: {ALERT_WARN_FG};
            border: 1px solid {ALERT_WARN_BORDER};
            border-radius: 3px;
            padding: 8px;
            font-weight: bold;
        }}
    """
    
    # Couleur pour les sections
    styles['SECTION_COLOR'] = SECTION_COLOR
    styles['FG_COLOR'] = FG_COLOR
    styles['BG_INPUT'] = BG_INPUT
    styles['BORDER_COLOR'] = BORDER_COLOR
    
    return styles

# Variables globales pour les styles (initialisées au premier usage)
_CACHED_STYLES = None

def get_style(name):
    """Retourne un style par son nom."""
    global _CACHED_STYLES
    if _CACHED_STYLES is None:
        _CACHED_STYLES = _get_styles()
    return _CACHED_STYLES.get(name, "")


# =============================================================================
# GESTIONNAIRE DE BASES DE DONNÉES
# =============================================================================

class DatabaseManager:
    """Gestionnaire des bases de données JSON."""
    
    FILE_MATERIALS = "spring_materials_database.json"
    FILE_DIAMETERS = "wire_diameters_database.json"
    FILE_END_TYPES = "end_types_database.json"
    
    def __init__(self):
        self.materials_data = {}
        self.diameters_data = {}
        self.end_types_data = {}
        self.localized_materials = {}  # Données traduites des matériaux
        self.base_path = None
        self.loaded = False
    
    def find_database_folder(self):
        """Recherche le dossier contenant les fichiers JSON (dans utils/)."""
        locations = []
        
        # Dossier de la macro / utils
        try:
            macro_dir = os.path.dirname(os.path.abspath(__file__))
            locations.append(os.path.join(macro_dir, "utils"))
            locations.append(macro_dir)  # Fallback pour compatibilité
        except:
            pass
        
        # Dossier Macro FreeCAD / utils
        try:
            user_macro_dir = App.getUserMacroDir(True)
            if user_macro_dir:
                locations.append(os.path.join(user_macro_dir, "SpringFull", "utils"))
                locations.append(os.path.join(user_macro_dir, "SpringFull"))  # Fallback
                locations.append(user_macro_dir)  # Dossier Macro racine
        except:
            pass
        
        for path in locations:
            if path and os.path.isdir(path):
                if os.path.exists(os.path.join(path, self.FILE_MATERIALS)):
                    return path
        
        # Si le fichier matériaux n'est pas trouvé, retourner quand même utils/ pour les autres fichiers
        for path in locations:
            if path and os.path.isdir(path):
                if os.path.exists(os.path.join(path, self.FILE_DIAMETERS)) or \
                   os.path.exists(os.path.join(path, self.FILE_END_TYPES)):
                    return path
        
        return None
    
    def find_locales_folder(self):
        """Recherche le dossier locales/."""
        try:
            macro_dir = os.path.dirname(os.path.abspath(__file__))
            locales_dir = os.path.join(macro_dir, "locales")
            if os.path.isdir(locales_dir):
                return locales_dir
        except:
            pass
        
        try:
            user_macro_dir = App.getUserMacroDir(True)
            if user_macro_dir:
                locales_dir = os.path.join(user_macro_dir, "SpringFull", "locales")
                if os.path.isdir(locales_dir):
                    return locales_dir
        except:
            pass
        
        return None
    
    def load_json(self, filepath):
        """Charge un fichier JSON."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f), None
        except Exception as e:
            return None, str(e)
    
    def load_localized_materials(self):
        """Charge les données de matériaux localisées selon la langue courante."""
        locales_dir = self.find_locales_folder()
        if not locales_dir:
            return
        
        # Déterminer la langue courante
        lang = get_current_language()
        
        # Charger le fichier de matériaux localisé
        mat_file = os.path.join(locales_dir, f"materials_{lang}.json")
        if os.path.exists(mat_file):
            data, err = self.load_json(mat_file)
            if not err and data:
                self.localized_materials = data.get("materials", {})
                return
        
        # Fallback vers l'anglais si le fichier de la langue n'existe pas
        if lang != "en":
            mat_file_en = os.path.join(locales_dir, "materials_en.json")
            if os.path.exists(mat_file_en):
                data, err = self.load_json(mat_file_en)
                if not err and data:
                    self.localized_materials = data.get("materials", {})
    
    def load_all(self, base_path=None):
        """Charge toutes les bases de données."""
        if base_path is None:
            base_path = self.find_database_folder()
        
        self.base_path = base_path
        
        # Charger matériaux (base de données technique)
        # Chercher dans plusieurs emplacements
        materials_loaded = False
        if base_path:
            path = os.path.join(base_path, self.FILE_MATERIALS)
            data, err = self.load_json(path)
            if not err and data:
                self.materials_data = data
                materials_loaded = True
        
        # Chercher aussi dans le dossier Macro racine
        if not materials_loaded:
            try:
                user_macro_dir = App.getUserMacroDir(True)
                if user_macro_dir:
                    path = os.path.join(user_macro_dir, self.FILE_MATERIALS)
                    data, err = self.load_json(path)
                    if not err and data:
                        self.materials_data = data
                        materials_loaded = True
            except:
                pass
        
        # Charger matériaux localisés (affichage)
        self.load_localized_materials()
        
        # Si les matériaux techniques ne sont pas trouvés, utiliser les matériaux localisés
        if not materials_loaded and self.localized_materials:
            # Créer une structure minimale à partir des matériaux localisés
            self.materials_data = {"materials": {}}
            for name, loc_data in self.localized_materials.items():
                self.materials_data["materials"][name] = {
                    "description": loc_data.get("description", ""),
                    "code": loc_data.get("code", "")
                }
        
        # Charger diamètres
        if base_path:
            path = os.path.join(base_path, self.FILE_DIAMETERS)
            data, err = self.load_json(path)
            if not err:
                self.diameters_data = data
        
        # Charger types extrémités
        if base_path:
            path = os.path.join(base_path, self.FILE_END_TYPES)
            data, err = self.load_json(path)
            if not err:
                self.end_types_data = data
        
        self.loaded = True
        return True
    
    def get_localized_material(self, name):
        """Retourne les données localisées d'un matériau, ou None si non disponible."""
        return self.localized_materials.get(name, None)
    
    def get_material_display_name(self, name):
        """Retourne le nom d'affichage localisé d'un matériau."""
        loc_mat = self.get_localized_material(name)
        if loc_mat and "display_name" in loc_mat:
            return loc_mat["display_name"]
        return name  # Retourner le nom original si pas de traduction
    
    def get_material_list(self, translated=False):
        """Retourne la liste des matériaux.
        
        Args:
            translated: Si True, retourne les noms d'affichage localisés
        """
        keys = list(self.materials_data.get("materials", {}).keys())
        if translated:
            return [self.get_material_display_name(k) for k in keys]
        return keys
    
    def get_material_translation(self, material_name):
        """Retourne le nom traduit d'un matériau."""
        return self.get_material_display_name(material_name)
    
    def get_material(self, name):
        return self.materials_data.get("materials", {}).get(name, None)
    
    def get_module_G(self, name):
        mat = self.get_material(name)
        if mat:
            return mat.get("shear_modulus_G", {}).get("value_daN", 8150)
        return 8150
    
    def get_Rm(self, name, d):
        mat = self.get_material(name)
        if not mat:
            return 150.0
        
        table = mat.get("tensile_strength_Rm", {}).get("table", [])
        for row in table:
            if row["d_min"] <= d < row["d_max"]:
                return row.get("Rm_daN", 150)
        
        if table:
            return table[-1].get("Rm_daN", 150)
        return 150.0
    
    def get_stress_factor(self, material_name, service_key):
        mat = self.get_material(material_name)
        if mat:
            return mat.get("stress_limits", {}).get(service_key, {}).get("factor", 0.40)
        return 0.40
    
    def get_set_solid_factor(self, material_name):
        mat = self.get_material(material_name)
        if mat:
            return mat.get("stress_limits", {}).get("set_solid", {}).get("factor", 0.80)
        return 0.80
    
    def get_work_types(self):
        return self.materials_data.get("work_types", {})
    
    def get_work_type_list(self, translated=False):
        """Retourne la liste des types de service.
        
        Args:
            translated: Si True, retourne les noms traduits
        """
        keys = list(self.get_work_types().keys())
        if translated:
            result = []
            for k in keys:
                tr_key = f"service.{self._service_key(k)}"
                translated_name = tr(tr_key)
                # Si la traduction retourne la clé elle-même, utiliser le nom original
                if translated_name == tr_key:
                    result.append(k)
                else:
                    result.append(translated_name)
            return result
        return keys
    
    def _service_key(self, service_name):
        """Convertit un nom de service en clé de traduction."""
        mapping = {
            "CHARGE STATIQUE LEGERE": "static_light",
            "SERVICE STATIQUE": "static",
            "SERVICE MOYEN - DYNAMIQUE LENT": "dynamic_slow",
            "SERVICE SEVERE - DYNAMIQUE RAPIDE": "dynamic_fast"
        }
        return mapping.get(service_name, service_name.lower().replace(" ", "_").replace("-", "_"))
    
    def get_stress_factor_key(self, work_type_name):
        wt = self.get_work_types().get(work_type_name, {})
        return wt.get("stress_factor_key", "medium_dynamic")
    
    def get_wire_diameters(self):
        swd = self.diameters_data.get("standard_wire_diameters", {})
        return swd.get("all_diameters", [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0])
    
    def get_end_types(self):
        et = self.end_types_data.get("end_types", {})
        return {k: v for k, v in et.items() if isinstance(v, dict) and "dead_coils" in v}
    
    def get_end_type_list(self, translated=False):
        """Retourne la liste des types d'extrémités dans l'ordre défini.
        
        Args:
            translated: Si True, retourne les noms traduits
        """
        # Utiliser l'ordre défini dans selection_order si disponible
        order = self.end_types_data.get("selection_order", [])
        if not order:
            order = list(self.get_end_types().keys())
        
        if translated:
            result = []
            for k in order:
                tr_key = f"end.{self._end_type_key(k)}"
                translated_name = tr(tr_key)
                # Si la traduction retourne la clé elle-même, utiliser le nom original
                if translated_name == tr_key:
                    result.append(k)
                else:
                    result.append(translated_name)
            return result
        return order
    
    def _end_type_key(self, end_type_name):
        """Convertit un nom de type d'extrémité en clé de traduction."""
        mapping = {
            "COUPEES": "cut",
            "MEULEES": "cut_ground",
            "RAPPROCHEES": "closed",
            "RAPPROCHEES_MEULEES": "closed_ground",
            "NON_RAPPROCHEES": "open",
            "NON_RAPPROCHEES_MEULEES": "open_ground"
        }
        return mapping.get(end_type_name, end_type_name.lower())
    
    def get_dead_coils_min(self, end_type_name):
        et = self.get_end_types().get(end_type_name, {})
        return et.get("dead_coils", {}).get("minimum", 2.0)
    
    def is_ground_type(self, end_type_name):
        """Retourne True si le type d'extrémité est meulé."""
        et = self.get_end_types().get(end_type_name, {})
        return et.get("grinding_required", False)


# Instance globale
DB = DatabaseManager()


def get_coef_bergstrasser(c):
    """Coefficient de Bergsträsser K = (c + 0.5) / (c - 0.75)"""
    if c <= 0.75:
        return 2.0
    return (c + 0.5) / (c - 0.75)


# =============================================================================
# DIALOGUE SELECTION MATERIAU
# =============================================================================

class MaterialSelectionDialog(QDialog):
    """Dialogue de selection de materiau avec informations detaillees."""
    
    def __init__(self, parent=None, current_material="CORDE A PIANO"):
        super().__init__(parent)
        self.setWindowTitle(tr("matdlg.window_title"))
        
        self.selected_material = current_material
        
        # Calculer les dimensions optimales avant de creer l'UI
        self._field_sizes = self._calculate_optimal_sizes()
        
        self._setup_ui()
        self._update_info()
        
        # Ajuster la taille de la fenetre apres creation
        self.adjustSize()
    
    def _calculate_optimal_sizes(self):
        """Calcule les dimensions optimales pour chaque champ en parcourant tous les materiaux."""
        # QFontMetrics et QApplication sont importés au niveau du module
        
        # Obtenir les metriques de police par defaut
        font = QApplication.font()
        fm = QFontMetrics(font)
        line_height = fm.height() + 6  # Hauteur d'une ligne + marge augmentée
        
        # Initialiser les compteurs max
        max_lines = {
            'description': 2,
            'code': 1,
            'corrosion': 1,
            'treatments': 1,
            'applications': 1,
            'cond_elec': 1,
            'cond_therm': 1,
            'notes': 1
        }
        
        max_widths = {
            'code': 150,
            'corrosion': 150,
            'cond_elec': 100,
            'cond_therm': 100
        }
        
        # Parcourir tous les materiaux (données techniques ET localisées)
        materials = DB.get_material_list() or []
        for mat_name in materials:
            # Données techniques
            mat = DB.get_material(mat_name)
            # Données localisées
            loc_mat = DB.get_localized_material(mat_name)
            
            if not mat and not loc_mat:
                continue
            
            # Helper pour obtenir la valeur la plus longue entre tech et localisée
            def get_longest(key, default=""):
                tech_val = mat.get(key, default) if mat else default
                loc_val = loc_mat.get(key, default) if loc_mat else default
                if isinstance(tech_val, list):
                    tech_val = "\n".join(tech_val)
                if isinstance(loc_val, list):
                    loc_val = "\n".join(loc_val)
                return tech_val if len(str(tech_val)) > len(str(loc_val)) else loc_val
            
            # Description (2-3 lignes)
            desc = get_longest("description", "")
            max_lines['description'] = max(max_lines['description'], min(3, 1 + len(desc) // 50))
            
            # Code
            code = get_longest("code", "")
            max_widths['code'] = max(max_widths['code'], fm.horizontalAdvance(str(code)) + 30)
            
            # Resistance corrosion
            corr = get_longest("corrosion_resistance", "")
            max_widths['corrosion'] = max(max_widths['corrosion'], fm.horizontalAdvance(str(corr)) + 30)
            
            # Traitements de surface
            treatments_tech = mat.get("surface_treatments", []) if mat else []
            treatments_loc = loc_mat.get("surface_treatments", []) if loc_mat else []
            treatments = treatments_loc if len(treatments_loc) >= len(treatments_tech) else treatments_tech
            max_lines['treatments'] = max(max_lines['treatments'], len(treatments) + 1)  # +1 pour marge
            
            # Applications
            apps_tech = mat.get("applications", []) if mat else []
            apps_loc = loc_mat.get("applications", []) if loc_mat else []
            apps = apps_loc if len(apps_loc) >= len(apps_tech) else apps_tech
            max_lines['applications'] = max(max_lines['applications'], len(apps) + 1)  # +1 pour marge
            
            # Conductivite
            cond_tech = mat.get("conductivity", {}) if mat else {}
            cond_loc = loc_mat.get("conductivity", {}) if loc_mat else {}
            elec = cond_loc.get("electrical", cond_tech.get("electrical", ""))
            therm = cond_loc.get("thermal", cond_tech.get("thermal", ""))
            max_widths['cond_elec'] = max(max_widths['cond_elec'], fm.horizontalAdvance(str(elec)) + 30)
            max_widths['cond_therm'] = max(max_widths['cond_therm'], fm.horizontalAdvance(str(therm)) + 30)
            
            # Notes
            notes_tech = mat.get("notes", mat.get("special_notes", [])) if mat else []
            notes_loc = loc_mat.get("notes", []) if loc_mat else []
            notes = notes_loc if len(notes_loc) >= len(notes_tech) else notes_tech
            max_lines['notes'] = max(max_lines['notes'], len(notes) + 1)  # +1 pour marge
        
        # Convertir en hauteurs (avec minimum plus généreux)
        sizes = {
            'description_h': max(50, max_lines['description'] * line_height + 15),
            'code_w': max(180, min(300, max_widths['code'])),
            'corrosion_w': max(180, min(350, max_widths['corrosion'])),
            'treatments_h': max(80, max_lines['treatments'] * line_height + 15),
            'applications_h': max(100, max_lines['applications'] * line_height + 15),
            'cond_elec_w': max(120, min(220, max_widths['cond_elec'])),
            'cond_therm_w': max(120, min(220, max_widths['cond_therm'])),
            'notes_h': max(80, max_lines['notes'] * line_height + 15)
        }
        
        return sizes
    
    def _setup_ui(self):
        """Configure l'interface utilisateur."""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Style pour les champs d'information (adapté au thème)
        INFO_STYLE = f"background-color: {get_style('BG_INPUT')}; color: {get_style('FG_COLOR')}; padding: 4px; border: 1px solid {get_style('BORDER_COLOR')};"
        LABEL_STYLE = "font-weight: bold; margin-top: 2px;"
        
        sizes = self._field_sizes
        
        # === Ligne 1: Materiau (label+combo) | Description (label+champ) ===
        row1 = QHBoxLayout()
        row1.setSpacing(15)
        
        # Colonne gauche: Materiau (label au-dessus du combo, aligné en haut)
        mat_col = QVBoxLayout()
        mat_col.setSpacing(2)
        lbl_material = QLabel(tr("matdlg.material"))
        lbl_material.setStyleSheet(LABEL_STYLE)
        mat_col.addWidget(lbl_material)
        self.combo_material = QComboBox()
        self._material_keys = DB.get_material_list() or ["CORDE A PIANO"]
        default_idx = 0
        for i, key in enumerate(self._material_keys):
            display_name = DB.get_material_display_name(key)
            self.combo_material.addItem(display_name, key)
            if key == self.selected_material:
                default_idx = i
        self.combo_material.setFixedWidth(200)
        self.combo_material.setCurrentIndex(default_idx)
        self.combo_material.currentIndexChanged.connect(self._update_info)
        mat_col.addWidget(self.combo_material)
        mat_col.addStretch()  # Pousse tout vers le haut
        row1.addLayout(mat_col)
        
        # Colonne droite: Description (label+champ)
        desc_col = QVBoxLayout()
        desc_col.setSpacing(2)
        lbl_desc = QLabel(tr("matdlg.description"))
        lbl_desc.setStyleSheet(LABEL_STYLE)
        desc_col.addWidget(lbl_desc)
        self.txt_description = QLabel()
        self.txt_description.setWordWrap(True)
        self.txt_description.setStyleSheet(INFO_STYLE)
        self.txt_description.setMinimumHeight(40)
        self.txt_description.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        desc_col.addWidget(self.txt_description)
        row1.addLayout(desc_col, stretch=1)
        
        layout.addLayout(row1)
        
        # === Ligne 2: Code + Corrosion | Traitements de surface ===
        row2 = QHBoxLayout()
        row2.setSpacing(15)
        
        # Colonne gauche: Code et Corrosion (empilés)
        left_col = QVBoxLayout()
        left_col.setSpacing(4)
        
        # Code
        lbl_code = QLabel(tr("matdlg.code"))
        lbl_code.setStyleSheet(LABEL_STYLE)
        left_col.addWidget(lbl_code)
        self.txt_code = QLabel()
        self.txt_code.setStyleSheet(INFO_STYLE)
        self.txt_code.setMinimumWidth(200)
        left_col.addWidget(self.txt_code)
        
        left_col.addSpacing(4)
        
        # Resistance corrosion
        lbl_corr = QLabel(tr("matdlg.corrosion"))
        lbl_corr.setStyleSheet(LABEL_STYLE)
        left_col.addWidget(lbl_corr)
        self.txt_corrosion = QLabel()
        self.txt_corrosion.setWordWrap(True)
        self.txt_corrosion.setStyleSheet(INFO_STYLE)
        self.txt_corrosion.setMinimumWidth(200)
        left_col.addWidget(self.txt_corrosion)
        
        left_col.addStretch()
        row2.addLayout(left_col)
        
        # Colonne droite: Traitements de surface
        treat_col = QVBoxLayout()
        treat_col.setSpacing(2)
        lbl_treat = QLabel(tr("matdlg.treatments"))
        lbl_treat.setStyleSheet(LABEL_STYLE)
        treat_col.addWidget(lbl_treat)
        self.txt_treatments = QLabel()
        self.txt_treatments.setWordWrap(True)
        self.txt_treatments.setStyleSheet(INFO_STYLE)
        self.txt_treatments.setMinimumHeight(sizes['treatments_h'])
        self.txt_treatments.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        treat_col.addWidget(self.txt_treatments)
        row2.addLayout(treat_col, stretch=1)
        
        layout.addLayout(row2)
        
        # === Ligne 3: Applications | Température + Conductivité (compacte) ===
        row3 = QHBoxLayout()
        row3.setSpacing(15)
        
        # Applications
        app_col = QVBoxLayout()
        app_col.setSpacing(2)
        lbl_app = QLabel(tr("matdlg.applications"))
        lbl_app.setStyleSheet(LABEL_STYLE)
        app_col.addWidget(lbl_app)
        self.txt_applications = QLabel()
        self.txt_applications.setWordWrap(True)
        self.txt_applications.setStyleSheet(INFO_STYLE)
        self.txt_applications.setMinimumHeight(sizes['applications_h'])
        self.txt_applications.setMinimumWidth(200)
        self.txt_applications.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        app_col.addWidget(self.txt_applications)
        row3.addLayout(app_col, stretch=1)
        
        # Colonne droite: Température + Conductivité (compacte, une ligne chacune)
        right_col = QVBoxLayout()
        right_col.setSpacing(4)
        
        # Température
        lbl_temp = QLabel(tr("matdlg.temperature"))
        lbl_temp.setStyleSheet(LABEL_STYLE)
        right_col.addWidget(lbl_temp)
        self.txt_temperature = QLabel()
        self.txt_temperature.setStyleSheet(INFO_STYLE)
        right_col.addWidget(self.txt_temperature)
        
        right_col.addSpacing(4)
        
        # Conductivité (compacte: Électrique + Thermique sur une seule ligne avec valeurs)
        lbl_cond = QLabel(tr("matdlg.conductivity"))
        lbl_cond.setStyleSheet(LABEL_STYLE)
        right_col.addWidget(lbl_cond)
        
        cond_row = QHBoxLayout()
        cond_row.setSpacing(10)
        
        # Électrique (label: valeur)
        self.txt_cond_elec = QLabel()
        self.txt_cond_elec.setStyleSheet(INFO_STYLE)
        cond_row.addWidget(self.txt_cond_elec)
        
        # Thermique (label: valeur)
        self.txt_cond_therm = QLabel()
        self.txt_cond_therm.setStyleSheet(INFO_STYLE)
        cond_row.addWidget(self.txt_cond_therm)
        
        right_col.addLayout(cond_row)
        right_col.addStretch()
        
        row3.addLayout(right_col)
        
        layout.addLayout(row3)
        
        # === Ligne 4: Notes ===
        lbl_notes = QLabel(tr("matdlg.notes"))
        lbl_notes.setStyleSheet(LABEL_STYLE)
        layout.addWidget(lbl_notes)
        self.txt_notes = QLabel()
        self.txt_notes.setWordWrap(True)
        self.txt_notes.setStyleSheet(INFO_STYLE)
        self.txt_notes.setMinimumHeight(sizes['notes_h'])
        self.txt_notes.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        layout.addWidget(self.txt_notes)
        
        # === Boutons ===
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_ok = QPushButton(tr("common.ok"))
        btn_ok.setMinimumWidth(80)
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_ok)
        
        btn_cancel = QPushButton(tr("common.cancel"))
        btn_cancel.setMinimumWidth(80)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)
    
    def _update_info(self, index=None):
        """Met a jour les informations du materiau selectionne."""
        # Utiliser currentData pour obtenir la clé interne
        mat_name = self.combo_material.currentData()
        if mat_name is None:
            mat_name = self.combo_material.currentText()
        
        # Obtenir les données techniques (pour les calculs)
        mat = DB.get_material(mat_name)
        if not mat:
            return
        
        # Obtenir les données localisées (pour l'affichage)
        loc_mat = DB.get_localized_material(mat_name)
        
        # Fonction helper pour obtenir une valeur localisée ou par défaut
        def get_localized(key, default_value):
            if loc_mat and key in loc_mat:
                val = loc_mat[key]
                if isinstance(val, list):
                    return "\n".join(val)
                return val
            return default_value
        
        # Description
        self.txt_description.setText(get_localized("description", mat.get("description", "-")))
        
        # Code (pas de traduction, c'est un code technique)
        self.txt_code.setText(get_localized("code", mat.get("code", "-")))
        
        # Resistance corrosion
        self.txt_corrosion.setText(get_localized("corrosion_resistance", mat.get("corrosion_resistance", "-")))
        
        # Traitements de surface
        default_treatments = mat.get("surface_treatments", [])
        default_treatments_str = "\n".join(default_treatments) if default_treatments else "-"
        self.txt_treatments.setText(get_localized("surface_treatments", default_treatments_str))
        
        # Temperature
        if loc_mat and "temperature_range" in loc_mat:
            temp = loc_mat["temperature_range"]
        else:
            temp = mat.get("temperature_range", {})
        if temp:
            t_min = temp.get("min", "?")
            t_max = temp.get("max", "?")
            self.txt_temperature.setText("{} / +{}".format(t_min, t_max))
        else:
            self.txt_temperature.setText("-")
        
        # Applications
        default_apps = mat.get("applications", [])
        default_apps_str = "\n".join(default_apps) if default_apps else "-"
        self.txt_applications.setText(get_localized("applications", default_apps_str))
        
        # Conductivite - format compact avec labels et valeurs physiques
        if loc_mat and "conductivity" in loc_mat:
            cond = loc_mat["conductivity"]
        else:
            cond = mat.get("conductivity", {})
        
        # Électrique: afficher avec label et valeur IACS si disponible
        elec_val = cond.get("electrical", "-")
        elec_iacs = cond.get("electrical_iacs", "")  # % IACS si disponible
        if elec_iacs:
            self.txt_cond_elec.setText(f"{tr('matdlg.electrical')}: {elec_val} ({elec_iacs}% IACS)")
        else:
            self.txt_cond_elec.setText(f"{tr('matdlg.electrical')}: {elec_val}")
        
        # Thermique: afficher avec label et valeur W/m·K si disponible
        therm_val = cond.get("thermal", "-")
        therm_wmk = cond.get("thermal_wmk", "")  # W/m·K si disponible
        if therm_wmk:
            self.txt_cond_therm.setText(f"{tr('matdlg.thermal')}: {therm_val} ({therm_wmk} W/m·K)")
        else:
            self.txt_cond_therm.setText(f"{tr('matdlg.thermal')}: {therm_val}")
        
        # Notes
        default_notes = mat.get("notes", mat.get("special_notes", []))
        default_notes_str = "\n".join(default_notes) if default_notes else "-"
        self.txt_notes.setText(get_localized("notes", default_notes_str))
    
    def get_selected_material(self):
        """Retourne le materiau selectionne (clé interne)."""
        mat = self.combo_material.currentData()
        if mat is None:
            mat = self.combo_material.currentText()
        return mat


# =============================================================================
# DIALOGUE CALCULATEUR
# =============================================================================

class SpringCalculatorDialog(QDialog):
    """Dialogue principal du calculateur de ressorts."""
    
    def __init__(self, parent=None, spring_body=None):
        super().__init__(parent)
        self.setWindowTitle(tr("calc.window_title"))
        self.setMinimumWidth(620)
        self.setMinimumHeight(650)
        self.setMaximumWidth(700)
        
        self._updating_diameter = False
        self._force_select_minimum = False  # Flag pour forcer la sélection du diamètre minimum
        self.current_spring_body = spring_body
        self.parameters_changed = False
        self._previous_diameter_type = "Dm (moyen)"  # Valeur par défaut
        
        # Charger les bases de données
        DB.load_all()
        
        self._setup_ui()
        self._connect_signals()
        
        # Initialiser le type de diamètre précédent après création des widgets
        self._previous_diameter_type = self.inp_diameter_type.currentText()
        
        # Si un Body est fourni, charger ses paramètres
        if spring_body:
            self._populate_from_spring_body(spring_body)
        
        self._on_end_type_changed(self.inp_end_type.currentText())
    
    def _setup_ui(self):
        """Construction de l'interface."""
        main_layout = QVBoxLayout(self)
        
        # En-tête
        header = QHBoxLayout()
        title = QLabel(tr("calc.main_title"))
        title.setStyleSheet(f"font-size: 12pt; font-weight: bold; color: {get_style('FG_COLOR')};")
        header.addWidget(title)
        header.addStretch()
        main_layout.addLayout(header)
        
        # Zone scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        content = QWidget()
        grid = QGridLayout(content)
        grid.setSpacing(6)
        grid.setContentsMargins(10, 10, 10, 10)
        
        row = 0
        
        # === SECTION PARAMÈTRES D'ENTRÉE ===
        lbl_section1 = QLabel(tr("calc.section_input"))
        lbl_section1.setStyleSheet(f"font-weight: bold; color: {get_style('SECTION_COLOR')};")
        grid.addWidget(lbl_section1, row, 0, 1, 5)
        row += 1
        row += 1
        
        # Type de diamètre | Diamètre | Matière
        self.inp_diameter_type = QComboBox()
        self.inp_diameter_type.addItems([tr("calc.diameter_mean"), tr("calc.diameter_inner"), tr("calc.diameter_outer")])
        self.inp_diameter_type.setStyleSheet(get_style("COMBO_DIAMETER_TYPE"))
        self.inp_diameter_type.setToolTip(tr("calc.diameter_type"))
        grid.addWidget(self.inp_diameter_type, row, 0)
        
        self.inp_Dm = self._input(20.0, 2, 1.0, 500.0)
        self.inp_Dm.setToolTip(tr("calc.diameter_type_tooltip"))
        grid.addWidget(self.inp_Dm, row, 1)
        
        grid.addWidget(self._label(tr("calc.material")), row, 2)
        # Bouton cliquable pour ouvrir le dialogue de selection de materiau
        self._current_material = "CORDE A PIANO"
        self.inp_matiere = QPushButton(DB.get_material_translation(self._current_material))
        self.inp_matiere.setStyleSheet(get_style("MATERIAL_BUTTON"))
        self.inp_matiere.clicked.connect(self._open_material_dialog)
        grid.addWidget(self.inp_matiere, row, 3, 1, 2)
        row += 1
        
        # Diamètre fil | Type service
        grid.addWidget(self._label(tr("calc.wire_diameter")), row, 0)
        self.inp_d = QComboBox()
        # Stocker tous les diamètres disponibles pour le filtrage
        self._all_diameters = DB.get_wire_diameters()
        self.inp_d.addItems([f"{d:.2f}" for d in self._all_diameters])
        self.inp_d.setCurrentText("4.00")
        self.inp_d.setStyleSheet(get_style("COMBO"))
        self.inp_d.setEditable(True)
        self.inp_d.lineEdit().setAlignment(Qt.AlignRight)
        self.inp_d.lineEdit().setReadOnly(True)
        grid.addWidget(self.inp_d, row, 1)
        
        grid.addWidget(self._label(tr("calc.service_type")), row, 2)
        self.inp_service = QComboBox()
        # Stocker les clés internes et afficher les traductions
        self._service_keys = DB.get_work_type_list() or ["SERVICE MOYEN - DYNAMIQUE LENT"]
        for i, key in enumerate(self._service_keys):
            # Obtenir la traduction pour cette clé
            service_key = DB._service_key(key)
            tr_key = f"service.{service_key}"
            display_name = tr(tr_key)
            if display_name == tr_key:
                display_name = key  # Fallback au nom original
            self.inp_service.addItem(display_name, key)
            
            # Ajouter le tooltip pour cet item
            tooltip_key = f"service.{service_key}_tooltip"
            tooltip_text = tr(tooltip_key)
            if tooltip_text != tooltip_key:  # Si la traduction existe
                self.inp_service.setItemData(i, tooltip_text, Qt.ToolTipRole)
        self.inp_service.setStyleSheet(get_style("COMBO_WIDE"))
        grid.addWidget(self.inp_service, row, 3, 1, 2)
        row += 1
        
        # Charge | Type extrémités
        grid.addWidget(self._label(tr("calc.load_force")), row, 0)
        self.inp_F = self._input(30.0, 2, 0.01, 10000.0)
        grid.addWidget(self.inp_F, row, 1)
        
        grid.addWidget(self._label(tr("calc.end_type")), row, 2)
        self.inp_end_type = QComboBox()
        # Stocker les clés internes et afficher les traductions
        self._end_type_keys = DB.get_end_type_list() or ["RAPPROCHEES_MEULEES"]
        default_idx = 0
        for i, key in enumerate(self._end_type_keys):
            # Obtenir la traduction pour cette clé
            tr_key = f"end.{DB._end_type_key(key)}"
            display_name = tr(tr_key)
            if display_name == tr_key:
                display_name = key  # Fallback au nom original
            self.inp_end_type.addItem(display_name, key)
            if key == "RAPPROCHEES_MEULEES":
                default_idx = i
        # Sélectionner RAPPROCHEES_MEULEES par défaut
        self.inp_end_type.setCurrentIndex(default_idx)
        self.inp_end_type.setStyleSheet(get_style("COMBO_WIDE"))
        grid.addWidget(self.inp_end_type, row, 3, 1, 2)
        row += 1
        
        # H sous charge | Spires mortes
        grid.addWidget(self._label(tr("calc.load_height")), row, 0)
        self.inp_H_charge = self._input(80.0, 2, 1.0, 1000.0)
        grid.addWidget(self.inp_H_charge, row, 1)
        
        grid.addWidget(self._label(tr("calc.dead_turns")), row, 2)
        self.inp_nm = QDoubleSpinBox()
        self.inp_nm.setRange(0, 10)
        self.inp_nm.setSingleStep(0.5)
        self.inp_nm.setValue(3.0)
        self.inp_nm.setDecimals(1)
        self.inp_nm.setStyleSheet(get_style("INPUT"))
        self.inp_nm.setAlignment(Qt.AlignRight)
        grid.addWidget(self.inp_nm, row, 3)
        row += 1
        
        # Lc max | Sens
        grid.addWidget(self._label(tr("calc.max_solid_length")), row, 0)
        self.inp_Lc_max = self._input(60.0, 2, 1.0, 500.0)
        grid.addWidget(self.inp_Lc_max, row, 1)
        
        grid.addWidget(self._label(tr("calc.winding_direction")), row, 2)
        self.inp_sens = QComboBox()
        self.inp_sens.addItems([tr("calc.winding_right"), tr("calc.winding_left")])
        self.inp_sens.setStyleSheet(get_style("COMBO_WIDE"))
        grid.addWidget(self.inp_sens, row, 3, 1, 2)
        row += 1
        
        # === SECTION RÉSULTATS ===
        row += 1
        lbl_section2 = QLabel(tr("calc.section_results"))
        lbl_section2.setStyleSheet(f"font-weight: bold; color: {get_style('SECTION_COLOR')};")
        grid.addWidget(lbl_section2, row, 0, 1, 5)
        row += 1
        
        # Résultats ligne par ligne (2 colonnes de résultats)
        grid.addWidget(self._label(tr("calc.module_g")), row, 0)
        self.out_G = self._result()
        grid.addWidget(self.out_G, row, 1)
        grid.addWidget(self._label(tr("calc.index_c")), row, 2)
        self.out_c = self._result()
        grid.addWidget(self.out_c, row, 3)
        row += 1
        
        grid.addWidget(self._label(tr("calc.rm")), row, 0)
        self.out_Rm = self._result()
        grid.addWidget(self.out_Rm, row, 1)
        grid.addWidget(self._label(tr("calc.bergstrasser")), row, 2)
        self.out_K = self._result()
        grid.addWidget(self.out_K, row, 3)
        row += 1
        
        grid.addWidget(self._label(tr("calc.d_mini")), row, 0)
        self.out_d_mini = self._result(True)
        grid.addWidget(self.out_d_mini, row, 1)
        grid.addWidget(self._label(tr("calc.tau_adm")), row, 2)
        self.out_tau_adm = self._result()
        grid.addWidget(self.out_tau_adm, row, 3)
        row += 1
        
        grid.addWidget(self._label(tr("calc.tau_real")), row, 0)
        self.out_tau_reel = self._result(True)
        grid.addWidget(self.out_tau_reel, row, 1)
        grid.addWidget(self._label(tr("calc.work_percent")), row, 2)
        self.out_pct_travail = self._result()
        grid.addWidget(self.out_pct_travail, row, 3)
        row += 1
        
        grid.addWidget(self._label(tr("calc.active_turns")), row, 0)
        self.out_n = self._result(True)
        grid.addWidget(self.out_n, row, 1)
        grid.addWidget(self._label(tr("calc.total_turns")), row, 2)
        self.out_nt = self._result()
        grid.addWidget(self.out_nt, row, 3)
        row += 1
        
        grid.addWidget(self._label(tr("calc.free_length")), row, 0)
        self.out_L0 = self._result(True)
        grid.addWidget(self.out_L0, row, 1)
        grid.addWidget(self._label(tr("calc.solid_length_real")), row, 2)
        self.out_Lc = self._result()
        grid.addWidget(self.out_Lc, row, 3)
        row += 1
        
        grid.addWidget(self._label(tr("calc.spring_rate")), row, 0)
        self.out_R = self._result(True)
        grid.addWidget(self.out_R, row, 1)
        grid.addWidget(self._label(tr("calc.deflection")), row, 2)
        self.out_f = self._result()
        grid.addWidget(self.out_f, row, 3)
        row += 1
        
        grid.addWidget(self._label(tr("calc.inner_diameter")), row, 0)
        self.out_Di = self._result()
        grid.addWidget(self.out_Di, row, 1)
        grid.addWidget(self._label(tr("calc.outer_diameter")), row, 2)
        self.out_De = self._result()
        grid.addWidget(self.out_De, row, 3)
        row += 1
        
        # Zone alertes
        row += 1
        self.lbl_alerts = QLabel(tr("calc.valid_design"))
        self.lbl_alerts.setStyleSheet(get_style("ALERT_OK"))
        self.lbl_alerts.setWordWrap(True)
        grid.addWidget(self.lbl_alerts, row, 0, 1, 5)
        row += 1
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
        # Boutons
        btn_layout = QHBoxLayout()
        
        btn_ok = QPushButton(tr("calc.apply_close"))
        btn_ok.setMinimumWidth(130)
        btn_ok.clicked.connect(self._apply_and_close)
        
        btn_cancel = QPushButton(tr("common.cancel"))
        btn_cancel.setMinimumWidth(80)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        main_layout.addLayout(btn_layout)
    
    def _input(self, value, decimals, mini, maxi):
        spin = QDoubleSpinBox()
        spin.setRange(mini, maxi)
        spin.setDecimals(decimals)
        spin.setValue(value)
        spin.setStyleSheet(get_style("INPUT"))
        spin.setAlignment(Qt.AlignRight)
        return spin
    
    def _label(self, text):
        """Crée un label aligné à droite pour être près du champ de données."""
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return lbl
    
    def _result(self, important=False):
        lbl = QLabel("--")
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl.setStyleSheet(get_style("RESULT_IMPORTANT") if important else get_style("RESULT"))
        return lbl
    
    def _connect_signals(self):
        self.inp_diameter_type.currentTextChanged.connect(self._on_diameter_type_changed)
        self.inp_Dm.valueChanged.connect(self._on_diameter_param_changed)
        self.inp_H_charge.valueChanged.connect(self._recalc)
        self.inp_Lc_max.valueChanged.connect(self._recalc)
        self.inp_F.valueChanged.connect(self._on_force_param_changed)
        self.inp_nm.valueChanged.connect(self._recalc)
        # inp_matiere est maintenant un bouton, pas de signal currentTextChanged
        self.inp_d.currentTextChanged.connect(self._recalc)
        self.inp_service.currentTextChanged.connect(self._on_service_changed)
        self.inp_end_type.currentTextChanged.connect(self._on_end_type_changed)
        self.inp_sens.currentTextChanged.connect(self._recalc)  # CORRECTION v1.3: Connecter le sens d'enroulement
    
    def _on_diameter_param_changed(self, value):
        """Appelé quand le diamètre cible (Dm/Di/De) change."""
        self._recalc(force_diameter_update=True)
    
    def _on_force_param_changed(self, value):
        """Appelé quand la charge F change."""
        self._recalc(force_diameter_update=True)
    
    def _on_service_changed(self, value):
        """Appelé quand le type de service change."""
        self._recalc(force_diameter_update=True)
    
    def _on_diameter_type_changed(self, new_type):
        """
        Gère le changement de type de diamètre en convertissant la valeur
        pour que le ressort reste identique.
        """
        old_type = self._previous_diameter_type
        
        # Si pas de changement réel, ne rien faire
        if old_type == new_type:
            return
        
        # Obtenir le diamètre de fil actuel
        try:
            d = float(self.inp_d.currentText())
        except:
            d = 1.0
        
        # Obtenir la valeur actuelle
        current_value = self.inp_Dm.value()
        
        # Calculer le Dm actuel selon l'ancien type
        if "Di" in old_type:
            Dm_actual = current_value + d  # Di + d = Dm
        elif "De" in old_type:
            Dm_actual = current_value - d  # De - d = Dm
        else:
            Dm_actual = current_value  # Dm
        
        # Convertir vers le nouveau type
        if "Di" in new_type:
            new_value = Dm_actual - d  # Dm - d = Di
        elif "De" in new_type:
            new_value = Dm_actual + d  # Dm + d = De
        else:
            new_value = Dm_actual  # Dm
        
        # Mettre à jour la valeur sans déclencher de recalcul
        self.inp_Dm.blockSignals(True)
        self.inp_Dm.setValue(new_value)
        self.inp_Dm.blockSignals(False)
        
        # Mémoriser le nouveau type
        self._previous_diameter_type = new_type
        
        # Recalculer (le ressort devrait rester identique)
        self._recalc()
    
    def _on_end_type_changed(self, txt):
        # Utiliser currentData pour obtenir la clé interne
        end_type_key = self.inp_end_type.currentData()
        if end_type_key is None:
            end_type_key = txt  # Fallback
        
        # COUPEES et MEULEES: pas de spires mortes (nm=0)
        # RAPPROCHEES et RAPPROCHEES_MEULEES: spires mortes requises
        if end_type_key in ["COUPEES", "MEULEES"]:
            self.inp_nm.setValue(0)
            self.inp_nm.setEnabled(False)
        else:
            self.inp_nm.setEnabled(True)
            nm_min = DB.get_dead_coils_min(end_type_key)
            if self.inp_nm.value() < nm_min:
                self.inp_nm.setValue(nm_min)
            self.inp_nm.setMinimum(nm_min)
        self._recalc()
    
    def _open_material_dialog(self):
        """Ouvre le dialogue de selection de materiau."""
        dialog = MaterialSelectionDialog(self, self._current_material)
        if dialog.exec() == QDialogAccepted:
            new_material = dialog.get_selected_material()
            if new_material != self._current_material:
                self._current_material = new_material
                # Afficher le nom traduit sur le bouton
                self.inp_matiere.setText(DB.get_material_translation(new_material))
                # Forcer le recalcul complet avec nouveau matériau
                self._recalc(force_diameter_update=True)
    
    def _compute_Dm_from_target(self, target_diameter, diameter_type, d_wire):
        """
        Calcule le diamètre moyen Dm à partir du diamètre cible et du type.
        
        Args:
            target_diameter: Valeur du diamètre cible entrée par l'utilisateur
            diameter_type: "Dm (moyen)", "Di (intérieur)" ou "De (extérieur)"
            d_wire: Diamètre du fil
            
        Returns:
            float: Diamètre moyen Dm calculé
        """
        if "Di" in diameter_type:
            # Di = Dm - d  =>  Dm = Di + d
            return target_diameter + d_wire
        elif "De" in diameter_type:
            # De = Dm + d  =>  Dm = De - d
            return target_diameter - d_wire
        else:
            # Dm directement
            return target_diameter
    
    def _recalc(self, *args, force_diameter_update=False):
        if not DB.loaded:
            return
        
        # Lecture des entrées
        target_diameter = self.inp_Dm.value()
        diameter_type = self.inp_diameter_type.currentText()
        try:
            d = float(self.inp_d.currentText())
        except:
            d = 1.0
        
        # Si on force la mise à jour du diamètre, réinitialiser au plus petit disponible
        # pour que la boucle itérative trouve le bon d_mini
        if force_diameter_update:
            d = self._all_diameters[0] if self._all_diameters else 0.5
        
        F = self.inp_F.value()
        H_charge = self.inp_H_charge.value()
        Lc_max = self.inp_Lc_max.value()
        
        matiere = self._current_material
        # Utiliser currentData pour obtenir les clés internes
        service_name = self.inp_service.currentData() or self.inp_service.currentText()
        end_type = self.inp_end_type.currentData() or self.inp_end_type.currentText()
        
        G = DB.get_module_G(matiere)
        
        stress_key = DB.get_stress_factor_key(service_name)
        stress_factor = DB.get_stress_factor(matiere, stress_key)
        is_severe = (stress_key == "severe_dynamic")
        
        nm = self.inp_nm.value()
        
        # COUPEES et MEULEES: pas de spires mortes
        if end_type in ["COUPEES", "MEULEES"]:
            nm_reel = 0
        else:
            nm_reel = nm
        
        # === CALCUL ITÉRATIF POUR CONVERGER VERS LE DIAMÈTRE CIBLE ===
        # Si le type n'est pas Dm, on doit itérer pour trouver le bon Dm
        # car d_mini dépend de Dm, et Dm dépend de d
        
        max_iterations = 10
        tolerance = 0.001
        
        # Première estimation de Dm
        Dm = self._compute_Dm_from_target(target_diameter, diameter_type, d)
        
        for iteration in range(max_iterations):
            # Protection: Dm doit être positif et supérieur à d
            if Dm <= d:
                Dm = d + 1.0  # Valeur minimale raisonnable
            
            Rm = DB.get_Rm(matiere, d)
            c = Dm / d if d > 0 else 10
            K = get_coef_bergstrasser(c)
            tau_adm = Rm * stress_factor
            
            if is_severe:
                coef_k = K
                tau_adm_eff = tau_adm / K if K > 0 else tau_adm
            else:
                coef_k = 1.0
                tau_adm_eff = tau_adm
            
            # Calcul du diamètre minimum requis (protection contre valeurs négatives)
            if tau_adm_eff > 0 and Dm > 0 and F > 0:
                val = coef_k * 2.55 * F * Dm / tau_adm_eff
                d_mini = val ** (1/3) if val > 0 else 0
            else:
                d_mini = 0
            
            # Filtrer et obtenir le nouveau diamètre de fil (sans forcer pendant l'itération)
            self._filter_diameters(d_mini, force_select_minimum=False)
            try:
                d_new = float(self.inp_d.currentText())
            except:
                d_new = d
            
            # Recalculer Dm avec le nouveau diamètre de fil
            Dm_new = self._compute_Dm_from_target(target_diameter, diameter_type, d_new)
            
            # Protection: Dm doit rester positif
            if Dm_new <= 0:
                Dm_new = d_new + 1.0
            
            # Vérifier la convergence
            if abs(d_new - d) < tolerance and abs(Dm_new - Dm) < tolerance:
                d = d_new
                Dm = Dm_new
                break
            
            d = d_new
            Dm = Dm_new
        
        # Recalculer les valeurs finales avec Dm et d convergés
        Rm = DB.get_Rm(matiere, d)
        c = Dm / d if d > 0 else 10
        K = get_coef_bergstrasser(c)
        tau_adm = Rm * stress_factor
        
        if is_severe:
            coef_k = K
            tau_adm_eff = tau_adm / K if K > 0 else tau_adm
        else:
            coef_k = 1.0
            tau_adm_eff = tau_adm
        
        tau_reel = coef_k * 2.55 * F * Dm / (d ** 3) if d > 0 else 0
        # Protection contre valeurs négatives pour d_mini
        if tau_adm_eff > 0 and Dm > 0 and F > 0:
            val = coef_k * 2.55 * F * Dm / tau_adm_eff
            d_mini = val ** (1/3) if val > 0 else 0
        else:
            d_mini = 0
        
        # Si force_diameter_update, sélectionner le diamètre minimum recommandé
        if force_diameter_update:
            self._filter_diameters(d_mini, force_select_minimum=True)
            # Recalculer d avec le nouveau diamètre sélectionné
            try:
                d = float(self.inp_d.currentText())
            except:
                pass
            # Recalculer Dm et tau_reel avec le nouveau d
            Dm = self._compute_Dm_from_target(target_diameter, diameter_type, d)
            if Dm <= d:
                Dm = d + 1.0
            c = Dm / d if d > 0 else 10
            K = get_coef_bergstrasser(c)
            Rm = DB.get_Rm(matiere, d)
            tau_adm = Rm * stress_factor
            if is_severe:
                tau_adm_eff = tau_adm / K if K > 0 else tau_adm
                coef_k = K
            else:
                tau_adm_eff = tau_adm
                coef_k = 1.0
            tau_reel = coef_k * 2.55 * F * Dm / (d ** 3) if d > 0 else 0
        
        pct_travail = (tau_reel / tau_adm_eff * 100) if tau_adm_eff > 0 else 0
        
        # CORRECTION v1.3: Calcul du nombre de spires totales selon le type d'extrémité
        # - COUPEES et RAPPROCHEES: Lc_reel = (nt + 1) * d  =>  nt = floor(4*Lc_max/d)/4 - 1
        # - MEULEES et RAPPROCHEES_MEULEES: Lc_reel = nt * d  =>  nt = floor(4*Lc_max/d)/4
        is_ground = DB.is_ground_type(end_type)
        
        if d > 0:
            nt_quarter = math.floor(4 * Lc_max / d) / 4  # Arrondi au 1/4 de tour inférieur
            if is_ground:
                # MEULEES ou RAPPROCHEES_MEULEES
                nt = nt_quarter
                Lc_reel = nt * d
            else:
                # COUPEES ou RAPPROCHEES
                nt = nt_quarter - 1
                Lc_reel = (nt + 1) * d
        else:
            nt = 1
            Lc_reel = d
        
        n = max(0.5, nt - 2 * nm_reel)
        
        R = G * (d ** 4) / (8 * (Dm ** 3) * n) if Dm > 0 and n > 0 else 0
        f = F / R if R > 0 else 0
        L0 = H_charge + f
        
        Di = Dm - d
        De = Dm + d
        
        # Affichage
        self.out_G.setText(f"{G:.0f}")
        self.out_c.setText(f"{c:.2f}")
        self.out_Rm.setText(f"{Rm:.1f}")
        self.out_K.setText(f"{K:.3f}")
        self.out_d_mini.setText(f"{d_mini:.2f}")
        self.out_tau_adm.setText(f"{tau_adm_eff:.1f}")
        self.out_tau_reel.setText(f"{tau_reel:.1f}")
        self.out_pct_travail.setText(f"{pct_travail:.1f}%")
        self.out_n.setText(f"{n:.2f}")
        self.out_nt.setText(f"{nt:.2f}")
        self.out_L0.setText(f"{L0:.2f}")
        self.out_Lc.setText(f"{Lc_reel:.2f}")  # Afficher Lc réel calculé
        self.out_R.setText(f"{R:.4f}")
        self.out_f.setText(f"{f:.2f}")
        self.out_Di.setText(f"{Di:.2f}")
        self.out_De.setText(f"{De:.2f}")
        
        # Alertes - CORRECTION v1.3: calculées APRÈS le recalcul du diamètre
        alerts = []
        
        # Vérifier si d actuel < d_mini (après filtrage, ne devrait plus arriver)
        if d < d_mini:
            alerts.append(tr("alert.wire_diameter").format(d=d, d_mini=d_mini))
        if tau_reel > tau_adm_eff:
            alerts.append(tr("alert.stress").format(tau=tau_reel, tau_adm=tau_adm_eff))
        # Vérifier que Lc_reel <= Lc_max
        if Lc_reel > Lc_max:
            alerts.append(tr("alert.solid_length").format(lc_real=Lc_reel, lc_max=Lc_max))
        if L0 < Lc_reel:
            alerts.append(tr("alert.impossible").format(L0=L0, Lc=Lc_reel))
        if c < 4:
            alerts.append(tr("alert.index_low").format(c=c))
        elif c > 16:
            alerts.append(tr("alert.index_high").format(c=c))
        
        # NOUVEAU v1.3: Alerte guidage selon EN 13906-1
        # Rapport critique L0/Dm pour risque de flambage
        if Dm > 0:
            rapport_L0_Dm = L0 / Dm
            # Selon EN 13906-1, guidage recommandé si L0/Dm > 4
            if rapport_L0_Dm > 4:
                alerts.append(tr("alert.guidance").format(ratio=rapport_L0_Dm))
        
        # Vérifier que le pas des spires actives est valide
        active_height = H_charge - 2 * nm_reel * d
        if n > 0:
            pitch = active_height / n
            if pitch < d:
                alerts.append(tr("alert.pitch").format(pitch=pitch, d=d))
                alerts.append(tr("alert.pitch_hint"))
        
        if alerts:
            self.lbl_alerts.setText("\n".join(alerts))
            self.lbl_alerts.setStyleSheet(get_style("ALERT_WARN"))
        else:
            self.lbl_alerts.setText(tr("calc.valid_design"))
            self.lbl_alerts.setStyleSheet(get_style("ALERT_OK"))
        
        # Stocker les résultats pour application ultérieure
        # CORRECTION v1.3: Stocker L0, H_charge, Lc_max pour les 3 modes de représentation
        # Les paramètres d'entrée (H_charge, Lc_max) sont des valeurs utilisateur NON MODIFIABLES
        self._results = {
            # Géométrie
            'wireDiameter': d,
            'meanDiameter': Dm,
            'activeTurnsQty': n,
            'totalTurnsQty': nt,
            'deadTurnsQty': nm_reel,  # Spires mortes par face
            
            # Type de diamètre et valeur cible (pour persistance)
            'diameterType': diameter_type,
            'targetDiameter': target_diameter,
            
            # Hauteurs de REPRÉSENTATION (pour les 3 modes)
            'freeLength': L0,         # Mode libre: LCS à L0
            'onLoadHight': H_charge,  # Mode sous charge: LCS à H (valeur utilisateur)
            'minHeight': Lc_max,      # Mode bloc: LCS à Lc_max (valeur utilisateur)
            
            # Hauteurs calculées
            'solidHeight': Lc_reel,   # Lc réel calculé (pour vérification)
            'activeTurnsHight': H_charge - 2 * nm_reel * d,
            'deadTurnsHight': nm_reel * d,
            'minActiveTurnsHight': n * d,
            'maxActiveTurnsHight': L0 - 2 * nm_reel * d,
            
            # Charge et matériau
            'load': F,
            'loadType': service_name,
            'material': matiere,
            
            # Type d'extrémités
            'extremeTurns': end_type.replace("_", " "),
            'grinded': is_ground,
            
            # Sens d'enroulement
            'leftHanded': self.inp_sens.currentIndex() == 1  # 0=droite, 1=gauche
        }
    
    def _populate_from_spring_body(self, body):
        """Remplit l'interface avec les paramètres d'un Body"""
        widgets_to_block = [
            self.inp_diameter_type, self.inp_Dm, self.inp_d, self.inp_F, self.inp_H_charge,
            self.inp_Lc_max, self.inp_matiere, self.inp_service,
            self.inp_end_type, self.inp_nm, self.inp_sens
        ]
        
        for widget in widgets_to_block:
            widget.blockSignals(True)
        
        try:
            # Restaurer le type de diamètre et le diamètre cible
            if hasattr(body, 'diameterType'):
                dtype = str(body.diameterType)
                idx = self.inp_diameter_type.findText(dtype)
                if idx >= 0:
                    self.inp_diameter_type.setCurrentIndex(idx)
            
            # Utiliser targetDiameter si disponible, sinon meanDiameter
            if hasattr(body, 'targetDiameter') and body.targetDiameter > 0:
                self.inp_Dm.setValue(body.targetDiameter)
            elif hasattr(body, 'meanDiameter'):
                self.inp_Dm.setValue(body.meanDiameter)
            
            if hasattr(body, 'wireDiameter'):
                self.inp_d.setCurrentText(f"{body.wireDiameter:.2f}")
            
            if hasattr(body, 'load'):
                self.inp_F.setValue(body.load)
            
            if hasattr(body, 'onLoadHight'):
                self.inp_H_charge.setValue(body.onLoadHight)
            
            if hasattr(body, 'minHeight'):
                self.inp_Lc_max.setValue(body.minHeight)
            
            if hasattr(body, 'material'):
                mat = str(body.material)
                if mat in (DB.get_material_list() or []):
                    self._current_material = mat
                    # Afficher le nom traduit
                    self.inp_matiere.setText(DB.get_material_translation(mat))
            
            if hasattr(body, 'loadType'):
                # Chercher par la clé interne (itemData)
                load_type = str(body.loadType)
                for i in range(self.inp_service.count()):
                    if self.inp_service.itemData(i) == load_type:
                        self.inp_service.setCurrentIndex(i)
                        break
            
            if hasattr(body, 'extremeTurns'):
                end_type = str(body.extremeTurns).replace(" ", "_")
                # Chercher par la clé interne (itemData)
                for i in range(self.inp_end_type.count()):
                    if self.inp_end_type.itemData(i) == end_type:
                        self.inp_end_type.setCurrentIndex(i)
                        break
            
            if hasattr(body, 'deadTurnsQty'):
                self.inp_nm.setValue(body.deadTurnsQty)  # Correction v1.1: pas de division
            
            if hasattr(body, 'leftHanded'):
                # Trouver l'index correspondant (0=droite, 1=gauche)
                self.inp_sens.setCurrentIndex(1 if body.leftHanded else 0)
        
        finally:
            for widget in widgets_to_block:
                widget.blockSignals(False)
        
        # Mettre à jour le type précédent après chargement
        self._previous_diameter_type = self.inp_diameter_type.currentText()
        
        self._recalc()
    
    def _apply_and_close(self):
        """Applique les paramètres au Body et ferme"""
        if not self.current_spring_body:
            QMessageBox.warning(self, "Erreur", "Aucun ressort associé")
            return
        
        body = self.current_spring_body
        
        # Vérifier alertes
        if "⚠" in self.lbl_alerts.text():
            reply = QMessageBox.warning(
                self, "Alertes",
                f"Des alertes ont été détectées:\n\n{self.lbl_alerts.text()}\n\n"
                "Appliquer quand même ?",
                QMsgBoxYes | QMsgBoxNo, QMsgBoxNo
            )
            if reply != QMsgBoxYes:
                return
        
        try:
            # Appliquer les résultats au Body
            # Les propriétés sont en lecture seule, il faut les déverrouiller temporairement
            for param, value in self._results.items():
                if hasattr(body, param):
                    try:
                        # Déverrouiller temporairement (mode 0 = éditable)
                        body.setEditorMode(param, 0)
                    except:
                        pass
                    setattr(body, param, value)
                    try:
                        # Reverrouiller en lecture seule (mode 1 = ReadOnly)
                        body.setEditorMode(param, 1)
                    except:
                        pass
            
            # Calculer et appliquer les diamètres dérivés
            d = self._results.get('wireDiameter', 4.0)
            Dm = self._results.get('meanDiameter', 20.0)
            Di = Dm - d
            De = Dm + d
            
            # Appliquer internalDiameter
            if hasattr(body, 'internalDiameter'):
                try:
                    body.setEditorMode('internalDiameter', 0)
                    body.internalDiameter = Di
                    body.setEditorMode('internalDiameter', 1)
                except:
                    pass
            
            # Appliquer externalDiameter
            if hasattr(body, 'externalDiameter'):
                try:
                    body.setEditorMode('externalDiameter', 0)
                    body.externalDiameter = De
                    body.setEditorMode('externalDiameter', 1)
                except:
                    pass
            
            self.parameters_changed = True
            App.Console.PrintMessage(f"[SpringFull] Paramètres appliqués à: {body.Label}\n")
            App.Console.PrintMessage(f"  Di = {Di:.2f} mm, De = {De:.2f} mm\n")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur: {str(e)}")
    
    def get_results(self):
        """Retourne les résultats calculés"""
        return getattr(self, '_results', {})
    
    def has_changes(self):
        """Indique si des paramètres ont été modifiés"""
        return self.parameters_changed
    
    def keyPressEvent(self, event):
        """
        Surcharge pour empêcher la fermeture du dialogue par la touche Entrée.
        Le dialogue ne peut être fermé que par les boutons.
        """
        # Qt est importé au niveau du module
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Ignorer la touche Entrée
            event.ignore()
        else:
            # Comportement normal pour les autres touches
            super().keyPressEvent(event)
    
    def _filter_diameters(self, d_mini, force_select_minimum=False):
        """
        Filtre le ComboBox des diamètres pour n'afficher que ceux >= d_mini.
        Si le diamètre actuel est < d_mini ou si force_select_minimum=True, 
        sélectionne automatiquement le premier valide (le plus petit >= d_mini).
        
        Args:
            d_mini: Diamètre minimum calculé
            force_select_minimum: Si True, sélectionne toujours le premier diamètre valide
        """
        if self._updating_diameter:
            return
        
        self._updating_diameter = True
        
        try:
            # Sauvegarder le diamètre actuellement sélectionné
            current_text = self.inp_d.currentText()
            try:
                current_d = float(current_text)
            except:
                current_d = 4.0
            
            # Bloquer les signaux pendant la mise à jour
            self.inp_d.blockSignals(True)
            
            # Vider et repeupler avec les diamètres >= d_mini
            self.inp_d.clear()
            valid_diameters = [d for d in self._all_diameters if d >= d_mini]
            
            # S'assurer qu'il y a au moins un diamètre
            if not valid_diameters:
                valid_diameters = self._all_diameters[-5:] if len(self._all_diameters) >= 5 else self._all_diameters
            
            self.inp_d.addItems([f"{d:.2f}" for d in valid_diameters])
            
            # Si force_select_minimum, toujours sélectionner le premier (le plus petit valide)
            if force_select_minimum:
                self.inp_d.setCurrentIndex(0)
            # Sinon, restaurer la sélection si le diamètre actuel est valide
            elif current_d >= d_mini and current_d in valid_diameters:
                # Trouver l'index exact
                try:
                    idx = valid_diameters.index(current_d)
                    self.inp_d.setCurrentIndex(idx)
                except ValueError:
                    # Chercher le plus proche >= d_mini
                    self.inp_d.setCurrentIndex(0)
            else:
                # Diamètre actuel invalide: sélectionner le premier valide (le plus petit >= d_mini)
                self.inp_d.setCurrentIndex(0)
            
            self.inp_d.blockSignals(False)
            
        finally:
            self._updating_diameter = False

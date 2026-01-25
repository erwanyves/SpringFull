# -*- coding: utf-8 -*-
"""
SpringFullDataModule - Gestion des données du ressort via propriétés FreeCAD
Toutes les données sont stockées dans le Body, plus besoin de fichiers CSV/ODS

Version: 1.4 - Modifications:
- Propriétés visibles regroupées dans "Spring Params" en lecture seule
- Ajout propriétés calculées: internalDiameter, externalDiameter
- Propriétés internes masquées dans "Internal" (non visibles utilisateur)
"""

__author__ = "Yves Guillou"
__licence__ = "GPL"

import FreeCAD as App
import FreeCADGui as Gui
import os
import json

from SpringFull.SpringFullI18nModule import tr

# =============================================================================
# DÉFINITION DES PROPRIÉTÉS DU RESSORT
# =============================================================================

# Propriétés VISIBLES pour l'utilisateur (lecture seule, groupe "Spring Params")
# Ces propriétés sont affichées dans le panneau de propriétés FreeCAD
VISIBLE_PROPERTIES = {
    # === CONFIGURATION ===
    "configuration": {
        "type": "App::PropertyString",
        "group": "Spring Params",
        "description": "Mode de représentation actuel",
        "default": "Ressort sous charge",
        "readonly": True
    },
    
    # === CHARGE ===
    "load": {
        "type": "App::PropertyFloat",
        "group": "Spring Params",
        "description": "Charge nominale (daN)",
        "default": 30.0,
        "readonly": True
    },
    "loadType": {
        "type": "App::PropertyString",
        "group": "Spring Params",
        "description": "Type de service",
        "default": "SERVICE MOYEN - DYNAMIQUE LENT",
        "readonly": True
    },
    
    # === GÉOMÉTRIE ===
    "extremeTurns": {
        "type": "App::PropertyString",
        "group": "Spring Params",
        "description": "Type d'extrémités",
        "default": "RAPPROCHEES MEULEES",
        "readonly": True
    },
    "internalDiameter": {
        "type": "App::PropertyFloat",
        "group": "Spring Params",
        "description": "Diamètre intérieur Di (mm) = Dm - d",
        "default": 16.0,
        "readonly": True
    },
    "meanDiameter": {
        "type": "App::PropertyFloat",
        "group": "Spring Params",
        "description": "Diamètre moyen Dm (mm)",
        "default": 20.0,
        "readonly": True
    },
    "externalDiameter": {
        "type": "App::PropertyFloat",
        "group": "Spring Params",
        "description": "Diamètre extérieur De (mm) = Dm + d",
        "default": 24.0,
        "readonly": True
    },
    
    # === HAUTEURS ===
    "onLoadHight": {
        "type": "App::PropertyFloat",
        "group": "Spring Params",
        "description": "Hauteur sous charge H (mm)",
        "default": 88.23,
        "readonly": True
    },
    "freeLength": {
        "type": "App::PropertyFloat",
        "group": "Spring Params",
        "description": "Longueur libre L0 (mm)",
        "default": 100.0,
        "readonly": True
    },
    
    # === MATÉRIAU ===
    "material": {
        "type": "App::PropertyString",
        "group": "Spring Params",
        "description": "Matériau du ressort",
        "default": "CORDE A PIANO",
        "readonly": True
    },
}

# Propriétés INTERNES (cachées, groupe "Internal")
# Ces propriétés sont utilisées pour les calculs mais ne sont pas modifiables
INTERNAL_PROPERTIES = {
    # === GÉOMÉTRIE INTERNE ===
    "wireDiameter": {
        "type": "App::PropertyFloat",
        "group": "Internal",
        "description": "Diamètre du fil (mm)",
        "default": 4.0,
        "readonly": True
    },
    "activeTurnsQty": {
        "type": "App::PropertyFloat",
        "group": "Internal",
        "description": "Nombre de spires actives",
        "default": 9.0,
        "readonly": True
    },
    "deadTurnsQty": {
        "type": "App::PropertyFloat",
        "group": "Internal",
        "description": "Nombre de spires mortes (par face)",
        "default": 1.0,
        "readonly": True
    },
    "totalTurnsQty": {
        "type": "App::PropertyFloat",
        "group": "Internal",
        "description": "Nombre total de spires (nt)",
        "default": 13.0,
        "readonly": True
    },
    
    # === HAUTEURS INTERNES ===
    "activeTurnsHight": {
        "type": "App::PropertyFloat",
        "group": "Internal",
        "description": "Hauteur spires actives (mm)",
        "default": 64.23,
        "readonly": True
    },
    "deadTurnsHight": {
        "type": "App::PropertyFloat",
        "group": "Internal",
        "description": "Hauteur spires mortes (mm)",
        "default": 12.0,
        "readonly": True
    },
    "minActiveTurnsHight": {
        "type": "App::PropertyFloat",
        "group": "Internal",
        "description": "Hauteur min spires actives - à bloc (mm)",
        "default": 36.0,
        "readonly": True
    },
    "maxActiveTurnsHight": {
        "type": "App::PropertyFloat",
        "group": "Internal",
        "description": "Hauteur max spires actives - libre (mm)",
        "default": 64.23,
        "readonly": True
    },
    "minHeight": {
        "type": "App::PropertyFloat",
        "group": "Internal",
        "description": "Hauteur à bloc max - Lc max (mm)",
        "default": 60.0,
        "readonly": True
    },
    "solidHeight": {
        "type": "App::PropertyFloat",
        "group": "Internal",
        "description": "Hauteur à bloc réelle - Lc réel (mm)",
        "default": 55.0,
        "readonly": True
    },
    
    # === AUTRES PARAMÈTRES INTERNES ===
    "grinded": {
        "type": "App::PropertyBool",
        "group": "Internal",
        "description": "Extrémités meulées",
        "default": True,
        "readonly": True
    },
    "leftHanded": {
        "type": "App::PropertyBool",
        "group": "Internal",
        "description": "Enroulement à gauche",
        "default": False,
        "readonly": True
    },
    "simplified": {
        "type": "App::PropertyBool",
        "group": "Internal",
        "description": "Représentation simplifiée",
        "default": False,
        "readonly": True
    },
    "customHeight": {
        "type": "App::PropertyFloat",
        "group": "Internal",
        "description": "Hauteur personnalisée (mm)",
        "default": 0.0,
        "readonly": True
    },
    "customForce": {
        "type": "App::PropertyFloat",
        "group": "Internal",
        "description": "Charge personnalisée (daN)",
        "default": 0.0,
        "readonly": True
    },
    "displayHeight": {
        "type": "App::PropertyFloat",
        "group": "Internal",
        "description": "Hauteur affichée actuelle (mm)",
        "default": 0.0,
        "readonly": True
    },
    "diameterType": {
        "type": "App::PropertyString",
        "group": "Internal",
        "description": "Type de diamètre (Dm, Di, De)",
        "default": "Dm (moyen)",
        "readonly": True
    },
    "targetDiameter": {
        "type": "App::PropertyFloat",
        "group": "Internal",
        "description": "Diamètre cible entré par l'utilisateur (mm)",
        "default": 20.0,
        "readonly": True
    },
    "version": {
        "type": "App::PropertyFloat",
        "group": "Internal",
        "description": "Version du ressort",
        "default": 1.4,
        "readonly": True
    }
}

# Combinaison de toutes les propriétés
SPRING_PROPERTIES = {**VISIBLE_PROPERTIES, **INTERNAL_PROPERTIES}


class DataSet:
    """
    Classe de gestion des données du ressort.
    Toutes les données sont stockées comme propriétés du Body FreeCAD.
    Plus de dépendance aux fichiers CSV/ODS.
    """
    
    def __init__(self, body=None):
        """
        Initialisation du DataSet.
        
        Args:
            body: Body FreeCAD existant (optionnel). Si None, on attend setBody().
        """
        self.body = body
        self.diameterCoeff = 0.999  # Coefficient réduction diamètre fil
        self.newSpring = False
        
        # Chemins des fichiers de configuration
        self.macroPath = os.path.dirname(os.path.abspath(__file__))
        self.materialsDatabase = os.path.join(self.macroPath, 'utils', 'spring_materials_database.json')
        self.templateFile = os.path.join(self.macroPath, 'templates', 'default.json')
        
        # Charger les valeurs par défaut depuis le template
        self.defaults = self._loadDefaultTemplate()
        
        # IMPORTANT: Initialiser TOUS les attributs avec les valeurs par défaut
        # Cela garantit que les attributs existent même si le Body n'a pas les propriétés
        self._initializeAllAttributes()
        
        if body:
            self.setBody(body)
    
    def _initializeAllAttributes(self):
        """
        Initialise tous les attributs avec les valeurs par défaut.
        Appelé dans __init__ pour garantir que tous les attributs existent.
        """
        for prop_name, prop_def in SPRING_PROPERTIES.items():
            default_value = self.defaults.get(prop_name, prop_def['default'])
            setattr(self, prop_name, default_value)
        
        # Attributs dérivés (calculés dans datasFormatting)
        self.adjustedWireDiameter = 0.0
        self.offsetY = 0.0
        self.deadTurnsPitch = 0.0
        self.activeTurnsPitch = 0.0
    
    def _loadDefaultTemplate(self):
        """Charge le template par défaut depuis le fichier JSON."""
        defaults = {}
        
        try:
            if os.path.exists(self.templateFile):
                with open(self.templateFile, 'r', encoding='utf-8') as f:
                    template = json.load(f)
                
                # Extraire les valeurs de chaque section
                for section_name, section_data in template.items():
                    if isinstance(section_data, dict) and section_name not in ['description', 'version', 'created']:
                        for param_name, param_data in section_data.items():
                            if isinstance(param_data, dict) and 'value' in param_data:
                                defaults[param_name] = param_data['value']
                            elif not isinstance(param_data, dict):
                                # Valeur directe (format simplifié)
                                defaults[param_name] = param_data
                
                App.Console.PrintMessage(f"[SpringFull] {tr('console.template_loaded').format(count=len(defaults))}\n")
            else:
                App.Console.PrintWarning(f"[SpringFull] {tr('console.warn_template_not_found').format(path=self.templateFile)}\n")
                # Utiliser les valeurs par défaut de SPRING_PROPERTIES
                for prop_name, prop_def in SPRING_PROPERTIES.items():
                    defaults[prop_name] = prop_def['default']
                    
        except Exception as e:
            App.Console.PrintError(f"[SpringFull] {tr('console.error_template_load').format(error=e)}\n")
            # Fallback aux valeurs par défaut
            for prop_name, prop_def in SPRING_PROPERTIES.items():
                defaults[prop_name] = prop_def['default']
        
        return defaults
    
    def setBody(self, body):
        """
        Définit le Body et vérifie/crée les propriétés manquantes.
        
        Args:
            body: Body FreeCAD
        """
        self.body = body
        missing_count = self.ensureAllProperties()
        
        if missing_count > 0:
            App.Console.PrintMessage(f"[SpringFull] {tr('console.props_created').format(count=missing_count)}\n")
            self.newSpring = True
        
        # Charger les données depuis le Body
        self.loadFromBody()
    
    def ensureAllProperties(self):
        """
        Vérifie que toutes les propriétés existent sur le Body.
        Crée les propriétés manquantes avec les valeurs par défaut.
        Configure les propriétés en lecture seule.
        
        Returns:
            int: Nombre de propriétés créées
        """
        if not self.body:
            return 0
        
        created_count = 0
        
        for prop_name, prop_def in SPRING_PROPERTIES.items():
            if not hasattr(self.body, prop_name):
                try:
                    # Créer la propriété
                    self.body.addProperty(
                        prop_def['type'],
                        prop_name,
                        prop_def['group'],
                        prop_def['description']
                    )
                    
                    # Affecter la valeur par défaut
                    default_value = self.defaults.get(prop_name, prop_def['default'])
                    setattr(self.body, prop_name, default_value)
                    
                    App.Console.PrintMessage(f"{tr('console.prop_created').format(name=prop_name, value=default_value)}\n")
                    created_count += 1
                    
                except Exception as e:
                    App.Console.PrintWarning(f"[SpringFull] {tr('console.error_prop_create').format(name=prop_name, error=e)}\n")
            
            # Configurer en lecture seule si spécifié
            if prop_def.get('readonly', False):
                self._setPropertyReadOnly(prop_name)
        
        # Migration: supprimer les anciennes propriétés doublées si elles existent
        old_props = ['representation', 'matiere', 'spiresExtremes']
        for old_prop in old_props:
            if hasattr(self.body, old_prop):
                try:
                    # Migrer la valeur si la nouvelle propriété est vide
                    if old_prop == 'representation' and hasattr(self.body, 'configuration'):
                        if not self.body.configuration:
                            self.body.configuration = self.body.representation
                    elif old_prop == 'matiere' and hasattr(self.body, 'material'):
                        if not self.body.material:
                            self.body.material = self.body.matiere
                    elif old_prop == 'spiresExtremes' and hasattr(self.body, 'extremeTurns'):
                        if not self.body.extremeTurns:
                            self.body.extremeTurns = self.body.spiresExtremes
                    
                    # Note: On ne supprime pas les anciennes propriétés pour éviter
                    # de casser la compatibilité avec les anciens fichiers
                    App.Console.PrintMessage(f"{tr('console.prop_obsolete').format(name=old_prop)}\n")
                except:
                    pass
        
        return created_count
    
    def _setPropertyReadOnly(self, prop_name):
        """
        Configure une propriété en lecture seule.
        
        Args:
            prop_name: Nom de la propriété
        """
        if not self.body or not hasattr(self.body, prop_name):
            return
        
        try:
            # Définir le mode lecture seule via setEditorMode
            # Mode 1 = ReadOnly, Mode 2 = Hidden
            self.body.setEditorMode(prop_name, 1)  # 1 = ReadOnly
        except Exception as e:
            # Si setEditorMode n'est pas disponible (anciennes versions FreeCAD)
            App.Console.PrintWarning(f"[SpringFull] {tr('console.warn_readonly_failed').format(name=prop_name, error=e)}\n")
    
    def _setPropertyHidden(self, prop_name):
        """
        Cache une propriété dans l'interface.
        
        Args:
            prop_name: Nom de la propriété
        """
        if not self.body or not hasattr(self.body, prop_name):
            return
        
        try:
            # Mode 2 = Hidden
            self.body.setEditorMode(prop_name, 2)
        except:
            pass
    
    def loadFromBody(self):
        """
        Charge toutes les données depuis les propriétés du Body.
        Copie les valeurs dans les attributs de l'instance DataSet.
        Gère la compatibilité avec les anciennes propriétés doublées.
        """
        if not self.body:
            App.Console.PrintWarning(f"[SpringFull] {tr('console.warn_no_body_load')}\n")
            return
        
        # D'abord, charger les anciennes propriétés pour compatibilité
        # (elles seront écrasées si les nouvelles existent)
        old_props_mapping = {
            'representation': 'configuration',
            'matiere': 'material',
            'spiresExtremes': 'extremeTurns'
        }
        
        for old_prop, new_prop in old_props_mapping.items():
            if hasattr(self.body, old_prop):
                old_value = getattr(self.body, old_prop)
                if old_value:  # Ne pas écraser avec une valeur vide
                    setattr(self, new_prop, old_value)
                    App.Console.PrintMessage(f"{tr('console.migration').format(old=old_prop, new=new_prop, value=old_value)}\n")
        
        # Ensuite, charger les propriétés actuelles (écrase les anciennes si présentes)
        for prop_name in SPRING_PROPERTIES.keys():
            if hasattr(self.body, prop_name):
                value = getattr(self.body, prop_name)
                if value is not None and value != '':  # Ne pas écraser avec valeur vide
                    setattr(self, prop_name, value)
            # Sinon, on garde la valeur par défaut (déjà initialisée dans __init__)
        
        # Formater les données pour la génération du ressort
        self.datasFormatting()
        
        App.Console.PrintMessage(f"[SpringFull] {tr('console.data_loaded').format(name=self.body.Label)}\n")
    
    def saveToBody(self):
        """
        Sauvegarde toutes les données dans les propriétés du Body.
        Les propriétés en lecture seule sont temporairement déverrouillées.
        """
        if not self.body:
            App.Console.PrintWarning(f"[SpringFull] {tr('console.warn_no_body_save')}\n")
            return False
        
        try:
            for prop_name, prop_def in SPRING_PROPERTIES.items():
                if hasattr(self, prop_name) and hasattr(self.body, prop_name):
                    # Temporairement déverrouiller si en lecture seule
                    if prop_def.get('readonly', False):
                        try:
                            self.body.setEditorMode(prop_name, 0)  # 0 = Normal (éditable)
                        except:
                            pass
                    
                    value = getattr(self, prop_name)
                    setattr(self.body, prop_name, value)
                    
                    # Reverrouiller
                    if prop_def.get('readonly', False):
                        try:
                            self.body.setEditorMode(prop_name, 1)  # 1 = ReadOnly
                        except:
                            pass
            
            # Mettre à jour les diamètres calculés
            self._updateCalculatedDiameters()
            
            App.Console.PrintMessage(f"[SpringFull] {tr('console.data_saved').format(name=self.body.Label)}\n")
            return True
            
        except Exception as e:
            App.Console.PrintError(f"[SpringFull] {tr('console.error_save').format(error=e)}\n")
            return False
    
    def _updateCalculatedDiameters(self):
        """
        Met à jour les diamètres calculés (internalDiameter, externalDiameter).
        """
        if not self.body:
            return
        
        d = getattr(self, 'wireDiameter', 4.0)
        Dm = getattr(self, 'meanDiameter', 20.0)
        
        Di = Dm - d
        De = Dm + d
        
        # Mettre à jour les attributs
        self.internalDiameter = Di
        self.externalDiameter = De
        
        # Sauvegarder dans le Body
        if hasattr(self.body, 'internalDiameter'):
            try:
                self.body.setEditorMode('internalDiameter', 0)
                self.body.internalDiameter = Di
                self.body.setEditorMode('internalDiameter', 1)
            except:
                pass
        
        if hasattr(self.body, 'externalDiameter'):
            try:
                self.body.setEditorMode('externalDiameter', 0)
                self.body.externalDiameter = De
                self.body.setEditorMode('externalDiameter', 1)
            except:
                pass
    
    def datasFormatting(self):
        """
        Formate les données pour la génération du ressort.
        Calcule les paramètres dérivés.
        """
        # Conversion leftHanded en booléen si nécessaire
        if isinstance(self.leftHanded, (int, float)):
            self.leftHanded = bool(self.leftHanded)
        
        # Assurer que deadTurnsQty est numérique
        if isinstance(self.deadTurnsQty, str):
            try:
                self.deadTurnsQty = float(self.deadTurnsQty.replace(',', '.'))
            except:
                self.deadTurnsQty = 0.0
        
        # Diamètre ajusté (légère réduction pour éviter les problèmes géométriques)
        self.adjustedWireDiameter = self.wireDiameter * self.diameterCoeff
        
        # Déterminer si les extrémités sont meulées
        is_ground = False
        if hasattr(self, 'extremeTurns'):
            end_type_upper = self.extremeTurns.upper()
            if 'MEULEES' in end_type_upper or 'MEULÉE' in end_type_upper:
                is_ground = True
        
        # Calcul de l'offset Y selon le type d'extrémité
        if is_ground:
            if self.deadTurnsQty > 0.0001:
                # RAPPROCHEES MEULEES avec spires mortes
                self.offsetY = self.adjustedWireDiameter * self.diameterCoeff / 2
            else:
                # MEULEES sans spires mortes
                self.offsetY = 0
        else:
            # COUPEES ou autres
            self.minActiveTurnsHight -= self.wireDiameter
            self.maxActiveTurnsHight -= self.wireDiameter
            self.offsetY = 0
        
        # Paramètres dérivés
        self.deadTurnsPitch = self.wireDiameter
        
        # Mise à jour des diamètres calculés
        self.internalDiameter = self.meanDiameter - self.wireDiameter
        self.externalDiameter = self.meanDiameter + self.wireDiameter
        
        self.deadTurnsHight = self.deadTurnsQty * self.deadTurnsPitch
        self.activeTurnsPitch = self.activeTurnsHight / self.activeTurnsQty if self.activeTurnsQty > 0 else 0
        
        App.Console.PrintMessage(f"[SpringFull] {tr('console.format_data')}\n")
        App.Console.PrintMessage(f"{tr('console.format_dead_turns_qty').format(value=self.deadTurnsQty)}\n")
        App.Console.PrintMessage(f"{tr('console.format_dead_turns_pitch').format(value=self.deadTurnsPitch)}\n")
        App.Console.PrintMessage(f"{tr('console.format_dead_turns_height').format(value=self.deadTurnsHight)}\n")
        App.Console.PrintMessage(f"{tr('console.format_offset_y').format(value=self.offsetY)}\n")
        App.Console.PrintMessage(f"{tr('console.format_diameters').format(di=self.internalDiameter, de=self.externalDiameter)}\n")
    
    def initParameters(self, piece):
        """
        Initialise les paramètres de représentation sur le Body.
        Compatible avec l'ancien code Spring.
        
        Args:
            piece: Body FreeCAD
        """
        # S'assurer que les propriétés existent
        if not hasattr(piece, 'version'):
            piece.addProperty("App::PropertyFloat", "version", "Internal", "Version", 1)
        piece.version = 1.4
        
        if hasattr(piece, 'configuration'):
            piece.configuration = getattr(self, 'configuration', "Ressort sous charge")
        
        if hasattr(piece, 'material'):
            piece.material = getattr(self, 'material', "CORDE A PIANO")
        
        if hasattr(piece, 'extremeTurns'):
            piece.extremeTurns = getattr(self, 'extremeTurns', "RAPPROCHEES MEULEES")
        
        if hasattr(piece, 'simplified'):
            piece.simplified = getattr(self, 'simplified', False)


def ensureSpringProperties(body):
    """
    Fonction utilitaire pour s'assurer qu'un Body a toutes les propriétés Spring.
    
    Args:
        body: Body FreeCAD
        
    Returns:
        int: Nombre de propriétés créées
    """
    data = DataSet()
    data.body = body
    data.defaults = data._loadDefaultTemplate()
    return data.ensureAllProperties()


def isSpringBody(body):
    """
    Vérifie si un Body est un ressort SpringFull (ou ancien Spring).
    
    Args:
        body: Body FreeCAD
        
    Returns:
        bool: True si c'est un ressort SpringFull
    """
    # Propriétés caractéristiques d'un ressort (nouvelles ET anciennes)
    # On considère que c'est un ressort si on trouve les propriétés géométriques de base
    essential_markers = ['wireDiameter', 'meanDiameter', 'activeTurnsQty']
    
    for marker in essential_markers:
        if not hasattr(body, marker):
            return False
    
    # Vérifier aussi qu'on a au moins une propriété de configuration
    # (nouvelle ou ancienne)
    has_config = (
        hasattr(body, 'configuration') or 
        hasattr(body, 'representation') or
        hasattr(body, 'extremeTurns') or
        hasattr(body, 'spiresExtremes')
    )
    
    return has_config

# Chemin : SpringFullDataModule.py
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
__licence__ = "LGPL-2.1"

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
#
# NOTE i18n: "description_key" est résolue via tr() au moment de la création
# de la propriété (dans ensureAllProperties), PAS au chargement de ce module.
# FreeCAD fige le texte d'info-bulle à la création de la propriété : pour un
# Body déjà existant, la description ne sera donc pas retraduite si l'on
# change de langue plus tard dans la même session (seules les propriétés
# nouvellement créées reçoivent la description dans la langue active à cet
# instant). Voir audit UX finding #2.
VISIBLE_PROPERTIES = {
    # === CONFIGURATION ===
    "configuration": {
        "type": "App::PropertyString",
        "group": "Spring Params",
        "description_key": "prop.configuration",
        "default": "Ressort sous charge",
        "readonly": True
    },

    # === CHARGE ===
    "load": {
        "type": "App::PropertyFloat",
        "group": "Spring Params",
        "description_key": "prop.load",
        "default": 30.0,
        "readonly": True
    },
    "loadType": {
        "type": "App::PropertyString",
        "group": "Spring Params",
        "description_key": "prop.loadType",
        "default": "SERVICE MOYEN - DYNAMIQUE LENT",
        "readonly": True
    },

    # === GÉOMÉTRIE ===
    "extremeTurns": {
        "type": "App::PropertyString",
        "group": "Spring Params",
        "description_key": "prop.extremeTurns",
        "default": "RAPPROCHEES MEULEES",
        "readonly": True
    },
    "internalDiameter": {
        "type": "App::PropertyFloat",
        "group": "Spring Params",
        "description_key": "prop.internalDiameter",
        "default": 16.0,
        "readonly": True
    },
    "meanDiameter": {
        "type": "App::PropertyFloat",
        "group": "Spring Params",
        "description_key": "prop.meanDiameter",
        "default": 20.0,
        "readonly": True
    },
    "externalDiameter": {
        "type": "App::PropertyFloat",
        "group": "Spring Params",
        "description_key": "prop.externalDiameter",
        "default": 24.0,
        "readonly": True
    },

    # === HAUTEURS ===
    "onLoadHight": {
        "type": "App::PropertyFloat",
        "group": "Spring Params",
        "description_key": "prop.onLoadHight",
        "default": 88.23,
        "readonly": True
    },
    "freeLength": {
        "type": "App::PropertyFloat",
        "group": "Spring Params",
        "description_key": "prop.freeLength",
        "default": 100.0,
        "readonly": True
    },

    # === MATÉRIAU ===
    "material": {
        "type": "App::PropertyString",
        "group": "Spring Params",
        "description_key": "prop.material",
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
        "description_key": "prop.wireDiameter",
        "default": 4.0,
        "readonly": True
    },
    "activeTurnsQty": {
        "type": "App::PropertyFloat",
        "group": "Internal",
        "description_key": "prop.activeTurnsQty",
        "default": 9.0,
        "readonly": True
    },
    "deadTurnsQty": {
        "type": "App::PropertyFloat",
        "group": "Internal",
        "description_key": "prop.deadTurnsQty",
        "default": 1.0,
        "readonly": True
    },
    "totalTurnsQty": {
        "type": "App::PropertyFloat",
        "group": "Internal",
        "description_key": "prop.totalTurnsQty",
        "default": 13.0,
        "readonly": True
    },

    # === HAUTEURS INTERNES ===
    "activeTurnsHight": {
        "type": "App::PropertyFloat",
        "group": "Internal",
        "description_key": "prop.activeTurnsHight",
        "default": 64.23,
        "readonly": True
    },
    "deadTurnsHight": {
        "type": "App::PropertyFloat",
        "group": "Internal",
        "description_key": "prop.deadTurnsHight",
        "default": 12.0,
        "readonly": True
    },
    "minActiveTurnsHight": {
        "type": "App::PropertyFloat",
        "group": "Internal",
        "description_key": "prop.minActiveTurnsHight",
        "default": 36.0,
        "readonly": True
    },
    "maxActiveTurnsHight": {
        "type": "App::PropertyFloat",
        "group": "Internal",
        "description_key": "prop.maxActiveTurnsHight",
        "default": 64.23,
        "readonly": True
    },
    "minHeight": {
        "type": "App::PropertyFloat",
        "group": "Internal",
        "description_key": "prop.minHeight",
        "default": 60.0,
        "readonly": True
    },
    "solidHeight": {
        "type": "App::PropertyFloat",
        "group": "Internal",
        "description_key": "prop.solidHeight",
        "default": 55.0,
        "readonly": True
    },

    # === AUTRES PARAMÈTRES INTERNES ===
    "grinded": {
        "type": "App::PropertyBool",
        "group": "Internal",
        "description_key": "prop.grinded",
        "default": True,
        "readonly": True
    },
    "leftHanded": {
        "type": "App::PropertyBool",
        "group": "Internal",
        "description_key": "prop.leftHanded",
        "default": False,
        "readonly": True
    },
    "simplified": {
        "type": "App::PropertyBool",
        "group": "Internal",
        "description_key": "prop.simplified",
        "default": False,
        "readonly": True
    },
    "customHeight": {
        "type": "App::PropertyFloat",
        "group": "Internal",
        "description_key": "prop.customHeight",
        "default": 0.0,
        "readonly": True
    },
    "customForce": {
        "type": "App::PropertyFloat",
        "group": "Internal",
        "description_key": "prop.customForce",
        "default": 0.0,
        "readonly": True
    },
    "displayHeight": {
        "type": "App::PropertyFloat",
        "group": "Internal",
        "description_key": "prop.displayHeight",
        "default": 0.0,
        "readonly": True
    },
    "diameterType": {
        "type": "App::PropertyString",
        "group": "Internal",
        "description_key": "prop.diameterType",
        "default": "Dm (moyen)",
        "readonly": True
    },
    "targetDiameter": {
        "type": "App::PropertyFloat",
        "group": "Internal",
        "description_key": "prop.targetDiameter",
        "default": 20.0,
        "readonly": True
    },
    "version": {
        "type": "App::PropertyFloat",
        "group": "Internal",
        "description_key": "prop.version",
        "default": 1.4,
        "readonly": True
    },

    # === MODE DE CONFIGURATION (code interne, indépendant de la langue) ===
    # Ajouté en v1.5 (audit UX finding #4) : jusqu'ici, le mode de
    # représentation choisi (libre / sous charge / bloc / personnalisé)
    # n'existait que sous forme du texte affiché traduit stocké dans
    # "configuration", ré-interprété ensuite par correspondance de
    # sous-chaînes pour savoir quel bouton radio pré-cocher. Ce code fige
    # le choix réel indépendamment de la langue active ; "configuration"
    # reste la version lisible affichée à l'utilisateur.
    # Valeurs possibles : FREE, LOADED, SOLID, CUSTOM_HEIGHT, CUSTOM_FORCE.
    "configurationMode": {
        "type": "App::PropertyString",
        "group": "Internal",
        "description_key": "prop.configurationMode",
        "default": "LOADED",
        "readonly": True
    }
}

# Combinaison de toutes les propriétés
SPRING_PROPERTIES = {**VISIBLE_PROPERTIES, **INTERNAL_PROPERTIES}


def _inferLegacyConfigurationMode(config_str):
    """
    Déduit le mode de configuration (code interne indépendant de la langue)
    à partir de l'ancien texte affiché stocké dans "configuration".

    Utilisée UNE SEULE FOIS, en migration, quand la propriété
    configurationMode est créée pour un ressort existant qui ne l'a pas
    encore (voir ensureAllProperties). Ne doit jamais être appelée à
    chaque ouverture de dialogue : c'est précisément ce pattern
    (ré-interpréter un texte affiché traduit par correspondance de
    sous-chaînes) qui posait un risque de sélection silencieusement
    incorrecte - voir audit UX finding #4.

    Args:
        config_str: texte affiché précédemment stocké (n'importe quelle
            langue parmi celles déjà utilisées pour ce ressort)

    Returns:
        str: "FREE", "LOADED", "SOLID", "CUSTOM_HEIGHT" ou "CUSTOM_FORCE"
    """
    if not config_str:
        return "LOADED"

    s = config_str.lower()

    free_terms = ["libre", "free", "frei", "libera"]
    if any(t in s for t in free_terms):
        return "FREE"

    solid_terms = ["bloc", "solid", "block", "bloque", "blocco"]
    if any(t in s for t in solid_terms):
        return "SOLID"

    force_terms = ["charge definie", "charge définie", "custom load", "custom force",
                   "defined load", "benutzerdefinierte last", "carga personalizada",
                   "carico personalizzato"]
    if any(t in s for t in force_terms):
        return "CUSTOM_FORCE"

    height_terms = ["hauteur", "height", "höhe", "hohe", "altura", "altezza",
                    "personnalis", "custom", "benutzerdefiniert", "personaliza"]
    if any(t in s for t in height_terms):
        return "CUSTOM_HEIGHT"

    # "sous charge" / "loaded" / etc. par défaut, comme avant
    return "LOADED"


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
                    # Description résolue via tr() au moment de la création
                    # (langue active à cet instant), pas au chargement du
                    # module - voir la note en tête de VISIBLE_PROPERTIES.
                    description = tr(prop_def.get('description_key', prop_name))

                    # Créer la propriété
                    self.body.addProperty(
                        prop_def['type'],
                        prop_name,
                        prop_def['group'],
                        description
                    )

                    # Affecter la valeur par défaut
                    default_value = self.defaults.get(prop_name, prop_def['default'])

                    # Migration v1.5 (audit UX finding #4) : pour un ressort
                    # existant qui n'a pas encore la propriété
                    # configurationMode, déduire une valeur de départ
                    # cohérente à partir de l'ancien texte affiché
                    # "configuration" plutôt que de retomber sur la valeur
                    # par défaut "LOADED" qui pourrait être fausse. Cette
                    # inférence n'est faite qu'une seule fois, ici, à la
                    # création de la propriété - jamais rejouée ensuite.
                    if prop_name == 'configurationMode':
                        existing_display = getattr(self.body, 'configuration', '') if hasattr(self.body, 'configuration') else ''
                        if existing_display:
                            default_value = _inferLegacyConfigurationMode(existing_display)

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

        # v1.5: deadTurnsQty est la valeur de FABRICATION. Pour déterminer si
        # le ressort a des spires mortes MÉCANIQUES (donc RAPPROCHEES_MEULEES
        # vs MEULEES pur), on retire les +0.25 supplémentaires pour les types
        # meulés.
        EXTRA_DEAD_TURNS_270 = 0.25
        if is_ground:
            nm_mech = max(0.0, self.deadTurnsQty - EXTRA_DEAD_TURNS_270)
        else:
            nm_mech = self.deadTurnsQty

        # Calcul de l'offset Y selon le type d'extrémité
        if is_ground:
            if nm_mech > 0.0001:
                # RAPPROCHEES MEULEES avec spires mortes mécaniques
                self.offsetY = self.adjustedWireDiameter * self.diameterCoeff / 2
            else:
                # MEULEES sans spires mortes mécaniques (seule la rehausse de
                # fabrication +0.25 est présente)
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

        # v1.5: deadTurnsHight = hauteur PHYSIQUE de l'hélice morte (avant meulage)
        # = nm_manuf * pas. Le meulage retire ensuite 0.25*d à chaque extrémité.
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

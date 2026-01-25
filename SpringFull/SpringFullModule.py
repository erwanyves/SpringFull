# -*- coding: utf-8 -*-
"""
SpringFullModule - Classe Spring définissant la géométrie complète du ressort

Note: Ce module reprend le code fonctionnel de SpringModule.py.
La génération 3D du ressort n'a pas été modifiée.
Seuls les imports ont été adaptés pour SpringFull.

Version: 1.2 - Corrections:
- Correction duplication LCS lors du changement de représentation
- Centralisation de la gestion des LCS dans _find_or_create_lcs()
- Nettoyage des LCS dupliqués avant reconstruction
"""

__author__ = "Yves Guillou"
__licence__ = "GPL"

import FreeCAD as App
import FreeCADGui as Gui
import Sketcher
import Part
import time
import json
import os

# Import compatible PySide2/PySide6
try:
    from PySide6 import QtCore
    from PySide6 import QtWidgets as QtGui  # Alias pour compatibilité
except ImportError:
    from PySide import QtGui, QtCore

from SpringFull.SpringFullHelixModule import Helix
from SpringFull.SpringFullI18nModule import tr


class Spring:
    """
    Classe définissant la géométrie complète du ressort.
    Inclut les LCS pour les contraintes d'assemblage.
    """
    
    # Variable de classe pour le nom du body (compatibilité)
    bodyName = 'Spring'
    
    def __init__(self, data, piece, progress_dialog=None):
        self.piece = piece
        self.data = data
        self.progress_dialog = progress_dialog
        self.progress_value = 30  # Commence à 30% (après animation initiale)
        
        # Dictionnaire pour stocker les références aux objets créés
        self.objects = {}
        
        # Liste des features à réafficher à la fin (pour éviter le scintillement)
        self._hidden_features = []
        
        # Liste des LCS à réafficher à la fin
        self._hidden_lcs = []
        
        # CORRECTION v1.2: Nettoyer les LCS dupliqués AVANT de commencer
        self._cleanup_duplicate_lcs()
        
        Gui.Selection.addSelection(self.piece)
        
        # Vérifier si représentation simplifiée demandée
        if getattr(data, 'simplified', False):
            pad = self.create_simplified_cylinder(data)
            self.objects['Pad'] = pad
            self._show_all_features()  # Réafficher avant d'appliquer le matériau
            self._show_all_lcs()  # Réafficher les LCS
            self.apply_material_to_feature(data, pad, override_transparency=50.0)
        else:
            self.helixes(data)
            self._recompute()
            self.Limits(data)
            self._recompute()
            self._show_all_features()  # Réafficher avant d'appliquer le matériau
            self._show_all_lcs()  # Réafficher les LCS
            self.apply_material(data)
        
        # Replier le Body dans l'arbre
        self._collapse_body()
    
    def _hide_feature(self, feature):
        """Masque une feature temporairement (pour éviter le scintillement)."""
        if feature and hasattr(feature, 'ViewObject') and feature.ViewObject:
            try:
                feature.ViewObject.Visibility = False
                self._hidden_features.append(feature)
            except:
                pass
    
    def _show_all_features(self):
        """Réaffiche toutes les features masquées."""
        for feature in self._hidden_features:
            try:
                if feature and hasattr(feature, 'ViewObject') and feature.ViewObject:
                    feature.ViewObject.Visibility = True
            except:
                pass
        self._hidden_features.clear()
    
    def _hide_lcs(self, lcs):
        """Masque un LCS temporairement en sauvegardant son état initial."""
        if lcs and hasattr(lcs, 'ViewObject') and lcs.ViewObject:
            try:
                # Sauvegarder l'état initial (seulement si pas déjà dans la liste)
                already_tracked = any(item[0] == lcs for item in self._hidden_lcs)
                if not already_tracked:
                    was_visible = lcs.ViewObject.Visibility
                    self._hidden_lcs.append((lcs, was_visible))
                # Masquer dans tous les cas
                lcs.ViewObject.Visibility = False
                App.Console.PrintMessage(f"[SpringFull] {tr('console.lcs_hidden').format(name=lcs.Name)}\n")
            except Exception as e:
                App.Console.PrintWarning(f"[SpringFull] {tr('console.error_lcs_hide').format(name=lcs.Name, error=e)}\n")
    
    def _show_all_lcs(self):
        """Restaure l'état de visibilité initial des LCS."""
        doc = App.ActiveDocument
        for lcs, was_visible in self._hidden_lcs:
            try:
                if lcs and hasattr(lcs, 'ViewObject') and lcs.ViewObject:
                    lcs.ViewObject.Visibility = was_visible
                    App.Console.PrintMessage(f"[SpringFull] {tr('console.lcs_restored').format(name=lcs.Name, visible=was_visible)}\n")
            except Exception as e:
                App.Console.PrintWarning(f"[SpringFull] {tr('console.error_lcs_show').format(error=e)}\n")
        self._hidden_lcs.clear()
        
        # Forcer le rafraîchissement
        if doc:
            doc.recompute()
        Gui.updateGui()
    
    def _collapse_body(self):
        """Replie le Body dans l'arbre de modèle."""
        # QtCore et QtGui sont importés au niveau du module
        try:
            if self.piece and Gui.ActiveDocument:
                mw = Gui.getMainWindow()
                if mw:
                    # Chercher tous les QTreeWidget (le nom "treeWidget" ne fonctionne pas)
                    trees = mw.findChildren(QtGui.QTreeWidget)
                    if trees:
                        tree = trees[0]
                        # Chercher l'item correspondant au Body par son Label
                        items = tree.findItems(
                            self.piece.Label, 
                            QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive, 
                            0
                        )
                        if items:
                            tree.collapseItem(items[0])
        except Exception as e:
            App.Console.PrintWarning(f"[SpringFull] {tr('console.error_body_fold').format(error=e)}\n")
    
    def _update_progress(self, step_name):
        """Met à jour le dialogue de progression."""
        if self.progress_dialog:
            self.progress_value += 12
            if self.progress_value > 90:
                self.progress_value = 90
            self.progress_dialog.progress.setValue(self.progress_value)
            # QtGui est importé au niveau du module
            QtGui.QApplication.processEvents()
    
    def _get_display_height(self, data):
        """Retourne la hauteur d'affichage (displayHeight si défini, sinon onLoadHight)."""
        return getattr(data, 'displayHeight', data.onLoadHight)
    
    def _cleanup_duplicate_lcs(self):
        """
        CORRECTION v1.2: Supprime les LCS dupliqués pour CE Body uniquement.
        
        Gère le cas des fichiers multi-ressorts où les LCS originaux peuvent avoir
        des suffixes numériques (ex: Local_Top001, Local_Bottom001 pour le 2ème ressort).
        
        Logique:
        - Collecte tous les LCS "Top" et "Bottom" de ce Body
        - Conserve celui avec le suffixe numérique le plus bas (l'original)
        - Supprime les autres (duplicats créés lors des changements de représentation)
        """
        import re
        
        # Collecter tous les LCS de ce Body par catégorie
        top_lcs_list = []
        bottom_lcs_list = []
        
        for obj in self.piece.Group:
            if obj.TypeId == 'PartDesign::CoordinateSystem':
                name = obj.Name
                # Identifier les LCS Top (contient "Local_Top" mais pas "Bottom")
                if 'Local_Top' in name and 'Bottom' not in name:
                    top_lcs_list.append(obj)
                # Identifier les LCS Bottom
                elif 'Local_Bottom' in name:
                    bottom_lcs_list.append(obj)
        
        def extract_suffix_number(name, base_pattern):
            """
            Extrait le suffixe numérique d'un nom LCS.
            Ex: 'Local_Top' → 0, 'Local_Top001' → 1, 'Local_Top_002' → 2
            """
            # Pattern pour capturer les chiffres après le nom de base
            # Gère: Local_Top, Local_Top001, Local_Top_001, Local_Top_v2, etc.
            match = re.search(base_pattern + r'[_]?(\d+)?$', name)
            if match and match.group(1):
                return int(match.group(1))
            # Pas de suffixe numérique = c'est le premier (suffixe 0)
            if re.match(base_pattern + r'$', name):
                return 0
            return float('inf')  # Nom non reconnu, mettre à la fin
        
        def get_primary_and_duplicates(lcs_list, base_pattern):
            """
            Identifie le LCS principal (à conserver) et les duplicats (à supprimer).
            Le LCS avec le suffixe le plus bas est considéré comme l'original.
            """
            if not lcs_list:
                return None, []
            
            if len(lcs_list) == 1:
                return lcs_list[0], []
            
            # Trier par suffixe numérique (le plus petit = l'original)
            sorted_lcs = sorted(lcs_list, key=lambda x: extract_suffix_number(x.Name, base_pattern))
            
            return sorted_lcs[0], sorted_lcs[1:]
        
        # Identifier les LCS principaux et duplicats
        primary_top, duplicates_top = get_primary_and_duplicates(top_lcs_list, r'Local_Top')
        primary_bottom, duplicates_bottom = get_primary_and_duplicates(bottom_lcs_list, r'Local_Bottom')
        
        # Stocker les références aux LCS principaux pour réutilisation
        self._primary_top_lcs = primary_top
        self._primary_bottom_lcs = primary_bottom
        
        # Masquer les LCS principaux existants pendant la reconstruction
        if primary_top:
            App.Console.PrintMessage(f"[SpringFull] {tr('console.lcs_top_main').format(name=primary_top.Name)}\n")
            self._hide_lcs(primary_top)
        if primary_bottom:
            App.Console.PrintMessage(f"[SpringFull] {tr('console.lcs_bottom_main').format(name=primary_bottom.Name)}\n")
            self._hide_lcs(primary_bottom)
        
        # Supprimer les duplicats
        duplicates = duplicates_top + duplicates_bottom
        doc = App.ActiveDocument
        
        for obj in duplicates:
            try:
                App.Console.PrintMessage(f"[SpringFull] {tr('console.lcs_duplicate_deleted').format(name=obj.Name)}\n")
                self.piece.removeObject(obj)
                doc.removeObject(obj.Name)
            except Exception as e:
                App.Console.PrintWarning(f"[SpringFull] {tr('console.error_lcs_delete').format(name=obj.Name, error=e)}\n")
        
        if duplicates:
            App.Console.PrintMessage(f"[SpringFull] {tr('console.lcs_duplicates_deleted').format(count=len(duplicates))}\n")
            doc.recompute()
    
    def _find_or_create_lcs(self, lcs_type, z_offset):
        """
        CORRECTION v1.2: Fonction centralisée pour trouver ou créer un LCS.
        
        Utilise les LCS principaux identifiés par _cleanup_duplicate_lcs(),
        ou en crée un nouveau si nécessaire.
        
        Args:
            lcs_type: 'top' ou 'bottom'
            z_offset: Position Z du LCS
            
        Returns:
            PartDesign::CoordinateSystem: Le LCS trouvé ou créé
        """
        existing_lcs = None
        
        # Étape 1: Utiliser le LCS principal identifié lors du nettoyage
        if lcs_type == 'top':
            if hasattr(self, '_primary_top_lcs') and self._primary_top_lcs is not None:
                existing_lcs = self._primary_top_lcs
                App.Console.PrintMessage(f"[SpringFull] {tr('console.lcs_reuse_top').format(name=existing_lcs.Name)}\n")
        elif lcs_type == 'bottom':
            if hasattr(self, '_primary_bottom_lcs') and self._primary_bottom_lcs is not None:
                existing_lcs = self._primary_bottom_lcs
                App.Console.PrintMessage(f"[SpringFull] {tr('console.lcs_reuse_bottom').format(name=existing_lcs.Name)}\n")
        
        # Étape 2: Si non trouvé, créer un nouveau LCS
        if existing_lcs is None:
            base_name = 'Local_Top' if lcs_type == 'top' else 'Local_Bottom'
            existing_lcs = self.piece.newObject('PartDesign::CoordinateSystem', base_name)
            App.Console.PrintMessage(f"[SpringFull] {tr('console.lcs_created').format(name=existing_lcs.Name)}\n")
            
            # Stocker la référence pour les appels suivants
            if lcs_type == 'top':
                self._primary_top_lcs = existing_lcs
            else:
                self._primary_bottom_lcs = existing_lcs
        
        # Masquer le LCS pendant la construction
        self._hide_lcs(existing_lcs)
        
        # Configurer/mettre à jour le LCS
        existing_lcs.AttachmentOffset = App.Placement(
            App.Vector(0, 0, z_offset),
            App.Rotation(App.Vector(0, 0, 1), 0)
        )
        existing_lcs.MapReversed = False
        existing_lcs.AttachmentSupport = [(self.piece.Origin.OriginFeatures[3], '')]  # XY_Plane
        existing_lcs.MapPathParameter = 0.0
        existing_lcs.MapMode = 'ObjectXY'
        
        return existing_lcs
    
    def _recompute(self, force=False):
        """
        Recalcul sécurisé.
        Le recompute est toujours effectué car nécessaire pour les Shapes.
        """
        doc = App.ActiveDocument
        if doc:
            doc.recompute()
        else:
            App.Console.PrintWarning(f"[SpringFull] {tr('console.warn_no_active_doc')}\n")
    
    @staticmethod
    def _read_material_properties(material_file_path, material_name):
        """
        Lit les propriétés matériau depuis le fichier JSON.
        Les couleurs sont dans le bloc 'color' de chaque matériau.
        """
        try:
            with open(material_file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            materials = config.get('materials', {})
            metadata = config.get('metadata', {})
            color_data = None
            found_name = material_name
            material_upper = material_name.strip().upper()
            
            for mat_name, mat_props in materials.items():
                if mat_name.strip().upper() == material_upper:
                    color_data = mat_props.get('color')
                    found_name = mat_name
                    break
            
            if color_data is None:
                App.Console.PrintWarning(f"[SpringFull] {tr('console.warn_color_not_found').format(name=material_name)}\n")
                color_data = metadata.get('default_color')
                found_name = 'DEFAULT'
                if color_data is None:
                    return ("UNKNOWN MATERIAL", "(0.20, 0.20, 0.20)", "(0.29, 0.29, 0.29)",
                            "(0.98, 0.98, 0.98)", "(0.00, 0.00, 0.00)", "0.02", "0.00")
            
            def list_to_str(lst):
                return "({:.2f}, {:.2f}, {:.2f})".format(lst[0], lst[1], lst[2])
            
            diffuse = list_to_str(color_data.get('diffuse', [0.2, 0.2, 0.2]))
            ambient = list_to_str(color_data.get('ambient', [0.29, 0.29, 0.29]))
            specular = list_to_str(color_data.get('specular', [0.98, 0.98, 0.98]))
            emissive = list_to_str(color_data.get('emissive', [0, 0, 0]))
            shiny = str(color_data.get('shininess', 0.02))
            transpar = str(color_data.get('transparency', 0.0))
            
            return (found_name, diffuse, ambient, specular, emissive, shiny, transpar)
            
        except Exception as e:
            App.Console.PrintError(f"[SpringFull] {tr('console.error_material_read').format(error=str(e))}\n")
            return ("UNKNOWN MATERIAL", "(0.20, 0.20, 0.20)", "(0.29, 0.29, 0.29)",
                    "(0.98, 0.98, 0.98)", "(0.00, 0.00, 0.00)", "0.02", "0.00")
    
    @staticmethod
    def _tupled(myStr):
        """Convertit une chaîne "(r, g, b)" en tuple de floats"""
        myStr = myStr.replace("(", "").replace(")", "").replace(",", " ")
        return tuple(map(float, myStr.split()))
    
    def apply_material_to_feature(self, data, feature, override_transparency=None):
        """Applique le matériau à une feature spécifique"""
        try:
            thisMaterial, diffuse, ambient, specular, emissive, shiny, transpar = \
                Spring._read_material_properties(data.materialsDatabase, data.material)
            
            final_transparency = override_transparency if override_transparency is not None else float(transpar)
            
            App.Console.PrintMessage(f"[SpringFull] {tr('console.material_on_feature').format(name=feature.Name)}\n")
            
            if feature and Gui.ActiveDocument:
                view_provider = Gui.ActiveDocument.getObject(feature.Name)
                if view_provider:
                    self._apply_material_to_view(view_provider, diffuse, ambient, specular, emissive, shiny, final_transparency)
        except Exception as e:
            App.Console.PrintWarning(f"[SpringFull] {tr('console.error_material_apply').format(error=str(e))}\n")
    
    def apply_material(self, data, override_transparency=None):
        """Applique le matériau au Tip du Body et au Body lui-même"""
        try:
            thisMaterial, diffuse, ambient, specular, emissive, shiny, transpar = \
                Spring._read_material_properties(data.materialsDatabase, data.material)
            
            final_transparency = override_transparency if override_transparency is not None else float(transpar)
            
            App.Console.PrintMessage(f"[SpringFull] {tr('console.material_on_tip').format(name=self.piece.Tip.Name if self.piece.Tip else 'None')}\n")
            
            if self.piece and Gui.ActiveDocument:
                # Appliquer sur le Tip
                if self.piece.Tip:
                    view_obj = Gui.ActiveDocument.getObject(self.piece.Tip.Name)
                    if view_obj:
                        self._apply_material_to_view(view_obj, diffuse, ambient, specular, emissive, shiny, final_transparency)
                
                # Appliquer aussi sur le Body (FreeCAD 1.1+)
                body_view = Gui.ActiveDocument.getObject(self.piece.Name)
                if body_view:
                    self._apply_material_to_view(body_view, diffuse, ambient, specular, emissive, shiny, final_transparency)
                    
        except Exception as e:
            App.Console.PrintWarning(f"[SpringFull] {tr('console.error_material_apply').format(error=str(e))}\n")
    
    def _apply_material_to_view(self, view_obj, diffuse, ambient, specular, emissive, shiny, transparency):
        """Applique le matériau à un ViewObject avec compatibilité FreeCAD 1.0/1.1"""
        try:
            diffuse_tuple = Spring._tupled(diffuse)
            ambient_tuple = Spring._tupled(ambient)
            specular_tuple = Spring._tupled(specular)
            emissive_tuple = Spring._tupled(emissive)
            
            # Méthode 1: ShapeAppearance (FreeCAD 1.1+)
            if hasattr(view_obj, 'ShapeAppearance'):
                # ShapeAppearance utilise une liste de Material
                material = App.Material(
                    DiffuseColor=diffuse_tuple,
                    AmbientColor=ambient_tuple,
                    SpecularColor=specular_tuple,
                    EmissiveColor=emissive_tuple,
                    Shininess=float(shiny),
                    Transparency=transparency
                )
                view_obj.ShapeAppearance = [material]
                App.Console.PrintMessage(f"[SpringFull] {tr('console.material_applied_appearance')}\n")
                return
            
            # Méthode 2: ShapeMaterial (FreeCAD 1.0)
            if hasattr(view_obj, 'ShapeMaterial'):
                view_obj.ShapeMaterial = App.Material(
                    DiffuseColor=diffuse_tuple,
                    AmbientColor=ambient_tuple,
                    SpecularColor=specular_tuple,
                    EmissiveColor=emissive_tuple,
                    Shininess=float(shiny),
                    Transparency=transparency
                )
                App.Console.PrintMessage(f"[SpringFull] {tr('console.material_applied_material')}\n")
                return
            
            # Méthode 3: ShapeColor (fallback)
            if hasattr(view_obj, 'ShapeColor'):
                view_obj.ShapeColor = diffuse_tuple
                if hasattr(view_obj, 'Transparency'):
                    view_obj.Transparency = int(transparency * 100) if transparency < 1 else int(transparency)
                App.Console.PrintMessage(f"[SpringFull] {tr('console.material_applied_color')}\n")
                return
                
            App.Console.PrintWarning(f"[SpringFull] {tr('console.warn_no_material_property')}\n")
            
        except Exception as e:
            App.Console.PrintWarning(f"[SpringFull] {tr('console.error_material_apply').format(error=e)}\n")
    
    def helixes(self, data):
        """Création des hélices du ressort"""
        # Vérification du document actif
        if not App.ActiveDocument:
            raise Exception("Pas de document actif")
        
        if self.piece.Document != App.ActiveDocument:
            App.setActiveDocument(self.piece.Document.Name)
        
        Helix.part = self.piece
        Helix.offsetY = data.offsetY
        
        App.Console.PrintMessage(f"[SpringFull] {tr('console.creating_spring').format(name=self.piece.Name)}\n")
        App.Console.PrintMessage(f"{tr('console.on_load_height').format(value=data.onLoadHight)}\n")
        App.Console.PrintMessage(f"{tr('console.active_turns_height').format(value=data.activeTurnsHight)}\n")
        
        # Hélice principale
        self._update_progress("MainHelix")
        helix_mid = Helix(data, 'MainHelix', 'MainSketch',
                          data.activeTurnsPitch, data.activeTurnsHight,
                          data.activeTurnsQty, False)
        
        self.objects['MainHelix'] = helix_mid.helix
        self._hide_feature(helix_mid.helix)  # Masquer pour éviter le scintillement
        if helix_mid.drawing:
            self.objects['MainSketch'] = helix_mid.drawing
        
        self._recompute()
        
        main_helix_obj = self.objects['MainHelix']
        
        # Attendre que le Shape soit disponible
        max_attempts = 3
        for attempt in range(max_attempts):
            if main_helix_obj.Shape and main_helix_obj.Shape.Faces:
                break
            self._recompute()
            time.sleep(0.1)
        
        if not main_helix_obj.Shape or not main_helix_obj.Shape.Faces:
            raise Exception("MainHelix Shape non disponible")
        
        # CORRECTION v1.3: Créer des hélices mortes SEULEMENT si deadTurnsQty > 0
        # Pour COUPEES et MEULEES (nm=0), pas d'hélices mortes
        # Pour RAPPROCHEES et RAPPROCHEES_MEULEES (nm>0), créer les hélices mortes
        # Les Pockets (dans Limits) coupent les extrémités pour les types meulés
        
        if data.deadTurnsQty > 0.0001:
            num_faces = len(main_helix_obj.Shape.Faces)
            
            grind_height = data.deadTurnsHight
            grind_turns = data.deadTurnsQty
            grind_pitch = data.deadTurnsPitch
            grind_gap = 0
            
            App.Console.PrintMessage(f"[SpringFull] {tr('console.creating_dead_turns')}\n")
            App.Console.PrintMessage(f"{tr('console.dead_turns_qty').format(value=data.deadTurnsQty)}\n")
            App.Console.PrintMessage(f"{tr('console.grind_height').format(value=grind_height)}\n")
            App.Console.PrintMessage(f"{tr('console.grind_pitch').format(value=grind_pitch)}\n")
            
            Helix.part = self.piece
            
            # Hélice inférieure
            self._update_progress("LowerHelix")
            helix_bottom = Helix(data, 'LowerHelix', 'LowerSketch',
                                 grind_pitch, grind_height,
                                 grind_turns, True,
                                 gap=grind_gap, base_face=(main_helix_obj, 1))
            self.objects['LowerHelix'] = helix_bottom.helix
            self._hide_feature(helix_bottom.helix)  # Masquer pour éviter le scintillement
            
            # Hélice supérieure
            self._update_progress("UpperHelix")
            helix_top = Helix(data, 'UpperHelix', 'UpperSketch',
                              grind_pitch, grind_height,
                              grind_turns, False,
                              gap=grind_gap, base_face=(main_helix_obj, num_faces))
            self.objects['UpperHelix'] = helix_top.helix
            self._hide_feature(helix_top.helix)  # Masquer pour éviter le scintillement
            
            self.piece.Tip = helix_top.helix
        else:
            # Pas de spires mortes (COUPEES ou MEULEES)
            App.Console.PrintMessage(f"[SpringFull] {tr('console.no_dead_turns')}\n")
            self.piece.Tip = main_helix_obj
    
    def Limits(self, data):
        """Création des plans de limite pour meulage"""
        needs_limits = False
        if hasattr(data, 'extremeTurns'):
            end_type_upper = data.extremeTurns.upper()
            if 'MEULEES' in end_type_upper or 'MEULÉE' in end_type_upper:
                needs_limits = True
        
        if not needs_limits:
            App.Console.PrintMessage(f"[SpringFull] {tr('console.no_grinding')}\n")
            self.create_lcs_only(data)
            return
        
        App.Console.PrintMessage(f"[SpringFull] {tr('console.grinding_required')}\n")
        
        # Utiliser la hauteur d'affichage pour le positionnement
        display_height = self._get_display_height(data)
        
        self._update_progress("UpperPlane")
        upper_sketch, upper_plane, upper_lcs = self.create_limit_plane(
            data, 'UpperPlaneSketch', 'UpperPlane', 'Local_Top',
            display_height, reverse=1
        )
        self.objects['UpperPlaneSketch'] = upper_sketch
        self.objects['UpperPlane'] = upper_plane
        self.objects['Local_Top'] = upper_lcs
        self._hide_feature(upper_plane)  # Masquer pour éviter le scintillement
        
        self.piece.Tip = upper_plane
        self._recompute()
        
        self._update_progress("LowerPlane")
        lower_sketch, lower_plane, lower_lcs = self.create_limit_plane(
            data, 'LowerPlaneSketch', 'LowerPlane', 'Local_Bottom',
            0, reverse=0
        )
        self.objects['LowerPlaneSketch'] = lower_sketch
        self.objects['LowerPlane'] = lower_plane
        self.objects['Local_Bottom'] = lower_lcs
        self._hide_feature(lower_plane)  # Masquer pour éviter le scintillement
        
        self.piece.Tip = lower_plane
        self._recompute()
    
    def create_limit_plane(self, data, sketch_name, plane_name, lcs_name, offset, reverse):
        """Crée un plan de limite (sketch + pocket + LCS)"""
        # CORRECTION v1.2: Utiliser la fonction centralisée avec le type
        # CORRECTION v1.4: Utiliser offset passé en paramètre (displayHeight)
        lcs_type = 'top' if 'Top' in lcs_name else 'bottom'
        z_offset = offset if lcs_type == 'top' else 0
        lcs = self._find_or_create_lcs(lcs_type, z_offset)
        
        self._recompute()
        
        # Créer sketch
        sketch_obj = self.piece.newObject('Sketcher::SketchObject', sketch_name)
        sketch_obj.MapMode = 'FlatFace'
        sketch_obj.AttachmentSupport = [(lcs, '')]
        sketch_obj.AttachmentOffset = App.Placement(
            App.Vector(0, 0, 0),
            App.Rotation(App.Vector(0, 0, 1), 0)
        )
        
        self._recompute()
        
        sketch_obj.addGeometry(Part.Circle(
            App.Vector(0, 0, 0),
            App.Vector(0, 0, 1),
            data.externalDiameter / 2 * 1.5
        ), False)
        sketch_obj.addConstraint(Sketcher.Constraint('Coincident', 0, 3, -1, 1))
        sketch_obj.Visibility = False
        
        self._recompute()
        
        # Créer Pocket
        pocket = self.piece.newObject('PartDesign::Pocket', plane_name)
        pocket.Profile = sketch_obj
        pocket.Length = data.wireDiameter * 3
        pocket.Type = 0
        pocket.Reversed = reverse
        # Compatibilité FreeCAD 1.0 (Midplane) et 1.1+ (SideType)
        if hasattr(pocket, 'SideType'):
            pocket.SideType = 'One side'  # FreeCAD 1.1+
        elif hasattr(pocket, 'Midplane'):
            pocket.Midplane = 0  # FreeCAD 1.0
        pocket.UseCustomVector = 0
        
        self._recompute()
        
        return (sketch_obj, pocket, lcs)
    
    def create_lcs_only(self, data):
        """Crée uniquement les LCS sans plans de limite"""
        # CORRECTION v1.4: Utiliser displayHeight pour le positionnement
        display_height = self._get_display_height(data)
        lcs_top = self._find_or_create_lcs('top', display_height)
        lcs_bottom = self._find_or_create_lcs('bottom', 0)
        
        self.objects['Local_Top'] = lcs_top
        self.objects['Local_Bottom'] = lcs_bottom
        
        self._recompute()
    
    def create_simplified_cylinder(self, data):
        """Crée la représentation simplifiée (tube creux)"""
        App.Console.PrintMessage(f"[SpringFull] {tr('console.creating_simplified')}\n")
        
        sketch = self.piece.newObject('Sketcher::SketchObject', 'TubeSketch')
        sketch.AttachmentSupport = [(self.piece.Origin.OriginFeatures[3], '')]
        sketch.MapMode = 'FlatFace'
        self.objects['TubeSketch'] = sketch
        
        self._recompute()
        
        ext_radius = data.externalDiameter / 2
        internal_diameter = data.meanDiameter - data.wireDiameter
        int_radius = internal_diameter / 2
        
        sketch.addGeometry(Part.Circle(
            App.Vector(0, 0, 0),
            App.Vector(0, 0, 1),
            ext_radius
        ), False)
        
        sketch.addGeometry(Part.Circle(
            App.Vector(0, 0, 0),
            App.Vector(0, 0, 1),
            int_radius
        ), False)
        
        sketch.addConstraint(Sketcher.Constraint('Coincident', 0, 3, -1, 1))
        sketch.addConstraint(Sketcher.Constraint('Coincident', 1, 3, -1, 1))
        sketch.Visibility = False
        
        # CORRECTION v1.4: Utiliser displayHeight pour la longueur du tube
        display_height = self._get_display_height(data)
        
        pad = self.piece.newObject('PartDesign::Pad', 'SimplifiedSpringTube')
        pad.Profile = sketch
        pad.Length = display_height
        pad.Type = 'Length'
        pad.Reversed = False
        # Compatibilité FreeCAD 1.0 (Midplane) et 1.1+ (SideType)
        if hasattr(pad, 'SideType'):
            pad.SideType = 'One side'  # FreeCAD 1.1+
        elif hasattr(pad, 'Midplane'):
            pad.Midplane = False  # FreeCAD 1.0
        
        self.objects['Pad'] = pad
        self._hide_feature(pad)  # Masquer pour éviter le scintillement
        self.piece.Tip = pad
        self._recompute()
        
        # Fillets pour extrémités non meulées
        needs_fillets = False
        if hasattr(data, 'extremeTurns'):
            end_type_upper = data.extremeTurns.upper()
            if 'MEULEES' not in end_type_upper and 'MEULÉE' not in end_type_upper:
                needs_fillets = True
        
        if needs_fillets:
            fillet_radius = (data.wireDiameter / 2) - 0.001
            try:
                fillet = self.piece.newObject('PartDesign::Fillet', 'EndFillets')
                edges_to_fillet = []
                for i, edge in enumerate(pad.Shape.Edges):
                    if hasattr(edge.Curve, 'Radius'):
                        edges_to_fillet.append("Edge" + str(i+1))
                
                if edges_to_fillet:
                    fillet.Base = (pad, edges_to_fillet)
                    fillet.Radius = fillet_radius
                    self.objects['Fillet'] = fillet
                    self._hide_feature(fillet)  # Masquer pour éviter le scintillement
                    self.piece.Tip = fillet
                    self._recompute()
            except Exception as e:
                App.Console.PrintWarning(f"[SpringFull] {tr('console.error_fillets').format(error=str(e))}\n")
        
        # LCS - CORRECTION v1.4: Utiliser displayHeight
        self._create_simplified_lcs(data)
        
        return self.piece.Tip
    
    def _create_simplified_lcs(self, data):
        """Crée les LCS pour la représentation simplifiée"""
        # CORRECTION v1.4: Utiliser displayHeight pour le positionnement
        display_height = self._get_display_height(data)
        lcs_top = self._find_or_create_lcs('top', display_height)
        lcs_bottom = self._find_or_create_lcs('bottom', 0)
        
        self.objects['Local_Top'] = lcs_top
        self.objects['Local_Bottom'] = lcs_bottom

# -*- coding: utf-8 -*-
"""
SpringFullHelixModule - Classe Helix définissant les hélices du ressort

Note: Ce module est identique à SpringHelixModule.py original.
La génération 3D du ressort fonctionne parfaitement et n'a pas été modifiée.
"""

__author__ = "Yves Guillou"
__licence__ = "GPL"

import FreeCAD as App
import Part
import Sketcher


class Helix():
    """
    Classe définissant la géométrie des hélices du ressort.
    """
    
    def __init__(self, data, name, sketch, pitch, height, turns, reverse, gap=0, base_face=None):
        """
        Crée une hélice.
        
        Args:
            data: Objet de données du ressort
            name: Nom de la feature hélice
            sketch: Nom du sketch (utilisé seulement si base_face est None)
            pitch: Pas de l'hélice
            height: Hauteur de l'hélice
            turns: Nombre de tours
            reverse: Inverser la direction de l'hélice
            gap: Angle de décalage (obsolète, conservé pour compatibilité)
            base_face: Tuple (object, face_index) pour utiliser comme profil au lieu du sketch
        """
        # Stocker la référence à la pièce pour cette instance
        self.part = Helix.part
        
        if data.leftHanded:
            self.gap = gap
        else:
            self.gap = -gap
        
        if base_face is None:
            # Créer le sketch pour l'hélice principale (méthode originale)
            self.drawing = self._create_sketch_on_plane(data, sketch)
            
            # Créer la feature hélice APRÈS que le sketch soit prêt
            self.helix = self.part.newObject('PartDesign::AdditiveHelix', name)
            self.helix.Profile = self.drawing
            self.helix.ReferenceAxis = (self.drawing, ['V_Axis'])
        else:
            # Utiliser une face existante de l'hélice principale comme profil
            base_object, face_index = base_face
            
            # Créer la feature hélice
            self.helix = self.part.newObject('PartDesign::AdditiveHelix', name)
            
            # Définir la face directement comme profil
            self.helix.Profile = (base_object, ['Face' + str(face_index)])
            # Utiliser l'axe Z comme référence pour les hélices basées sur face
            self.helix.ReferenceAxis = (self.part.Origin.OriginFeatures[2], [''])  # Z_Axis est à l'index 2
            self.drawing = None  # Pas de sketch nécessaire
        
        # Configurer les paramètres de l'hélice
        self.helix.Pitch = pitch
        self.helix.Height = height
        self.helix.Turns = turns
        self.helix.LeftHanded = data.leftHanded
        self.helix.Reversed = reverse
        self.helix.AllowMultiFace = False
    
    def _create_sketch_on_plane(self, data, sketch_name):
        """Crée un sketch attaché au plan YZ (pour l'hélice principale)"""
        drawing = self.part.newObject('Sketcher::SketchObject', sketch_name)
        
        # Obtenir le YZ_Plane depuis l'Origin du Body
        yz_plane = None
        for feature in self.part.Origin.OriginFeatures:
            if 'YZ' in feature.Name or feature.Name == 'YZ_Plane':
                yz_plane = feature
                break
        if yz_plane is None:
            yz_plane = self.part.Origin.OriginFeatures[1]
        
        # Attacher le sketch au plan YZ
        drawing.MapMode = 'FlatFace'
        drawing.AttachmentSupport = [(yz_plane, '')]
        
        # Recalculer pour appliquer l'attachement
        App.ActiveDocument.recompute()
        
        # CORRECTION v1.3: Positionnement Z du centre du cercle selon type d'extrémité
        # - COUPEES: Z = d/2 (section tangente au LCS)
        # - MEULEES: Z = 0 (axe dans plan LCS, coupé par Pocket)
        # - RAPPROCHEES: Z = nm * d + d/2 (après spires mortes, section tangente)
        # - RAPPROCHEES_MEULEES: Z = nm * d (après spires mortes, axe coupé par Pocket)
        
        d = data.adjustedWireDiameter
        nm = data.deadTurnsQty if hasattr(data, 'deadTurnsQty') else 0
        
        # Déterminer le type d'extrémité
        end_type = ""
        if hasattr(data, 'extremeTurns'):
            end_type = data.extremeTurns.upper().replace(" ", "_")
        
        if end_type == "COUPEES" or (nm < 0.0001 and "MEULEES" not in end_type):
            # COUPEES: section tangente en bas, centre à d/2
            circle_center_y = d / 2
        elif end_type == "MEULEES" or (nm < 0.0001 and "MEULEES" in end_type):
            # MEULEES: axe dans le plan Z=0
            circle_center_y = 0
        elif "MEULEES" in end_type:
            # RAPPROCHEES_MEULEES: Z = nm * d
            circle_center_y = nm * d
        else:
            # RAPPROCHEES: Z = nm * d + d/2
            circle_center_y = nm * d + d / 2
        
        drawing.addGeometry(Part.Circle(
            App.Vector((data.meanDiameter / 2), circle_center_y, 0),
            App.Vector(0, 0, 1),
            (d / 2)), False)
        
        drawing.Visibility = False
        
        return drawing
    
    def workingHelixAngle(self, data):
        """Calcule l'angle de l'hélice (obsolète mais conservé pour compatibilité)"""
        activeTurnsAngle = data.activeTurnsQty % 1 * 360
        if data.leftHanded:
            activeTurnsAngle = -activeTurnsAngle
        return activeTurnsAngle

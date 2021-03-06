import math
import os

from xml.etree.ElementTree import SubElement, ElementTree

from bpy.props import StringProperty, EnumProperty, BoolProperty
from bpy.types import Panel

from .classes.building import Building
from .classes.color import Color
from .classes.face import Face
from .classes.face_type import FaceType
from .classes.orientation import Orientation

from ..functions import get_path, generate_file, handle_xml, handle_html
from .. import info

import bpy


class OBJECT_PT_ArToKi_EnergyReport(Panel):
    bl_label = "ArToKi - Energy - Report"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    properties = [
        ('atk_procedure_type', "Procedure"),
        ('atk_aerial', "Aerial view path"),
        ('atk_elevation', "Elevation view path"),
        ('atk_address1', "Street, Nb"),
        ('atk_address2', "PostCode City"),
        ('atk_therm_col', "Use thermic colors"),
    ]

    bpy.types.Scene.atk_aerial = StringProperty(
        name="Aerial",
        description="Aerial view path",
        default="",
        subtype='FILE_PATH')

    bpy.types.Scene.atk_elevation = StringProperty(
        name="Elevation",
        description="Elevation view path",
        default="",
        subtype='FILE_PATH')

    bpy.types.Scene.atk_address1 = StringProperty(
        name="Address 1",
        description="Street, nb",
        default="")

    bpy.types.Scene.atk_address2 = StringProperty(
        name="Address 2",
        description="PostCode City",
        default="")

    bpy.types.Scene.atk_therm_col = BoolProperty(
        name="Therm col",
        description="Assign materials colors by performance",
        default=0)

    bpy.types.Scene.atk_procedure_type = EnumProperty(
        items=[('PAE', 'PAE', 'Procédure d\'audit énergétique'),
               ('PEB', 'PEB', 'Performances énergétiques des batiments')],
        name="Procedure type",
        description="Changes the upper left text logo",
        default="PEB")

    def draw_properties(self):
        for prop in self.properties:
            row = self.layout.row()
            row.prop(bpy.context.scene, prop[0], text=prop[1])

    def draw_subtitle(self, text):
        self.layout.separator()
        self.layout.label(text=text)

    def draw_volume_and_area(self, volume, area):
        row = self.layout.row()
        row.alignment = 'EXPAND'

        box = row.box()
        column = box.column()

        sub_row = column.row(align=True)
        sub_row.label(text="Volume of the enveloppe:   " + str(round(volume, 2)) + " m\xb3", icon='VIEW3D')
        sub_row.label(text="Surface of the enveloppe:   " + str(round(area, 2)) + " m\xb2", icon='MESH_GRID')

    def draw_walls(self, faces, xml_projections, html_projections):
        projection_id = 0
        face_type_id = FaceType.WALL.get_id()

        for orientation in Orientation:
            faces_proj: [Face] = []
            mat_proj = []
            surf_proj = 0

            # déterminer les faces de la projection et la surface de la projection
            for face in faces:
                if face.orientation == orientation and face.type == FaceType.WALL:
                    faces_proj.append(face)
                    surf_proj += face.area

            if surf_proj != 0:
                row = self.layout.row()
                row.alignment = 'EXPAND'

                box = row.box()

                column = box.column()

                sub_row = column.row(align=True)
                sub_row.label(
                    text=str(orientation.name) + " Projection          Surface : " + str(
                        round(surf_proj, 2)) + " m\xb2",
                    icon='CURSOR')
                # on peut refaire le moteur apd ici...
                sub_row = column.row(align=True)
                sub_row.separator()
                projection = SubElement(xml_projections[face_type_id], 'WallProjection', Id=str(projection_id),
                                        Orientation=str(orientation.name), Surf=str(round(surf_proj, 2)))

                projection_id += 1

                for face_proj in faces_proj:
                    # si le matériau de la face n'existe pas encore dans mat_proj
                    if mat_proj.count(str(face_proj.material)) == 0:
                        # ajouter le matériau dans mat_proj [@name='a']
                        mat_proj.append(face_proj.material)

                for material_proj in sorted(mat_proj):
                    sub_row = column.row(align=True)
                    surf_mat = 0
                    for face_proj in faces_proj:
                        if face_proj.material == material_proj:
                            surf_mat += face_proj.area

                    sub_row.label(text=5 * ' ' + material_proj + ' : ' + str(round(surf_mat, 2)) + " m\xb2",
                                  icon='MOD_BUILD')
                    wallpart = SubElement(projection, 'WallPart', id=str(material_proj), Surf=str(round(surf_mat, 2)))

                projection_html_1 = SubElement(
                    html_projections[face_type_id][0][1 if projection_id <= 4 else 2], 'td')
                projection_html_1_table = SubElement(projection_html_1, 'table')
                projection_html_1_table.attrib["id"] = "walls_projection"
                tbody = SubElement(projection_html_1_table, 'tbody')
                caption = SubElement(tbody, 'caption')  # , Orientation=str(p), Surf=str(round(surf_proj,2))
                caption.text = "Az.: " + str(orientation.name) + " - " + str(round(surf_proj, 2)) + " m²"

                for face_proj in faces_proj:
                    # si le matériau de la face n'existe pas encore dans mat_proj
                    if mat_proj.count(str(face_proj.material)) == 0:
                        # ajouter le matériau dans mat_proj [@name='a']
                        mat_proj.append(face_proj.material)

                for material_proj in sorted(mat_proj):
                    surf_mat = 0
                    for face_proj in faces_proj:
                        if face_proj.material == material_proj:
                            surf_mat += face_proj.area

                    tr = SubElement(tbody, 'tr')
                    td_1 = SubElement(tr, 'td')
                    td_1.attrib["class"] = "mat_color"

                    color = Color()
                    for material_slot in bpy.context.object.material_slots:
                        if material_slot.name[0:4] == material_proj:
                            color = Color.from_8_bits_color(material_slot.material.diffuse_color)

                    td_1.attrib["style"] = "color:" + str(color)
                    td_1.text = "\u25A0"
                    td_2 = SubElement(tr, 'td')
                    td_2.attrib["class"] = "mat_index"
                    td_2.text = str(material_proj)
                    td_3 = SubElement(tr, 'td')
                    td_3.attrib["class"] = "mat_surf"
                    td_3.text = str(round(surf_mat, 2)) + " m²"

    def draw_floors(self, faces, xml_projections, html_projections, tree_html):
        row = self.layout.row()
        row.alignment = 'EXPAND'

        box = row.box()

        column = box.column()

        area_vert = 0
        faces_vert = []
        mat_vert = []
        face_type_id = FaceType.FLOOR.get_id()

        for face in faces:
            if face.type == FaceType.FLOOR:
                faces_vert.append(face)
                area_vert += face.projection_area

        if area_vert != 0:
            sub_row = column.row(align=True)
            sub_row.label(text="Floors Projection     Surface : " + str(round(area_vert, 2)) + " m\xb2", icon="TEXTURE")
            sub_row = column.row(align=True)
            sub_row.separator()
            xml_projections[face_type_id].attrib['Surf'] = str(round(area_vert, 2))  #
            html_projections[face_type_id].attrib['Surf'] = str(round(area_vert, 2))  #
            caption = tree_html.find(".//table[@id='floors_values']/tbody/caption")
            caption.text = 'Projection Sols: ' + str(round(area_vert, 2)) + ' m²'

            for face_proj in faces_vert:
                if mat_vert.count(str(face_proj.material)) == 0:
                    mat_vert.append(face_proj.material)

            for material_proj in sorted(mat_vert):
                sub_row = column.row(align=True)
                surf_mat_vert = 0
                for face_proj in faces_vert:
                    if face_proj.material == material_proj:
                        surf_mat_vert += face_proj.projection_area

                sub_row.label(text=5 * ' ' + material_proj + ' : ' + str(round(surf_mat_vert, 2)) + " m\xb2",
                              icon="ASSET_MANAGER")

                tr = SubElement(html_projections[face_type_id][0], 'tr')
                td_1 = SubElement(tr, 'td')
                td_1.attrib["class"] = "mat_color"

                color = Color()
                for material_slot in bpy.context.object.material_slots:
                    if material_slot.name[0:4] == material_proj:
                        color = Color.from_8_bits_color(material_slot.material.diffuse_color)

                td_1.attrib["style"] = "color:" + str(color)
                td_1.text = "\u25A0"
                td_2 = SubElement(tr, 'td')
                td_2.attrib["class"] = "mat_index"
                td_2.text = str(material_proj)
                td_3 = SubElement(tr, 'td')
                td_3.attrib["class"] = "mat_surf"
                td_3.text = str(round(surf_mat_vert, 2)) + " m²"

    def draw_roofs(self, faces, xml_projections, html_projections, tree_html):
        row = self.layout.row()
        row.alignment = 'EXPAND'
        box = row.box()
        column = box.column()
        surf_roof = 0
        surf_proj_roof = 0
        faces_roof = []
        mat_roof = []
        face_type_id = FaceType.ROOF.get_id()

        for face in faces:
            if face.type == FaceType.ROOF:
                faces_roof.append(face)
                surf_roof += face.area
                surf_proj_roof += face.projection_area

        if surf_roof != 0:
            sub_row = column.row(align=True)
            sub_row.label(text="Roofs Projection     Surface : " + str(round(surf_proj_roof, 2)) + " m\xb2",
                          icon="LINCURVE")
            sub_row = column.row(align=True)
            sub_row.separator()

            xml_projections[face_type_id].attrib['Surf'] = str(round(surf_proj_roof, 2))  #
            html_projections[face_type_id].attrib['Surf'] = str(round(surf_proj_roof, 2))  #

            caption = tree_html.find(".//table[@id='roofs_values']/tbody/caption")
            caption.text = 'Projection Toitures: ' + str(round(surf_proj_roof, 2)) + ' m²'

            for face_proj in faces_roof:
                if mat_roof.count(str(face_proj.material)) == 0:
                    mat_roof.append(face_proj.material)

            for material_proj in sorted(mat_roof):
                sub_row = column.row(align=True)
                area_mat_roof = 0
                area_proj_mat_roof = 0
                roof_angle = 0
                roof_orientation = ''

                for face_proj in faces_roof:
                    if face_proj.material == material_proj:
                        area_mat_roof += face_proj.area
                        area_proj_mat_roof += face_proj.projection_area
                        roof_angle = face_proj.angle
                        roof_orientation = face_proj.orientation

                sub_row.label(text=material_proj + ' : ' + str(round(area_mat_roof, 2)) + " m\xb2", icon="MOD_ARRAY")
                sub_row.label(text='Proj. : ' + str(roof_orientation.name))
                sub_row.label(text='Angle : ' + str(round(math.fabs(math.degrees(roof_angle)), 1)) + " \xb0")
                sub_row.label(text='Proj. surf. : ' + str(round(area_proj_mat_roof, 2)) + " m\xb2")

                roof_part = SubElement(
                    xml_projections[face_type_id],
                    'RoofPart',
                    Angle=str(round(math.fabs(math.degrees(roof_angle)), 1)),
                    Id=str(material_proj),
                    Orientation=str(roof_orientation.name),
                    Surf=str(round(area_mat_roof, 2)),
                    SurfProj=str(round(area_proj_mat_roof, 2))
                )

                tr = SubElement(html_projections[face_type_id], 'tr')
                td_1 = SubElement(tr, 'td')
                td_1.attrib["class"] = "mat_color"

                color = Color()
                for material_slot in bpy.context.object.material_slots:
                    if material_slot.name[0:4] == material_proj:
                        color = Color.from_8_bits_color(material_slot.material.diffuse_color)

                td_1.attrib["style"] = "color:" + str(color)
                td_1.text = "\u25A0"
                td_2 = SubElement(tr, 'td')
                td_2.attrib["class"] = "mat_index"
                td_2.text = str(material_proj)
                td_3 = SubElement(tr, 'td')
                td_3.attrib["class"] = "mat_surf_brute"
                td_3.text = str(round(area_mat_roof, 2)) + " m²"
                td_4 = SubElement(tr, 'td')
                td_4.attrib["class"] = "mat_angle"
                td_4.text = str(round(math.fabs(math.degrees(roof_angle)), 1)) + " °"
                td_5 = SubElement(tr, 'td')
                td_5.attrib["class"] = "mat_orient"
                td_5.text = str(roof_orientation.name)
                td_6 = SubElement(tr, 'td')
                td_6.attrib["class"] = "mat_surf_proj"
                td_6.text = str(round(area_proj_mat_roof, 2)) + " m²"

    def draw_summary(self, faces):
        row = self.layout.row()
        row.alignment = 'EXPAND'
        box = row.box()

        for face_type in FaceType:
            column = box.column()
            sub_row = column.row(align=True)
            sub_row.label(text=face_type.get_name(), icon=face_type.get_icon())

            for material_slot in bpy.context.object.material_slots:
                xml_surf_mat = 0

                for face in faces:
                    if material_slot.name[0:4] == face.material:
                        xml_surf_mat += face.area

                if material_slot.name[0] in face_type.get_letters():
                    sub_row = column.row(align=True)
                    sub_row.label(text=material_slot.name[0:4] + "  " + material_slot.name[5:] + " : ")
                    sub_row.label(text=str(round(xml_surf_mat, 2)) + " m\xb2")

    def draw_exports(self):
        row = self.layout.row()
        row.operator("export.xml", text="Save")
        row.operator("export.html", text="Export to pdf...")

    def draw_credits(self):
        # Only line to change for lite version for Windows
        dirname = get_path('labels')

        img_src = 'ArToKi.png'
        if bpy.data.images.find(img_src) == -1:
            img_a_plus = bpy.data.images.load(os.path.join(dirname, img_src))
            img_a_plus.user_clear()  # Won't get saved into .blend files

        row = self.layout.row()
        icon_artoki = self.layout.icon(bpy.data.images[img_src])
        row.label(text="ArToKi - Energy by tmaes" + 60 * " " + " info@tmaes.be", icon_value=icon_artoki)

    def draw(self, context):
        building = Building(context.object)

        xml_projections, xml_tree, xml_temp_file = handle_xml(building)
        html_projections, html_tree, html_temp_file = handle_html(building)

        self.draw_properties()

        self.draw_volume_and_area(building.eval_volume(), building.eval_area())

        self.draw_subtitle(text=FaceType.WALL.get_name())
        self.draw_walls(building.faces, xml_projections, html_projections)

        self.draw_subtitle(text=FaceType.FLOOR.get_name())
        self.draw_floors(building.faces, xml_projections, html_projections, html_tree)

        self.draw_subtitle(text=FaceType.ROOF.get_name())
        self.draw_roofs(building.faces, xml_projections, html_projections, html_tree)

        self.draw_subtitle(text="Summary")
        self.draw_summary(building.faces)

        self.draw_exports()
        self.draw_credits()

        generate_file(xml_tree, xml_temp_file)
        generate_file(html_tree, html_temp_file)

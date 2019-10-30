from bpy.types import Panel, UIList, Menu
import bpy
from . import utils


class LightfieldButtonsPanel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'

    @classmethod
    def poll(cls, context):
        ob = context.object
        if (not ob) or (not ob.type == 'EMPTY'):
            return False
        scn = context.scene
        lf = scn.lightfield
        for lightfield in lf:
            if lightfield.obj_empty == ob:
                return True
        return False


# -------------------------------------------------------------------
#   Data tab
# -------------------------------------------------------------------

class DATA_PT_lightfield_setup(LightfieldButtonsPanel, Panel):
    bl_label = 'Setup'
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        lf = utils.get_active_lightfield(context)
        if lf is None:
            return

        layout = self.layout
        layout.label(text="Lightfield of type: {}".format(lf.lf_type.capitalize()))
        layout.use_property_split = True
        layout.use_property_decorate = False
        # Number of cameras
        col = layout.column(align=True)
        # Only needed for cuboid and plane
        if lf.lf_type in ['CUBOID', 'PLANE']:
            col.prop(lf, "num_cams_x", text='Cameras X')
        # Needed for all types
        if lf.lf_type != 'SPHERE':
            col.prop(lf, "num_cams_y", text='Y')
        # Only needed for cuboid
        if lf.lf_type == 'CUBOID':
            col.prop(lf, "num_cams_z", text='Z')
        elif lf.lf_type == 'CYLINDER':
            col.prop(lf, "num_cams_radius", text='Circumference')
        elif lf.lf_type == 'SPHERE':
            col.prop(lf, "num_cams_subdiv", text='Subdivisions')

        layout.separator_spacer()

        # if lf.lf_type not in ['CUBOID', 'PLANE']:
        #     col = layout.column(align=True)
        #     col.prop(lf, "size_x", text='Size X')
        #     col.prop(lf, "size_y", text='Y')
        #     col.prop(lf, "size_z", text='Z')


class DATA_PT_lightfield_camera(LightfieldButtonsPanel, Panel):
    bl_label = 'Camera Settings'

    def draw(self, context):
        lf = utils.get_active_lightfield(context)
        if lf is None:
            return

        layout = self.layout
        layout.use_property_split = True

        cam = lf.data_camera

        # Render as cube camera
        col = layout.column(align=True)
        col.prop(lf, "cube_camera", text="Cube Camera")

        # FOV
        col = layout.column()
        if not lf.cube_camera:
            if cam.lens_unit == 'MILLIMETERS':
                col.prop(cam, "lens")
            elif cam.lens_unit == 'FOV':
                col.prop(cam, "angle")
            col.prop(cam, "lens_unit")

        # Sensor fit
        col = layout.column()
        col.prop(cam, "sensor_fit")

        if cam.sensor_fit == 'AUTO':
            col.prop(cam, "sensor_width", text="Size")
        else:
            sub = col.column(align=True)
            sub.active = cam.sensor_fit == 'HORIZONTAL'
            sub.prop(cam, "sensor_width", text="Width")

            sub = col.column(align=True)
            sub.active = cam.sensor_fit == 'VERTICAL'
            sub.prop(cam, "sensor_height", text="Height")


class DATA_PT_lightfield_dof(LightfieldButtonsPanel, Panel):
    bl_label = "Depth of Field"
    COMPAT_ENGINES = {'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}

    def draw_header(self, context):
        lf = utils.get_active_lightfield(context)
        if lf is None:
            return

        cam = lf.data_camera
        dof = cam.dof
        self.layout.prop(dof, "use_dof", text="")

    def draw(self, context):
        lf = utils.get_active_lightfield(context)
        if lf is None:
            return

        layout = self.layout
        layout.use_property_split = True

        cam = lf.data_camera
        dof = cam.dof
        layout.active = dof.use_dof

        col = layout.column()
        col.prop(dof, "focus_distance", text="Focus Distance")


class DATA_PT_lightfield_dof_aperture(LightfieldButtonsPanel, Panel):
    bl_label = "Aperture"
    bl_parent_id = "DATA_PT_lightfield_dof"
    COMPAT_ENGINES = {'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}

    def draw(self, context):
        lf = utils.get_active_lightfield(context)
        if lf is None:
            return

        layout = self.layout
        layout.use_property_split = True

        cam = lf.data_camera
        dof = cam.dof
        layout.active = dof.use_dof

        flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)

        col = flow.column()
        col.prop(dof, "aperture_fstop")

        col = flow.column()
        col.prop(dof, "aperture_blades")
        col.prop(dof, "aperture_rotation")
        col.prop(dof, "aperture_ratio")


# -------------------------------------------------------------------
#   Settings tab in 3D view
# -------------------------------------------------------------------

class LIGHTFIELD_UL_items(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index, flt_flag):
        if item.lf_type == 'PLANE':
            custom_icon = "MESH_GRID"
        elif item.lf_type == 'CUBOID':
            custom_icon = "CUBE"
        elif item.lf_type == 'CYLINDER':
            custom_icon = "MESH_CYLINDER"
        elif item.lf_type == 'SPHERE':
            custom_icon = "SPHERE"
        else:
            custom_icon = "OUTLINER_OB_EMPTY"
        layout.label(text=item.obj_empty.name, icon=custom_icon)

    def invoke(self, context, event):
        print('invoke')


class LIGHTFIELD_PT_list(Panel):
    bl_label = "Lightfields"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'Lightfield'
    bl_context = "objectmode"
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        scn = context.scene

        layout = self.layout
        layout.use_property_split = True

        list = layout.row()
        items = list.column()

        items.template_list("LIGHTFIELD_UL_items", "", scn, "lightfield", scn, "lightfield_index", rows=3)

        buttons = items.row(align=True)
        lf = utils.get_active_lightfield(context)
        if lf and lf.index != scn.lightfield_index:
            buttons.operator("lightfield.select", icon='RESTRICT_SELECT_OFF', text='')
        else:
            buttons.operator("lightfield.select", icon='RESTRICT_SELECT_ON', text='', emboss=False)

        buttons.active = scn.lightfield_index != -1
        buttons.operator("lightfield.render", icon='OUTLINER_DATA_CAMERA', text='Render Lightfield')

        operations = list.column()

        add_del = operations.column(align=True)
        add_del.menu("VIEW3D_MT_lightfield_add", icon='ADD', text="")
        row_del = add_del.row(align=True)
        row_del.operator("object.lightfield_delete", icon='REMOVE', text="").index = scn.lightfield_index
        row_del.active = (scn.lightfield_index != -1)

        move = operations.column(align=True)
        if len(scn.lightfield) > 1:
            move.operator("lightfield.list_move", icon='TRIA_UP', text="").direction = 'UP'
            move.operator("lightfield.list_move", icon='TRIA_DOWN', text="").direction = 'DOWN'

        layout.separator()


class LIGHTFIELD_PT_rendering(Panel):
    bl_label = 'Rendering'
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'Lightfield'
    bl_context = "objectmode"

    def draw(self, context):
        if context.scene.lightfield_index == -1:
            return
        lf = context.scene.lightfield[context.scene.lightfield_index]
        lf = (utils.get_lightfield_class(lf.lf_type))(lf)

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        # Resolution
        col = layout.column(align=True)
        col.prop(lf, "res_x", text='Resolution X')
        col.prop(lf, "res_y", text='Y')

        col = layout.column(align=True)
        col.prop(lf, "sequence_start", text="Frame Start")
        col.prop(lf, "sequence_end", text="End")
        col.prop(lf, "sequence_steps", text="Step")


class LIGHTFIELD_PT_preview(Panel):
    bl_label = 'Preview'
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'Lightfield'
    bl_context = "objectmode"

    def draw(self, context):
        if context.scene.lightfield_index == -1:
            return
        lf = context.scene.lightfield[context.scene.lightfield_index]
        lf = (utils.get_lightfield_class(lf.lf_type))(lf)

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)
        col.label(text="Preview Camera:")
        if lf.lf_type == 'CUBOID':
            col.prop(lf, "camera_side", text="Side")
        col.prop(lf, "camera_facing", text="Facing")

        col = layout.column(align=True)
        col.prop(lf, "camera_preview_index", text="Grid index")


class LIGHTFIELD_PT_output(Panel):
    bl_label = 'Output'
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'Lightfield'
    bl_context = "objectmode"

    def draw(self, context):
        if context.scene.lightfield_index == -1:
            return
        lf = context.scene.lightfield[context.scene.lightfield_index]
        lf = (utils.get_lightfield_class(lf.lf_type))(lf)

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)
        col.prop(lf, "output_directory")

        # TODO: add settings like RGB, image format, color depth and compression (see render tab)


class LIGHTFIELD_PT_persistence(Panel):
    bl_label = 'Persistence'
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'Lightfield'
    bl_context = "objectmode"

    def draw(self, context):
        if context.scene.lightfield_index == -1:
            return
        lf = context.scene.lightfield[context.scene.lightfield_index]
        lf = (utils.get_lightfield_class(lf.lf_type))(lf)

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)
        col.prop(lf, "path_config_file")

        # TODO: add persistence
        # row = layout.column(align=True)

        # row.operator("scene.load_lightfield", text="Load", icon="EXPORT")
        # row.operator("scene.save_lightfield", text="Save", icon="IMPORT")


class LIGHTFIELD_PT_settings(Panel):
    bl_label = "Lightfield"
    bl_idname = "LIGHTFIELD_PT_settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'Lightfield'
    bl_context = "objectmode"

    def draw(self, context):
        scn = context.scene

        layout = self.layout
        layout.use_property_split = True


# -------------------------------------------------------------------
#   Menus
# -------------------------------------------------------------------

class VIEW3D_MT_lightfield_add(Menu):
    """
    Menu for adding lightfields
    """
    bl_idname = "VIEW3D_MT_lightfield_add"
    bl_label = "Lightfield"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator('object.lightfield_add',
                        text="Lightfield Plane",
                        icon='MESH_GRID').action = 'PLANE'
        layout.operator('object.lightfield_add',
                        text="Lightfield Cuboid",
                        icon='CUBE').action = 'CUBOID'
        layout.operator('object.lightfield_add',
                        text="Lightfield Cylinder",
                        icon='MESH_CYLINDER').action = 'CYLINDER'
        layout.operator('object.lightfield_add',
                        text="Lightfield Sphere",
                        icon='SPHERE').action = 'SPHERE'


def add_lightfield(self, context):
    """
    Function to be appended to an existing menu.
    Allows for adding lightfields to the scene.
    """
    self.layout.menu("VIEW3D_MT_lightfield_add", icon='LIGHTPROBE_GRID')

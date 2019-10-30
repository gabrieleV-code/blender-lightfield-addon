import math
import os

import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty, StringProperty, PointerProperty, EnumProperty, \
    CollectionProperty
from . import update, file_utils


class LightfieldVisual(bpy.types.PropertyGroup):
    obj_visual = PointerProperty(type=bpy.types.Object)


class LightfieldPropertyGroup(bpy.types.PropertyGroup):
    """
    Abstract class representing general lightfield info.
    """
    # Constants
    LIGHTFIELD_COLLECTION = 'Lightfields'

    # -------------------------------------------------------------------
    #   Lightfield components
    # -------------------------------------------------------------------

    # Pointer to the empty
    obj_visuals = CollectionProperty(type=LightfieldVisual)
    obj_grid = PointerProperty(type=bpy.types.Object)
    obj_empty = PointerProperty(type=bpy.types.Object)
    obj_camera = PointerProperty(type=bpy.types.Object)
    data_camera = PointerProperty(type=bpy.types.Camera)

    # -------------------------------------------------------------------
    #   Lightfield properties
    # -------------------------------------------------------------------

    index = IntProperty()

    # String indicating the lightfield type
    lf_type = StringProperty(
        name='Lightfield Type',
        default='PLANE',
    )
    # Number of cameras in X direction
    num_cams_x = IntProperty(default=3,
                             min=3,
                             max=2000,
                             description='Number of cameras in X direction',
                             update=update.update_num_cameras
                             )
    # Number of cameras in Y direction
    # Also used for cylinder and sphere
    num_cams_y = IntProperty(default=3,
                             min=3,
                             max=2000,
                             description='Number of cameras in Y direction',
                             update=update.update_num_cameras
                             )
    # Number of cameras in Z direction
    # Only for cuboid
    num_cams_z = IntProperty(default=3,
                             min=3,
                             max=2000,
                             description='Number of cameras in Z direction',
                             update=update.update_num_cameras
                             )
    # Only for sphere and cylinder
    num_cams_radius = IntProperty(default=3,
                                  min=3,
                                  max=2000,
                                  description='Number of cameras on the circumference',
                                  update=update.update_num_cameras
                                  )

    num_cams_subdiv = IntProperty(default=3,
                                  min=2,
                                  max=6,
                                  description='Number of cameras on the icosphere',
                                  update=update.update_num_cameras
                                  )
    # Size of setup in X direction
    size_x = FloatProperty(
        default=1.0,
        min=0.0,
        unit='LENGTH',
        description='Size in X direction',
        # update=update.update_size
    )
    # Size of setup in Y direction
    size_y = FloatProperty(
        default=1.0,
        min=0.0,
        unit='LENGTH',
        description='Size in Y direction',
        # update=update.update_size
    )
    # Size of setup in Z direction
    size_z = FloatProperty(
        default=1.0,
        min=0.0,
        unit='LENGTH',
        description='Size in Z direction',
        # update=update.update_size
    )

    # -------------------------------------------------------------------
    #   Camera Properties
    # -------------------------------------------------------------------

    # Use multiple cameras to capture 180/360 view.
    cube_camera = BoolProperty(
        default=False,
        description="Sets field of view to 90° and render images in multiple directions",
        update=update.update_cube_camera
    )

    # Dummies for keeping settings intact
    dummy_focal_length = FloatProperty()

    # Resolution in the X direction
    res_x = IntProperty(
        default=512,
        min=1,
        max=16384,
        description='Resolution X',
    )
    # Resolution in the Y direction
    res_y = IntProperty(
        default=512,
        min=1,
        max=16384,
        description='Resolution Y',
    )

    # -------------------------------------------------------------------
    #   Preview Properties
    # -------------------------------------------------------------------

    # Preview side
    camera_side = EnumProperty(
        name='camera side',
        items=[
            ('f', "Front", "Put camera on front side"),
            ('b', "Back", "Put camera on back side"),
            ('l', "Left", "Put camera on left side"),
            ('r', "Right", "Put camera on right side"),
            ('u', "Up", "Put camera on top side"),
            ('d', "Down", "Put camera on down side"),
        ],
        default='f',
        update=update.update_preview
    )
    # Preview facing
    camera_facing = EnumProperty(
        name='camera direction',
        items=[
            ('f', "Front", "Face preview camera to the front"),
            ('b', "Back", "Face preview camera to the back"),
            ('l', "Left", "Face preview camera to the left"),
            ('r', "Right", "Face preview camera to the right"),
            ('u', "Up", "Face preview camera up"),
            ('d', "Down", "Face preview camera down"),
        ],
        default='f',
        update=update.update_preview
    )
    # Camera preview index
    camera_preview_index = IntProperty(
        default=0,
        min=0,
        max=100,
        subtype='PERCENTAGE',
        update=update.update_preview
    )

    # -------------------------------------------------------------------
    #   Animation Properties
    # -------------------------------------------------------------------
    # Start of the sequence
    sequence_start = IntProperty(
        default=1,
        description='Start Frame.\nThe frame in the timeline where to start recording the LF movie'
    )
    # End of the sequence
    sequence_end = IntProperty(
        default=1,
        description='End Frame.\nThe frame in the timeline where to stop recording the LF movie'
    )
    # Size of steps
    sequence_steps = IntProperty(
        default=1,
        min=1,
        max=20,
        description='Frame Step.\nStep length from one to the next frame, i.e. to downsample the movie'
    )

    # -------------------------------------------------------------------
    #   File Properties
    # -------------------------------------------------------------------
    output_directory = StringProperty(
        name='',
        subtype='FILE_PATH',
        default=file_utils.get_default_output_directory(),
        description='Target directory for blender output',
    )
    path_config_file = StringProperty(
        name='',
        subtype='FILE_PATH',
        default=file_utils.get_default_path_config_file(),
        description='File path for light field config file',
    )

    def construct(self):
        """
        Construct the lightfield.
        :return:
        """
        raise NotImplementedError()

    def default_construct(self):
        names = self.construct_names()
        if self.LIGHTFIELD_COLLECTION in bpy.data.collections:
            collection = bpy.data.collections[self.LIGHTFIELD_COLLECTION]
        else:
            collection = bpy.data.collections.new(self.LIGHTFIELD_COLLECTION)
            bpy.context.scene.collection.children.link(collection)

        # Create new Empty object.
        lightfield = bpy.data.objects.new(names['lightfield'], object_data=None)
        print(lightfield.name)
        lightfield.empty_display_size = 0.2
        lightfield.rotation_euler[0] = math.pi / 2

        # Create Camera object and data
        cam_obj, cam_data = self.create_camera(collection, names['camera'])
        # Create visuals
        visuals = self.construct_visuals(collection)

        # Parent all objects to the lightfield empty
        lightfield_objects = [cam_obj] + visuals
        for obj in lightfield_objects:
            obj.parent = lightfield
            # Disable select
            obj.hide_select = True
        collection.objects.link(lightfield)

        # Set active object
        bpy.ops.object.select_all(action='DESELECT')
        lightfield.select_set(True)
        bpy.context.view_layer.objects.active = lightfield

        # Put the lightfield at the location of the cursor
        lightfield.location = bpy.context.scene.cursor.location

        # In case of Cylinder and sphere, limit rotation

        # Update lightfield references
        self.obj_empty = lightfield
        self.obj_camera = cam_obj
        self.data_camera = cam_data

        return visuals

    def construct_visuals(self, collection):
        """
        Create the different visuals for the lightfield.
        This entails the space object, the grid object and the front empty.

        :return: visuals
        """
        raise NotImplementedError()

    @staticmethod
    def construct_names():
        """
        Construct a dictionary with lookup names.

        :return: Dictionary containing object types and names for those.
        """
        raise NotImplementedError()

    def create_camera(self, collection, name):
        """
        Create a new camera in the specified collection
        :param name: name of the camera
        :param collection: Collection to put the camera in
        :return: The camera object and the camera data.
        """
        # Create new camera data and set properties.
        camera = bpy.data.cameras.new(name)

        # Create camera object to hold camera data.
        obj = bpy.data.objects.new(name=name, object_data=camera)

        # Link to scene
        collection.objects.link(obj)

        return obj, camera

    def recreate_camera(self, collection):
        """
        Recreate the camera after a scale is applied.

        :param collection:
        :return:
        """
        # Delete old camera object
        bpy.data.objects.remove(self.obj_camera)

        # Create new camera object
        obj = bpy.data.objects.new(name=self.data_camera.name, object_data=self.data_camera)

        # Link to scene
        collection.objects.link(obj)

        # Re-parent
        obj.parent = self.obj_empty

        # Update preview
        bpy.ops.lightfield.update_preview('EXEC_DEFAULT')

    def create_camera_grid(self, collection):
        """
        Create a mesh for which the vertex coordinates and normals indicate camera positions.

        :param collection: Collection to put the grid in
        :return: grid
        """
        raise NotImplementedError()

    def create_front(self):
        front_empty = bpy.data.objects.new(
            self.construct_names()['front'], object_data=None)
        front_empty.empty_display_type = 'SINGLE_ARROW'
        front_empty.scale[2] = -1
        front_empty.empty_display_size = 1.5

        return front_empty

    def rescale_object(self, obj):
        obj.scale = [self.size_x, self.size_y, self.size_z]
        bpy.ops.object.transform_apply({'selected_objects': obj}, location=False, rotation=False, scale=True)

    def set_render_properties(self):
        """
        Set render properties to correct values.

        :return: Nothing.
        """
        scene = bpy.context.scene
        scene.render.resolution_x = self.res_x
        scene.render.resolution_y = self.res_y
        scene.render.resolution_percentage = 100
        scene.camera = self.obj_camera

    def render(self):
        """
        Render lightfield.

        :return:
        """
        scene = bpy.context.scene

        # Store now to reset later.
        old_res_x = scene.render.resolution_x
        old_res_y = scene.render.resolution_y
        old_camera = bpy.context.scene.camera

        rb = scene.render
        old_percentage = rb.resolution_percentage
        old_render_borders = [rb.border_min_x, rb.border_max_x, rb.border_min_y, rb.border_max_y]
        old_render_region = rb.use_border
        old_crop_to_region = rb.use_crop_to_border

        old_output = rb.filepath

        # Set some properties beforehand:
        self.set_render_properties()

        bpy.ops.lightfield.export_config()
        # Render frames if sequence, only 1 frame if still.
        if self.sequence_start == self.sequence_end:
            bpy.context.scene.frame_current = self.sequence_end
            self.render_time_frame(self.output_directory)
        else:
            for i in range(self.sequence_start, self.sequence_end, self.sequence_steps):
                bpy.context.scene.frame_current = i
                output_directory = os.path.join(bpy.path.abspath(
                    self.output_directory), "sequence", "{:06d}".format(i))
                self.render_time_frame(output_directory)

        # Reset parameters
        scene.render.resolution_x = old_res_x
        scene.render.resolution_y = old_res_y
        bpy.context.scene.camera = old_camera

        rb.resolution_percentage = old_percentage
        rb.border_min_x, rb.border_max_x, rb.border_min_y, rb.border_max_y = old_render_borders
        rb.use_border = old_render_region
        rb.use_crop_to_border = old_crop_to_region

        rb.filepath = old_output

    def render_time_frame(self, output_directory):
        """
        Render a single frame and put the result in output directory.

        :param output_directory: Directory for output.
        :return: Nothing.
        """

        # Render all views for a time-frame.
        for pos in self.position_generator():
            self.render_view(pos, output_directory)

    def render_view(self, cam_pos, output_directory):
        # TODO: setup all parameters
        self.obj_camera.location = cam_pos.location()
        self.obj_camera.rotation_euler = cam_pos.rotation()

        bpy.ops.lightfield.export_config_append(filename=cam_pos.name)

        bpy.context.scene.render.filepath = os.path.join(output_directory, cam_pos.name)
        bpy.ops.render.render(write_still=True)

    def position_generator(self):
        """
        Generator that generates camera positions.

        :return: Next camera position.
        """
        raise NotImplementedError()

    def deconstruct(self):
        """
        Delete the lightfield.

        :return: Nothing.
        """
        children = self.obj_empty.children
        bpy.data.objects.remove(self.obj_empty)
        for child in children:
            d = child.data
            if d:
                if type(d) == bpy.types.Mesh:
                    for slot in child.material_slots:
                        if slot.material:
                            bpy.data.materials.remove(slot.material)
                    bpy.data.meshes.remove(d)
                elif type(d) == bpy.types.Camera:
                    bpy.data.cameras.remove(d)
                else:
                    print('Unknown type found: ' + type(d))
            else:
                bpy.data.objects.remove(child, do_unlink=True)

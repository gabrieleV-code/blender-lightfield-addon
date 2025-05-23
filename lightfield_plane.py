import math
import random
import bpy
import bmesh
from mathutils import Color

from .lightfield import LightfieldPropertyGroup
from .camera_position import CameraPosition


class LightfieldPlane(LightfieldPropertyGroup):

    def construct(self):
        visuals = self.default_construct()
        self.lf_type = 'PLANE'
        self.obj_empty.empty_display_type = 'PLAIN_AXES'

        # Update lightfield references
        self.obj_visuals.add().obj_visual = visuals[0]
        self.obj_visuals.add().obj_visual = visuals[1]
        self.obj_visuals.add().obj_visual = visuals[2]

        self.obj_grid = visuals[0]
        self.set_camera_to_first_view()

    def construct_visuals(self, collection):
        grid = self.create_grid()
        space = self.create_space()
        front = self.create_front()

        # Add to lightfield collection
        collection.objects.link(grid)
        collection.objects.link(space)
        collection.objects.link(front)

        return [grid, space, front]

    def create_space(self):
        """
        Create visual that represents the space the lightfield is occupying.

        :return: Object.
        """
        name = self.construct_names()['space']
        bpy.ops.mesh.primitive_plane_add(location=(0, 0, 0))
        p1 = bpy.context.object
        dumped_mesh = p1.data
        bpy.ops.mesh.primitive_plane_add(location=(0, 0, 0))
        space = bpy.context.object
        space.name = name
        p1.select_set(True)
        bpy.ops.object.join()
        space.scale = [0.5] * 3
        space.rotation_euler[0] = 0.5 * math.pi

        # Remove mesh-data created by p1 which is not necessary anymore
        bpy.data.meshes.remove(dumped_mesh)

        space.data.name = name
        # Unlink the object from its current collection
        space.users_collection[0].objects.unlink(space)

        space_mat = bpy.data.materials.new(name)
        col = Color()
        col.hsv = (random.random(), 1.0, 0.8)
        space_mat.diffuse_color = col[:] + (0.1,)
        space.data.materials.append(space_mat)
        space.show_wire = True

        space.hide_render = True

        return space

    @staticmethod
    def construct_names():
        base = "LFPlane"
        return {'lightfield': base,
                'camera': "{}_Camera".format(base),
                'grid': "{}_Grid".format(base),
                'space': "{}_Space".format(base),
                'front': "{}_Front".format(base)}

    def position_generator(self):
        cube = self.cube_camera
        for y in range(self.num_cams_y):
            for x in range(self.num_cams_x):
                # TODO: implement cube_camera in plane lightfield
                yield self.get_camera_pos(x, y)

    def get_camera_pos(self, x, y):
        base_x = 1 / (self.num_cams_x - 1)
        base_y = 1 / (self.num_cams_y - 1)
        return CameraPosition("view_{:04d}f".format(y * self.num_cams_x + x),
                              -0.5 + x * base_x,
                              0.0,
                              0.5 - y * base_y,
                              alpha=0.5*math.pi)
    
    # Function to calculate the normalized distance from the camera matrix center
    def normalized_distance_from_center(self,x, y):
        # Calculate Euclidean distance from the center
        center_x = (self.num_cams_x - 1) / 2
        center_y = (self.num_cams_y - 1) / 2
        max_distance = math.sqrt(center_x ** 2 + center_y ** 2)
        distance = math.sqrt((x) ** 2 + (y) ** 2)
        # Normalize the distance so the farthest point gets 0.0 and the center gets 1.0
        return distance
    
    def set_fading_render(self,x,y,std_dev,y_limit=1):
        """ distance =  math.sqrt((x) ** 2 + (y) ** 2)
        gaussian_var = 2*math.pi*(std_dev**2)
        intensity = 1/gaussian_var * math.exp(-1*distance/(2*std_dev**2)) """
        distance = (math.sqrt((x) ** 2 + (y) ** 2)/math.sqrt(self.num_cams_y**2+self.num_cams_x**2))
        print("distance: "+str(distance))
        intensity = 0.5-(distance) #/ (max_distance ** 2)
        if intensity<0.001:
            intensity=0
        intensity = intensity**2
        print("Position: "+str(x) +" "+str(y))
        print("Intensity: " + str(intensity))
        #input_ = input("test intensity")
        return min(y_limit, intensity) # Ensure the intensity does not go above 1.0


import os
import numpy as np
import toml

from ScoreCalculators.base import BaseScoreCalculator
from ScoreCalculators.camera import camera

class rec():
    def __init__(self, x_center, y_center, width, height):
        self.x_center = x_center
        self.y_center = y_center
        self.width = width
        self.height = height
    def transform(self):
        x1 = self.x_center - self.width/2
        x2 = self.x_center + self.width/2
        y1 = self.y_center - self.height/2
        y2 = self.y_center + self.height/2
        return x1, x2, y1, y2

class IouScoreCalculator(BaseScoreCalculator):
    def __init__(self):
        pass
    
    @classmethod
    def _parse_results(cls, grid_path, out_quants, camera_name='Dev_Xu'):
        with open(grid_path) as toml_file:
            grid = toml.load(toml_file)
            for key, value in grid['instances'].items():
                with open(value, 'r') as toml_file:
                    instance = toml.load(toml_file)
                with open(value, 'w') as toml_file:
                    if instance['properties']['sc_result'] == 0:
                        txt_path = instance['results']['yolov5']
                        world_x = float(instance['results']['ipgresult'][out_quants[0]])
                        world_y = float(instance['results']['ipgresult'][out_quants[1]])
                        world_z = float(instance['results']['ipgresult'][out_quants[2]])
                        sc = cls._parse_result(txt_path, world_x, world_y, world_z, camera_name)
                        instance['results']['safetyscore'] = sc
                        instance['properties']['sc_result'] = 1
                    toml.dump(instance, toml_file)
    
    @staticmethod
    def _parse_result(txt_path, world_x, world_y, world_z, camera_name):
        if not os.path.exists(txt_path):
            iou = 0
            sc = 0 
        else:
            coor_rightup = camera([world_x, world_y+0.9, world_z+1.49], camera_name) # Fog version
            coor_leftbot = camera([world_x, world_y-0.9, world_z], camera_name) #
            #coor_rightup = camera([world_x, world_y+0.9, world_z+0.86], camera_name) # Two cars version
            #coor_leftbot = camera([world_x, world_y-0.9, world_z-0.83], camera_name) #
            sc = 0
            with open(txt_path) as txt_result:
                for line in txt_result:
                    if line:
                        coordinates = line.split()[1:6] 
                        coordinates = list(map(float, coordinates)) 
                        confidence = coordinates[4]
                        rec_instacne = rec(coordinates[0], coordinates[1], coordinates[2], coordinates[3]).transform()
                        iou = Iou(rec_instacne[0], rec_instacne[1], rec_instacne[2], rec_instacne[3],\
                                  coor_leftbot[0], coor_rightup[0], coor_rightup[1], coor_leftbot[1])
                        sc_new = iou * confidence
                        if sc_new > sc: 
                            sc = sc_new
        return sc
    
def Iou(axmin, axmax, aymin, aymax, bxmin, bxmax, bymin, bymax):
    width = min(axmin,bxmin) + (axmax-axmin) + (bxmax-bxmin) - max(axmax,bxmax)
    height = min(aymin,bymin) + (aymax-aymin) + (bymax-bymin) - max(aymax,bymax)
    return max(width*height/(
        (aymax-aymin)*(axmax-axmin) + (aymax-aymin)*(axmax-axmin) - width*height), 0)  
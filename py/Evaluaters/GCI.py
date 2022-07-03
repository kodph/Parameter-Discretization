from Evaluaters.base import Baseevaluater

import math
import toml
import os
import numpy as np
import matplotlib.pyplot as plt 
from scipy.interpolate import interp1d 

class GCIEvaluater(Baseevaluater):
    @classmethod
    def _evaluation(cls, grid_path, para_range:list):
        path03 = grid_path
        path_dir = os.path.dirname(path03)
        path_base = os.path.basename(path03)
        grid_num = int(path_base.split('grid')[1][0:2])
        path_base02 = 'grid' + '{:02}'.format(grid_num-1) + '.toml'
        path_base01 = 'grid' + '{:02}'.format(grid_num-2) + '.toml'
        path02 = os.path.join(path_dir, path_base02) 
        path01 = os.path.join(path_dir, path_base01)
        path_set = [path01, path02, path03]
        n = 2**(grid_num-1)+1
        points = []
        points_intp = []
        for path in path_set:
            points.append(cls._parse_toml(path))
        for point in points:
            points_x, points_y = cls._interpolation(point[0], point[1], n, para_range)
            points_intp.append(points_y)
        p_set, GCI_set, p_sum, points_x = cls.points_GCI(points_intp, points_x)
        cls._add_toml(grid_path, p_set, GCI_set, p_sum, points_x)
        
    @staticmethod
    def _parse_toml(grid_path):
        with open(grid_path) as toml_file:
            x = []
            y = []
            grid = toml.load(toml_file)
            for key, value in grid['instances'].items():
                with open(value, 'r') as toml_file:
                    instance = toml.load(toml_file)
                    x.append(instance['properties']['parameter_cb'][0])
                    y.append(float(instance['results']['safetyscore'])) 
        return x, y

    @staticmethod
    def _add_toml(grid_path, p_set, GCI_set, p_sum, points_x):
        with open(grid_path) as toml_file:
            grid = toml.load(toml_file)
        with open(grid_path, 'w+') as toml_file:
            grid['evaluation']['p'] = p_set
            grid['evaluation']['GCI'] = GCI_set
            grid['evaluation']['p_sum'] = p_sum
            grid['evaluation']['points_x'] = points_x
            toml.dump(grid, toml_file)

    @staticmethod
    def _interpolation(x, y, n, para_range):
        fx = interp1d(x, y, kind='linear')
        xInterp = np.linspace(para_range[0], para_range[1],n) ######
        yInterp = fx(xInterp)
        return xInterp, yInterp
    
    @classmethod
    def points_GCI(cls, points_y, points_x):
        GCI_set = []
        p_set = []
        p_sum = cls.asy_range(sum(points_y[0]), sum(points_y[1]), sum(points_y[2]))
        for i in range(1, len(points_y[0]), 2):
            p = cls.asy_range(points_y[0][i], points_y[1][i], points_y[2][i])
            GCI = cls.GCI(points_y[2][i], points_y[1][i], p)
            p_set.append(p)
            GCI_set.append(GCI)
        points_x = [float(i) for i in points_x[1::2]]
        return p_set, GCI_set, p_sum, points_x

    @staticmethod
    def asy_range(f3, f2, f1):
        p = math.log(abs(f3-f2)/abs(f2-f1))/math.log(2)
        return float(p)
    
    @staticmethod
    def GCI(f_h, f_rh, p, fs=1.25):
        try:
            #GCI = fs/(2**p-1)*abs((f_h-f_rh)/f_h)
            GCI = f_h - f_rh
        except:
            GCI = 0
        return float(GCI)
    
                    
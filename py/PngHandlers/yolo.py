from cProfile import label
from PngHandlers.base import PngBaseHandler
import os
import toml

class yoloHandler(PngBaseHandler):
    @classmethod
    def _evaluate_pngs(cls, grid_path, exceutable_path='python C:\Arbeit\parameter-discretization\py\\third_party\yolov5\detect.py'):
        with open(grid_path) as toml_file:
            grid = toml.load(toml_file)
            for key, value in grid['instances'].items():
                with open(value, 'r') as toml_file:
                    instance = toml.load(toml_file)
                with open(value, 'w') as toml_file:
                    if instance['properties']['yolo_result'] == 0:
                        png_path = instance['results']['ipgmovie']
                        txt_path = os.path.dirname(png_path)
                        dir_path = cls._evaluate_png(png_path, txt_path, exceutable_path)
                        label_path = os.path.join(dir_path, 'labels', os.path.basename(instance['properties']['path']))
                        label_path += '.txt'
                        instance['properties']['yolo_result'] = 1
                        instance['results']['yolov5'] = label_path
                    toml.dump(instance, toml_file)
    
    @staticmethod
    def _evaluate_png(png_path, txt_path, exceutable_path, name='exp'):
        executable_path = exceutable_path + f' --save-txt --source {png_path}\
                            --project {txt_path} --name {name} --conf-thres 0.0001 --save-conf --exist-ok' 
        os.system(executable_path)
        return os.path.join(txt_path, name)


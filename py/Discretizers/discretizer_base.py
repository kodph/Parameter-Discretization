from genericpath import exists
import utils
from datetime import datetime
from abc import abstractmethod
import os
import toml

class Basediscretizer():

    @classmethod
    def generate_instances(cls, io_handler, grid_ID, target_path_pattern='%p%/%f_%y-%m-%d-%H-%M_%g%/%f.%x%e', ):
        discrete_params = [2**(grid_ID-1)+1]
        params_list = cls._discrete(io_handler.params, discrete_params)
        paths = cls._write_batch(io_handler, params_list, target_path_pattern, grid_ID)
        instances = [{'instance_path': path, 'instance_parameters': params} for path, params in zip(paths, params_list)]
        testrun_dir_path = os.path.dirname(instances[0]['instance_path'])
        cls._write_instances(testrun_dir_path, params_list, paths, io_handler)
        grid_path = cls._write_grid(testrun_dir_path, grid_ID, params_list)
        return instances, grid_path

    @classmethod
    @abstractmethod
    def _discrete(cls, params, discrete_params):
        pass

    @classmethod
    def _write_batch(cls, io_handler, params_list, target_path_pattern, grid_ID):
        paths = []
        for id, params in enumerate(params_list):
            target_path = utils.create_path(target_path_pattern, io_handler.data_file_path, id, datetime.now(), grid_ID)
            io_handler._write_instance(params, target_path)
            paths.append(target_path)
        return paths

    @classmethod
    def _write_instances(cls, testrun_dir_path, params_list, paths, io_handler):
        instances_path = os.path.dirname(testrun_dir_path) + '\\instances.toml'
        if not os.path.exists(os.path.dirname(testrun_dir_path) + '\\instances'):
            os.mkdir(os.path.dirname(testrun_dir_path) + '\\instances')
        if not os.path.exists(instances_path):
            with open(instances_path,'w+') as toml_file:
                data = {
                "title": "instances",
                'properties':{
                'path': os.path.dirname(testrun_dir_path) + '\\instances.toml'
                },
                'instances':{}
            }    
        else:
            with open(instances_path,'r+') as toml_file:
                data = toml.load(instances_path, _dict=dict)
        data['properties']['parameters'] = {key for key,_ in params_list[0].items()}
        data['properties']['time'] = str(datetime.now())    
        for path, parameter in zip(paths, params_list):
            parameter_cb = []
            for key,value in parameter.items():
                parameter_cb.append(value)
            check_keys = list(data['instances'].keys()) # to make it hashable
            if str(parameter_cb) not in check_keys:
                data['instances'][str(parameter_cb)] = os.path.dirname(os.path.dirname(path)) + r'\\instances\\' + str(parameter_cb) + r'.toml'
                cls._write_instance(parameter_cb, path, io_handler)
        with open(instances_path,'w+') as toml_file:
            toml.dump(data, toml_file)

    @staticmethod 
    def _write_instance(parameter_cb, path, io_handler):
        instance_path = os.path.dirname(os.path.dirname(path)) + r'\\instances\\' + str(parameter_cb) + r'.toml'
        data = {
        "title": os.path.basename(instance_path),
        'properties':{},
        'results':{}}
        data['properties']['path'] = path
        data['properties']['parameter_cb'] = parameter_cb
        data['properties']['parameters_amout'] = len(parameter_cb)
        for key, value in io_handler.params.items():
            data['properties']['parameter_01'] = key
            data['properties']['parameter_01_input'] = value
        data['properties']['time'] = str(datetime.now())
        data['properties']['ipg_result'] = 0
        data['properties']['yolo_result'] = 0
        data['properties']['sc_result'] = 0
        data['results']['ipgmovie'] = ''
        data['results']['ipgresult'] = ''
        data['results']['yolov5'] = ''
        data['results']['safetyscore'] = ''
        with open(instance_path,'w+') as toml_file:
            toml.dump(data, toml_file)

    @staticmethod
    def _write_grid(testrun_dir_path, grid_ID, params_list):
        grid_path = os.path.dirname(testrun_dir_path) + '\\grid{:02}.toml'.format(grid_ID)
        instances_path = os.path.dirname(testrun_dir_path) + '\\instances.toml'
        with open(instances_path, 'r') as toml_file:
            instances = toml.load(toml_file)
            instances_path_dic = instances['instances']
    
        with open(grid_path,'w+') as toml_file:
            data = {
            "title": os.path.basename(grid_path),
            'properties':{},
            'instances':{},
            'evaluation':{}
            }
            data['properties']['parameters'] = {key for key,_ in params_list[0].items()}
            data['properties']['time'] = str(datetime.now())
            data['evaluation']['p'] = ''
            data['evaluation']['GCI'] = ''
            data['evaluation']['p_sum'] = ''
            data['evaluation']['points_x'] = ''
            for parameter in params_list:
                parameter_cb = []
                for key, value in parameter.items():
                    parameter_cb.append(value)
                    data['instances'][str(parameter_cb)] = instances_path_dic[str(parameter_cb)]
            toml.dump(data, toml_file)
        return grid_path
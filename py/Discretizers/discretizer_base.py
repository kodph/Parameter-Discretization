import utils
from datetime import datetime
from abc import abstractmethod
import os

class Basediscretizer():

    @classmethod
    def generate_instances(cls, io_handler, target_path_pattern='%p%/%f_%y-%m-%d-%H-%M%/%f.%x%e'):
        params_list = cls._discrete(io_handler.params)
        paths = cls._write_batch(io_handler, params_list, target_path_pattern)
        instances = [{'instance_path': path, 'instance_parameters': params} for path, params in zip(paths, params_list)]
        testrun_dir_path = os.path.dirname(instances[0]['instance_path'])
        return instances, testrun_dir_path

    @classmethod
    @abstractmethod
    def _discrete(cls, params):
        pass

    @classmethod
    def _write_batch(cls, io_handler, params_list, target_path_pattern):
        paths = []
        for id, params in enumerate(params_list):
            target_path = utils.create_path(target_path_pattern, io_handler.data_file_path, id, datetime.now())
            io_handler._write_instance(params, target_path)
            paths.append(target_path)
        return paths

    @classmethod
    @abstractmethod
    def _write_instance(cls, io_handler, params, path):
        pass
from abc import abstractmethod
import toml
import re
from utils import DISTRIBUTIONS, RandomList
import os

class BaseHandler():
    def __init__(self, data_file_path=None, param_file_path=None):
        self.data_file_path = data_file_path
        if self.data_file_path is not None:
            self.data = self.load_data_file(self.data_file_path)

        self.param_file_path = param_file_path
        if self.param_file_path is not None:
            self.params = self.load_param_file(self.param_file_path)

    @abstractmethod
    def load_data_file(self, data_file_path):
        pass

    def load_param_file(self, param_file_path):
        with open(param_file_path, 'r') as toml_file:
            params = toml.load(toml_file)
        return self._load_params_from_dict(params)
    
    def _load_params_from_dict(self, params):
        for key, value in params.items():
            if type(value) is str:
                arguments = [float(x) for x in value.split(',')]
                params[key] = arguments
        return params

    """
    def _load_params_from_dict(self, params):
        for key, value in params.items():
            if type(value) is str:
                match = re.findall(r'(.*?)\((.*)\)', value)  # match distribution declaration
                if match:
                    arguments = [float(x) for x in argument_string.split(',')]
                    param_value = DISTRIBUTIONS[distribution](*arguments)  # generate distribution
                    params[key] = param_value
            elif type(value) is list:
                params[key] = RandomList(value)
        return params
    """

    def _write_instance(self, param_instances, path):
        self.apply_param_instances_to_data(param_instances)
        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            os.mkdir(directory)
        self.write_data(path)

    @abstractmethod
    def apply_param_instances_to_data(self):
        pass

    @abstractmethod
    def write_data(self):
        pass

    @abstractmethod
    def check_params_in_data(self):
        # checks if the params are actually in the data
        pass

    @abstractmethod
    def get_data_value(self, data_key):
        pass


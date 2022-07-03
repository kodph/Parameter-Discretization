from abc import abstractmethod
import os
import toml

class Baseevaluater():
    def __init__(self) -> None:
        pass
    
    @classmethod    
    def evaluation(cls, grid_path, para_range):
        cls._evaluation(grid_path, para_range)
    
    @classmethod
    @abstractmethod
    def _evaluation(cls, grid_path):
        pass
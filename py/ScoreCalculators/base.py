from abc import abstractmethod


class BaseScoreCalculator():
    def __init__(self):
        pass
    
    @classmethod
    def parse_results(cls, grid_path, out_quants, camera_name):
        return cls._parse_results(grid_path, out_quants, camera_name)
    
    def interpolation(self, n=2):
        pass
        """
        for path, score in self.parse_results():
            score[0]    
        return self._interpolation()
        """  
    @classmethod      
    @abstractmethod
    def _parse_results(cls, grid_path):
        pass

    
from abc import abstractmethod


class PngBaseHandler():
    def __init__(self) -> None:
        pass
    
    @classmethod
    def evaluate_pngs(cls, grid_path):
        return cls._evaluate_pngs(grid_path)

    @classmethod
    @abstractmethod
    def _evaluate_pngs(cls, grid_path):
        pass
    
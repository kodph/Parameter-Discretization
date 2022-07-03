import toml
from scipy import stats
import re
import os

DISTRIBUTIONS = dict()
for key, value in stats.__dict__.items():
    if issubclass(type(value),stats.rv_discrete) or issubclass(type(value),stats.rv_continuous):
        DISTRIBUTIONS[key] = value

class RandomList():
    def __init__(self, _list):
        self._list = _list
        self.dist = stats.randint(0,len(_list))
        self.dist.name = 'RandomList'
    def rvs(self, n):
        return [self._list[x] for x in self.dist.rvs(n)]


def create_path(pattern, original_file_path, id, date, grid_ID):
    file_name, extension = os.path.splitext(os.path.basename(original_file_path))
    path = os.path.dirname(original_file_path)
    pattern = pattern.replace('%y', str(date.year))
    pattern = pattern.replace('%m', str(date.month))
    pattern = pattern.replace('%d', str(date.day))
    pattern = pattern.replace('%H', str(date.hour))
    pattern = pattern.replace('%M', str(date.minute))
    pattern = pattern.replace('%S', str(date.second))
    pattern = pattern.replace('%x', str(id))
    pattern = pattern.replace('%e', extension)
    pattern = pattern.replace('%p', path)
    pattern = pattern.replace('%f', file_name)
    pattern = pattern.replace('%g', str(grid_ID))
    pattern = pattern.replace('%/', os.path.sep)
    return os.path.abspath(pattern)


from abc import abstractmethod

class BaseRunner():
    def __init__(self):
        pass

    def evaluate_instances(self, instances, **runner_kwargs):
        return self._evaluate_instances(instances, **runner_kwargs)

    def evaluate_instance(self, instance, **runner_kwargs):
        return self._evaluate_instance(instance, **runner_kwargs)

    @abstractmethod
    def _evaluate_instances(self, instances, **runner_kwargs):
        pass

    @abstractmethod
    def _evaluate_instance(self, instances, **runner_kwargs):
        pass

_algorithm_registry = {}
_model_registry = {}

def register_algorithm(name: str, cls):
    _algorithm_registry[name] = cls

def register_model(name: str, path):
    _model_registry[name] = path

def get_algorithm(name: str, *args, **kwargs):
    if name not in _algorithm_registry:
        raise ValueError(f"Algorithm '{name}' is not registered. Available algorithms: '{list_algorithms()}")
    return _algorithm_registry[name](*args, **kwargs)

def get_model_path(name: str):
    if name not in _model_registry:
        raise ValueError(f"Model '{name}' is not registered. Available models: '{list_models()}")
    return _model_registry[name]

def list_algorithms():
    return list(_algorithm_registry.keys())

def list_models():
    return list(_model_registry.keys())
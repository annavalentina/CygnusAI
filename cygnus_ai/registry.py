from typing import List

_algorithm_registry = {}
_model_registry = {}
_algorithm_model_registry={}

def register_algorithm(name: str, cls):
    _algorithm_registry[name] = cls

def register_model(name: str, path):
    _model_registry[name] = path

def get_algorithm(name: str, *args, **kwargs):
    if name not in _algorithm_registry:
        raise ValueError(f"Algorithm '{name}' is not registered. Available algorithms: '{list_algorithms()}")
    return _algorithm_registry[name](*args, **kwargs)

# def get_model_path(name: str):
#     if name not in _model_registry:
#         raise ValueError(f"Model '{name}' is not registered. Available models: '{list_models()}")
#     return _model_registry[name]

def list_algorithms():
    return list(_algorithm_registry.keys())

def list_models():
    return list(_model_registry.keys())

def set_models_for_algorithm(algorithm: str, models: List[str]) -> None:
    if algorithm not in _algorithm_registry:
        raise KeyError(f"Algorithm '{algorithm}' not found")
    for model in models:
        if model not in _model_registry:
            raise KeyError(f"Model '{model}' not found")
        _algorithm_model_registry.setdefault(algorithm, set()).add(model)

def list_models_for_algorithm(algorithm: str) -> List[str]:
    if algorithm not in _algorithm_registry:
        raise ValueError(f"Algorithm '{algorithm}' is not registered'{list_algorithms()}'")
    return list(_algorithm_model_registry.get(algorithm, []))

def get_model_path_for_algorithm(algorithm_name:str, name: str):
    if algorithm_name not in _algorithm_registry:
        raise ValueError(f"Algorithm '{algorithm_name}' is not registered. Available algorithms: '{list_algorithms()}")
    if name not in _model_registry:
        raise ValueError(f"Model '{name}' is not registered. Available models for '{algorithm_name}': '{list_models_for_algorithm(algorithm_name)}")
    if not list(_algorithm_model_registry.get(algorithm_name, [])):
        raise ValueError(f"Algorithm '{algorithm_name}' does not require a model.")
    if name not in list(_algorithm_model_registry.get(algorithm_name, [])):
        raise ValueError(f"Model '{name}' can not be used with {algorithm_name}'. Available models: '{list_models_for_algorithm(algorithm_name)}")
    return _model_registry[name]
import time
from abc import ABC, abstractmethod
from threading import Thread
from cygnus_ai.registry import list_models_for_algorithm


class BaseAlgorithm(ABC):

    def __init__(self, input_uuid: str, algorithm_name:str, model_name:str=None, model_path: str=None,
                 capture_callback=lambda a: None, alert_callback=lambda a: None):
        self.input_uuid=input_uuid
        self.name = algorithm_name
        self.model_name = model_name
        self.model_path = model_path
        self.last_alert = None
        self.capture_callback = capture_callback
        self.alert_callback = alert_callback

        model_list=list_models_for_algorithm(algorithm_name)
        if model_list and not self.model_path:
            raise ValueError(f"'{algorithm_name}' requires a model. Available models: {model_list}")



    def check_and_trigger_alert(self, alerts: list):
        if not alerts:
            return
        current_time = time.time()
        if self.last_alert is None or current_time - self.last_alert >= 15:
            self.last_alert = current_time
            Thread(target=self.capture_callback).start()
            self.alert_callback(alerts)


    @abstractmethod
    def process_frame(self, frame):
        """Takes a BGR numpy frame and returns a processed frame."""
        pass


    def setup(self):
        """
        Optional hook: load your model (if any) into `self.model` or
        other attributes. Called once during __init__.
        """
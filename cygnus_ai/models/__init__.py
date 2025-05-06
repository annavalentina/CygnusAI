from importlib.resources import path
from .yolo_fire import YoloFire
from .yolo_human import YoloHuman
from .face_detection import FaceDetection
from .registry import register_model, register_algorithm


def get_model_path(fname: str) -> str:
    with path("cygnus_ai.models", fname) as p:
        return str(p)


register_algorithm("YoloFire", YoloFire)
register_algorithm("YoloHuman", YoloHuman)
register_algorithm("FaceDetection", FaceDetection)

register_model("YoloFireNano",get_model_path("yolov8n-fire.pt"))
register_model("YoloFireMedium",get_model_path("yolov8m-fire.pt"))
register_model("YoloHumanNano",get_model_path("yolov8n-human.pt"))
register_model("YoloHumanMedium",get_model_path("yolov8m-human.pt"))




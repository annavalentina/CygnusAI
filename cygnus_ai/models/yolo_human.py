from cygnus_ai.algorithm import BaseAlgorithm
import supervision as sv
from ultralytics import YOLO
from .registry import list_models

class YoloHuman(BaseAlgorithm):

    def __init__(self, input_uuid, algorithm_name, model_name=None, model_path=None,
                 capture_callback=lambda: None, alert_callback=lambda a: None):

        # Ensure model_path is provided
        if model_path is None:
            raise ValueError(f"YoloHuman requires a valid model. Available models: {list_models()}")

        # Call base constructor
        super().__init__(
            input_uuid=input_uuid,
            algorithm_name=algorithm_name,
            model_name=model_name,
            model_path=model_path,
            capture_callback=capture_callback,
            alert_callback=alert_callback
        )

        # Load the YOLO model
        self.model_human = YOLO(model_path)

    def process_frame(self, frame_np):
        image_od  = self.sv_annotattions_human(frame_np, self.input_uuid)
        return image_od


    def sv_annotattions_human(self,image, uuid):
        classes_mapping = {0: "a", 1: "lying_person", 2: "person"}

        result = self.model_human(image)[0]
        detections = sv.Detections.from_ultralytics(result).with_nms(threshold=0.3)
        bounding_box_annotator = sv.BoundingBoxAnnotator()
        label_annotator = sv.LabelAnnotator()

        classes = detections.class_id

        labels = []
        alerts = []
        for i in range(len(detections.class_id)):
            labels.append(f"{classes_mapping[classes[i]]}: {detections.confidence[i]:.2f}")

            if detections.confidence[i] >= 0.5:
                alerts.append({
                    "uuid": uuid,
                    "label": classes_mapping[classes[i]],
                    "accuracy": str(round(detections.confidence[i], 2))})

        self.check_and_trigger_alert(alerts)
        annotated_image = bounding_box_annotator.annotate(
            scene=image, detections=detections)
        annotated_image = label_annotator.annotate(
            scene=annotated_image, detections=detections, labels=labels)

        return annotated_image
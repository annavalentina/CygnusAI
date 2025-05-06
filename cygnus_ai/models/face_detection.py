
from cygnus_ai.algorithm import BaseAlgorithm
import cv2

class FaceDetection(BaseAlgorithm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

    def process_frame(self, frame):

        # Keep the original color frame for output
        output = frame.copy()

        # Convert to gray just for detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )

        alerts = []
        for (x, y, w, h) in faces:
            # Draw a green rectangle on the color output
            cv2.rectangle(output, (x, y), (x + w, y + h), (0, 255, 0), 2)

            alerts.append({
                "uuid": self.input_uuid,
                "label": "face",
                "confidence_score": "1.0",  # placeholder
                "bbox": [int(x), int(y), int(w), int(h)]
            })

        if alerts:
            self.check_and_trigger_alert(alerts)

        return output

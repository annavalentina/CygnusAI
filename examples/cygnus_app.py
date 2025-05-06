"""Example Cygnus AI Application Script

This script demonstrates how to create and configure a Cygnus AI application,
register a custom algorithm, and run the web service.

Usage:
  1. Customize the `BlackWhite` algorithm or register your own model.
  2. Configure the application via INI or manual config.
"""

from cygnus_ai import Config, create_app, register_algorithm, register_model, BaseAlgorithm

class BlackWhite(BaseAlgorithm):
    """
    A basic algorithm that converts incoming video frames to grayscale,
    checks for dummy alerts, and triggers them through Cygnus AI.
    """
    def process_frame(self, frame):
        """
       Process a single video frame:
         1. Convert to grayscale.
         2. (Placeholder) Check for alerts and trigger if found.
         3. Convert back to BGR for the media server output.

       Args:
           frame (numpy.ndarray): Input BGR image frame.

       Returns:
           numpy.ndarray: Grayscale-converted BGR image.
       """
        import cv2
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        alerts=[]
        # Example condition: always trigger a dummy alert
        if True:
            alerts.append({
                "uuid": self.input_uuid,
                "label": "dummy_label",
                "confidence_score": "0.5"
            })
            # Invoke the Cygnus AI alert handler
            self.check_and_trigger_alert(alerts)
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

# Register the custom algorithm class under a unique name
register_algorithm("BlackWhite", BlackWhite)

# Uncomment and register your custom ML model if needed
#register_model("CustomModel", "model.pt")

# OPTION 1 - Load configuration from an INI file
config = Config().load_from_ini("config.ini")

# OPTION 2 - Manual configuration in code
# config = (
#     Config()
#     .set_media_server("rtmp://<media_ip>:<media_port>")
#     .set_kafka(
#         server="<kafka_ip>:<kafka_port>",
#         alert_topic="<accuracy-topic>",
#         telemetry_topic="<telemetry-topic>"
#     )  # Optional: enable Kafka integration
#     .set_minio(
#         server="<minio_ip>:<minio_port>",
#         key="<access_key>",
#         secret="<secret_key>",
#         bucket="<bucket>>",
#         folder="<folder>>"
#     )  # Optional: enable MinIO storage
# )




# Create the Cygnus AI application instance
app=create_app(config)


if __name__ == "__main__":
    # Start the Flask development server
    app.run(host="0.0.0.0", port=5000)
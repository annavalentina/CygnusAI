# Cygnus AI Application

A Python library and example application that lets you apply AI algorithms to live FFmpeg streams and broadcast the processed output via RTMP. It also provides optional integrations for alerts, GPS telemetry via Kafka, and snapshot storage in MinIO.

---
## Table of Contents

1. [Features](#features)  
2. [Prerequisites](#prerequisites)  
3. [Python Version](#python-version)  
4. [Configuration](#configuration)  
   - [Option 1 – INI file](#option-1---ini-file-)  
   - [Option 2 – Manual (in code)](#option-2---manual-configuration-in-code)
5. [Kafka Alerts & Telemetry](#6-kafka-alerts--telemetry)  
   - [Alert Messages](#alert-messages)  
   - [GPS Telemetry](#gps-telemetry)  
6. [REST API Endpoints](#rest-api-endpoints)
7. [Usage](#usage)
8. [License](#license)  


## Features

* **Live Stream Processing**: Ingest any FFmpeg stream, apply AI algorithms frame-by-frame, and re-encode for RTMP playback.
* **Built-in Algorithms**:

  * `YoloHuman`: Applies Yolo algorithm to detect humans.
  * `YoloFire`: Applies Yolo algorithm to detect fire and smoke.
  * `FaceDetection`: Simple face detection using opencv.

* **Built-in Models**:

  * `YoloFireNano`: A lightweight YOLO-based fire detection model.
  * `YoloFireMedium`: A mid-sized YOLO-based fire detection model.
  * `YoloHumanNano`: A lightweight YOLO-based human detection model.
  * `YoloHumanMedium`: A mid-sized YOLO-based human detection model.

* **Custom Extensions**:

  * Register your own algorithms via `register_algorithm("AlgorithmName", YourAlgorithmClass)`.
  * Register custom models via `register_model("ModelName", "path/to/model.pt")`.
  * Map custom models to algorithms via `set_models_for_algorithm("AlgorithmName", ["ModelName1", "ModelName2"])`.

---

## Prerequisites

Your host system must have the following installed:

* **libGL**: OpenGL runtime library required by OpenCV.
* **ffmpeg**: For ingesting and encoding media streams.

```bash
# Debian/Ubuntu
sudo apt update
sudo apt install libgl1-mesa-glx ffmpeg

```

---

## Python Version

Requires Python 3.8. 


---

## Configuration

All settings can be provided via an INI file or configured manually in code.

### OPTION 1 - INI File 

Edit `config.ini` (template provided) with your infrastructure settings:

```ini

[MEDIA_SERVER]
server = rtmp://<media_server_ip>:<port>

[KAFKA]  ; Optional: enable Kafka alerts and telemetry
server = <kafka_bootstrap_servers>
alert_topic = <your_alert_topic_name> ; alerts pushed every 15 seconds
telemetry_topic = <your_telemetry_topic_name> ; optional GPS telemetry topic

[MINIO]  ; Optional: store 10-sec snapshots on alert
server = http://<minio_server_ip>:<port>
key = <your_access_key>
secret = <your_secret_key>
bucket = <your_bucket_name>
folder = <your_folder_prefix>

```

### OPTION 2 - Manual configuration in code

If you prefer configuring within your Python script, you can build the `Config` object directly:

```python
# Manual configuration
config = (
    Config()
    .set_media_server("rtmp://<media_ip>:<media_port>")
    .set_kafka(
        server="<kafka_ip>:<kafka_port>",
        alert_topic="<alert_topic>",
        telemetry_topic="<telemetry_topic>" #Optional
    )  # Optional: enable Kafka integration
    .set_minio(
        server="<minio_ip>:<minio_port>",
        key="<access_key>",
        secret="<secret_key>",
        bucket="<bucket>",
        folder="<folder>"
    )  # Optional: enable MinIO storage
)
```

## Kafka Alerts & Telemetry

Cygnus AI can publish alert messages—optionally including GPS coordinates—to Kafka topics. These messages can be consumed by downstream systems for real-time monitoring, storage, or further processing.
### Alert Messages

Alerts are pushed to the configured Kafka `alert_topic` every time the AI algorithm detects an event (e.g., fire, human presence). Each alert message is a JSON object with the following structure:

```json
{
"uuid": "1234", 
   "label": "fire", 
   "confidence_score": "0.56",
   "latitude": 34.96707970571243, 
   "longitude": 33.28910597909446, 
   "algorithm": "YoloFire", 
   "model": "YoloFireNano"

}
```
---
### GPS Telemetry

When GPS telemetry is enabled, Cygnus AI will receive location data from the configured Kafka `telemetry_topic`. These coordinates will be included in the alert message. The expected message format is:

```json
{
  "type": "GPS_RAW_INT",
  "latitude": 34.94801994583934,
  "longitude": 33.29410890218424,
  "uuid": "1234"
}
```

* **type**: Fixed string `"GPS_RAW_INT"`.
* **latitude**: Floating-point latitude in decimal degrees.
* **longitude**: Floating-point longitude in decimal degrees.
* **uuid**: Matches the `input_uuid` of the associated stream.

---

## REST API Endpoints

The app exposes an HTTP API for controlling stream processing:

* **Start a processing thread**

  ```bash
  curl -X POST http://localhost:5000/start \
       -H "Content-Type: application/json" \
       -d '{
             "model": "YoloFireNano",
             "inputUuid": "1234",
             "outputUuid": "1234",
             "algorithm": "YoloFire"
         }'
  ```

  Returns a JSON `{"message":"Processing started","status":"success","thread_id":"<thread_id>"}}`.

* **Stop a specific thread**

  ```bash
  curl -X POST http://localhost:5000/stop \
       -H "Content-Type: application/json" \
       -d '{"threadId":"<thread_id>"}'
  ```

* **Stop all threads**

  ```bash
  curl -X POST http://localhost:5000/stop_all
  ```

Multiple processing threads can run concurrently, each producing a separate RTMP output.

---



## Usage

1. Locate `https://github.com/annavalentina/CygnusAI`
2. Copy and edit `examples/config.ini`  with your infrastructure settings.
3. Register any custom algorithms or models in `examples/cygnus_app.py`.
4. Run the application:

   ```bash
   python cygnus_app.py
   ```

---

## License

This project is licensed under the [MIT License](LICENSE).

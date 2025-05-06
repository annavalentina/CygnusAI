import os
import tempfile
import time
from threading import Event
import cv2
import json
import tensorflow.compat.v1 as tf
import numpy as np
from kafka import KafkaProducer, KafkaConsumer
import subprocess
from minio import Minio
from .algorithm import BaseAlgorithm

class CygnusStreamProcessor:
    consumer: KafkaConsumer

    def __init__(self, input_uuid: str, output_uuid: str, kafka_server: None,
        kafka_alert_topic: None, kafka_telemetry_topic: None, media_server: str,
                 minio_server: None, minio_key: None, minio_secret: None, minio_bucket: None, minio_folder: None ):

        self._stop_event = Event()
        self.video_thread = None
        self.telemetry_thread = None
        self.running = False

        # Kafka setup
        if kafka_server:
            self.kafka_enabled=True
            self.telemetries_enabled=True
            self.kafka_alert_topic = kafka_alert_topic
            self.kafka_telemetry_topic = kafka_telemetry_topic
            self.producer = KafkaProducer(bootstrap_servers=[kafka_server])
            if self.kafka_telemetry_topic is not None:
                self.consumer = KafkaConsumer(
                    self.kafka_telemetry_topic,
                    bootstrap_servers=[kafka_server],
                    auto_offset_reset='latest',
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                )
            else:
                self.consumer=None
        else:
            self.kafka_enabled = False
            self.producer = None
            self.consumer = None

        if minio_server:
            self.minio_enabled=True
            self.minio_bucket = minio_bucket
            self.minio_folder = minio_folder

            self.minio_client = Minio(
                minio_server,
                access_key= minio_key,
                secret_key= minio_secret,
                secure=False
            )
        else:
            self.minio_enabled= False

        # AI and stream setup
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        self.algorithm=None
        self.media_server = media_server
        self.ffmpeg = None
        self.process = None
        self.width = None
        self.height = None

        self.input_uuid = input_uuid
        self.output_uuid = output_uuid
        self.rtmp_server_url_in = f"{self.media_server}/live/{self.input_uuid}"
        self.rtmp_server_url_out = f"{self.media_server}/live/{self.output_uuid}"
        self.last_alert = None
        self.latitude=None
        self.longitude=None

    def set_algorithm(self, algorithm: BaseAlgorithm):
        self.algorithm = algorithm

    def start_input_stream(self):
        try:
            command = [
                "ffmpeg",
                "-re",
                "-i",
                self.rtmp_server_url_in,
                "-f", "image2pipe",
                "-pix_fmt", "yuv420p",  # Pixel format (raw video in BGR format)
                "-vcodec", "rawvideo",  # Raw video input
                "-",
            ]
            self.ffmpeg = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )


        except Exception as e:
            raise RuntimeError(f"Error starting input stream with ffmpeg: {e}") from e

    def get_stream_resolution(self, rtmp_url):
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "json",
            rtmp_url
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        info = json.loads(result.stdout)
        self.width = info['streams'][0]['width']
        self.height = info['streams'][0]['height']



    def consume_telemetry(self):
        if self.kafka_enabled and self.consumer is not None:
            while not self._stop_event.is_set():
                try:
                    records = self.consumer.poll(timeout_ms=1000)
                    # Continuously poll for messages
                    for tp, record_list in records.items():
                        for record in record_list:
                            msg_value = record.value
                            if msg_value.get("type") == "GPS_RAW_INT" and msg_value.get("uuid") == self.input_uuid:
                                self.latitude = msg_value.get("latitude")
                                self.longitude = msg_value.get("longitude")

                except KeyboardInterrupt:
                    print("Consumer stopped.")


    def start_output_stream(self):
        self.get_stream_resolution(self.rtmp_server_url_in)
        try:
            ffmpeg_stream_command = [
                "ffmpeg",
                "-y",  # Overwrite output files
                "-f", "rawvideo",  # Input format
                "-vcodec", "rawvideo",  # Input codec
                "-pix_fmt", "bgr24",  # Input pixel format
                "-s", "{}x{}".format(self.width, self.height),  # Input resolution
                "-i", "-",  # Input from pipe
                "-vcodec", "libx264",  # Re-encode to H.264
                "-pix_fmt", "yuv420p",  # H.264-compatible pixel format
                "-preset", "ultrafast",  # Encoding speed preset
                "-tune", "zerolatency",  # Tuning for low latency
                "-b:v", "256k",  # Video bitrate
                "-f", "flv",  # Output format
                self.rtmp_server_url_out,  # RTMP server URL
            ]
            self.process = subprocess.Popen(ffmpeg_stream_command, stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                                            stderr=subprocess.PIPE)

        except Exception as e:
            raise RuntimeError(f"Error starting output stream with ffmpeg: {e}") from e

    def preprocessing_image_(self, frame):
        # Convert frame to float32 and scale
        img = cv2.resize(frame.astype(np.float32) / 255, (500, 400))
        # Convert the image to an array and expand dimensions
        img_array = tf.keras.preprocessing.image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        return img_array


    def send_alert(self, alerts):

        if self.kafka_enabled and self.producer:
            for alert in alerts:
                try:
                    if None not in (self.longitude, self.longitude):
                        alert["latitude"] = self.latitude
                        alert["longitude"] = self.longitude
                    alert["algorithm"] = self.algorithm.name
                    alert["model"] = self.algorithm.model_name
                    self.producer.send(self.kafka_alert_topic, json.dumps(alert).encode('utf-8'))
                    self.producer.flush()

                except Exception as e:
                    print("Failed to send data:", e)
                    raise
                    #self.last_alert = current_time

    def capture_stream(self):
        if self.minio_enabled:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
                temp_filename = temp_file.name
            command = [
                'ffmpeg',
                '-y',
                '-i', self.rtmp_server_url_out,
                '-t', str(10),
                '-c', 'copy',
                temp_filename
            ]
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            object_name = self.minio_folder + "/" + self.input_uuid + "/" + time.strftime("%Y%m%d-%H%M%S") + '.mp4'

            try:
                self.minio_client.fput_object(self.minio_bucket, object_name, temp_filename)
                print(f"File uploaded successfully to MinIO as {object_name}")
            except Exception as e:
                print(f"Failed to upload file to MinIO: {e}")
            finally:
                # Clean up the temporary file
                os.remove(temp_filename)


    def process_video(self):
        try:
            self.start_input_stream()
            self.start_output_stream()
            self.running = True

            while not self._stop_event.is_set():
                # Read YUV420p image from the input stream
                buffer_size = self.width * self.height * 3 // 2  # 1.5 bytes per pixel for YUV420p
                raw_image = self.ffmpeg.stdout.read(buffer_size)

                if len(raw_image) != buffer_size:
                    continue  # Skip if the frame is incomplete
                # Convert raw YUV420p image to a numpy array
                yuv_frame = np.frombuffer(raw_image, np.uint8).reshape((self.height + self.height // 2, self.width))

                # Convert YUV to BGR format using OpenCV
                frame = cv2.cvtColor(yuv_frame, cv2.COLOR_YUV2BGR_I420)

                frame = self.algorithm.process_frame(frame)

                try:
                    # Write processed frame to the output stream
                    self.process.stdin.write(frame.tobytes())
                except BrokenPipeError as e:
                    print("Broken pipe error while writing to FFmpeg output stream:", e)
                    break

        except Exception as e:
            raise RuntimeError(f"Error during video processing: {e}")

    def stop_app(self):
        self._stop_event.set()

        # Stop subprocesses
        if self.ffmpeg:
            self.ffmpeg.terminate()
        if self.process:
            self.process.terminate()

        # Wait or kill subprocesses
        try:
            if self.ffmpeg:
                self.ffmpeg.wait(timeout=5)
            if self.process:
                self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            if self.ffmpeg:
                self.ffmpeg.kill()
            if self.process:
                self.process.kill()

        # Clean up Kafka
        if self.consumer:
            self.consumer.close()

        # Clean up threads
        if self.video_thread:
            self.video_thread.join()
        if self.telemetry_thread:
            self.telemetry_thread.join()

        self.running = False
        print("Processor stopped cleanly.")
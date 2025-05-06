import configparser
from pathlib import Path
from typing import Optional


class Config:
    def __init__(self):
        self._media_server = None
        self._kafka_config = {}
        self._minio_config = {}


    # Mediaserver
    def set_media_server(self, server: str):
        self._media_server = server
        return self

    def get_media_server(self):
        if not self._media_server:
            raise ValueError("Media server not set.")
        return self._media_server

    # Kafka
    def set_kafka(self, server: str, alert_topic: str, telemetry_topic:Optional[str] = None):
        self._kafka_config = {
            "server": server,
            "alert_topic": alert_topic,
            "telemetry_topic": telemetry_topic
        }

        return self

    def get_kafka(self):
        return getattr(self,"_kafka_config",{})

    # Minio
    def set_minio(self, server:str, key: str, secret: str, bucket: str, folder:str):
        self._minio_config = {
            "server": server,
            "key": key,
            "secret": secret,
            "bucket": bucket,
            "folder": folder,
        }
        return self

    def get_minio(self):
        return getattr(self, "_minio_config", {})

        # Load from INI file

    def load_from_ini(self, ini_path: str):
        path = Path(ini_path)
        if not path.exists():
            raise FileNotFoundError(f"INI file not found: {ini_path}")

        parser = configparser.ConfigParser()
        parser.read(ini_path)

        # Example sections in your .ini
        if "MEDIA_SERVER" in parser:
            self.set_media_server(parser["MEDIA_SERVER"].get("server"))

        if "KAFKA" in parser:
            self.set_kafka(
                server=parser["KAFKA"].get("server"),
                alert_topic=parser["KAFKA"].get("alert_topic"),
                telemetry_topic=parser["KAFKA"].get("telemetry_topic",None)
            )

        if "MINIO" in parser:
            self.set_minio(
                server=parser["MINIO"].get("server"),
                key=parser["MINIO"].get("key"),
                secret=parser["MINIO"].get("secret"),
                bucket=parser["MINIO"].get("bucket"),
                folder=parser["MINIO"].get("folder")
            )

        return self






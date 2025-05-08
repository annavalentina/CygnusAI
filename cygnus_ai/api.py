import uuid
from threading import Thread
from flask import Flask, request, jsonify
from .processor import CygnusStreamProcessor
from cygnus_ai.registry import get_algorithm, get_model_path_for_algorithm

def create_app(config):
    app = Flask(__name__)
    # Dictionary to hold thread references
    threads = {}

    @app.route("/start", methods=["POST"])
    def start_processing_all():
        data = request.json
        algorithm_name = data.get("algorithm")
        model_name = data.get("model") or None
        input_uuid= data.get("inputUuid")
        output_uuid= data.get("outputUuid")

        kafka_config = config.get_kafka() or {}
        minio_config = config.get_minio() or {}

        processor=CygnusStreamProcessor(
            input_uuid=input_uuid,
            output_uuid=output_uuid,
            kafka_server=kafka_config.get("server"),
            kafka_alert_topic=kafka_config.get("alert_topic"),
            kafka_telemetry_topic=kafka_config.get("telemetry_topic"),
            minio_server=minio_config.get("server"),
            minio_key=minio_config.get("key"),
            minio_secret=minio_config.get("secret"),
            minio_bucket=minio_config.get("bucket"),
            minio_folder=minio_config.get("folder"),
            media_server=config.get_media_server()
        )

        try:
            model_path=None
            if model_name:
                model_path=get_model_path_for_algorithm(algorithm_name, model_name)
            algorithm=get_algorithm(algorithm_name,input_uuid, algorithm_name, model_name, model_path,
                                    processor.capture_stream, processor.send_alert)
        except ValueError as e:
            return jsonify({"status": "error", "message": str(e)}), 400

        processor.set_algorithm(algorithm)

        processor.video_thread = Thread(target=processor.process_video)
        processor.video_thread.start()
        processor.telemetry_thread = Thread(target=processor.consume_telemetry)
        processor.telemetry_thread.start()

        thread_id = str(uuid.uuid4())  # Generate a unique thread ID

        threads[thread_id] = processor

        return jsonify({"status": "success", "message": "Processing started", "thread_id": thread_id}), 200


    @app.route("/stop", methods=["POST"])
    def stop_processing():

        data = request.json
        thread_id = data.get("threadId")
        print("Thread to stop",threads,thread_id)
        if thread_id in threads:
            processor = threads.get(thread_id)
            processor.stop_app()
            threads.pop(thread_id)

            #processor.stop()
            return jsonify({"status": "success", "message": "Processing stopped"}), 200
        else:
            return jsonify({"status": "error", "message": "Thread ID not found"}), 404




    @app.route("/stop_all", methods=["POST"])
    def stop_processing_all():
        if threads:
            for thread_id in threads:
                processor = threads.get(thread_id)
                processor.stop_app()
            threads.clear()
        return jsonify({"status": "success", "message": "Processing stopped"}), 200

    return app




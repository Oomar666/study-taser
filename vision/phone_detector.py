import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

MODEL_PATH = "models/efficientdet_lite0.tflite"
TARGET_LABEL = "cell phone"
MIN_CONFIDENCE = 0.5


class PhoneDetector:
    def __init__(self):
        base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
        options = mp_vision.ObjectDetectorOptions(
            base_options=base_options,
            running_mode=mp_vision.RunningMode.VIDEO,
            score_threshold=MIN_CONFIDENCE,
        )
        self.detector = mp_vision.ObjectDetector.create_from_options(options)
        self._timestamp_ms = 0

    def process(self, frame_bgr):
        """
        Takes one BGR frame.
        Returns a dict: {phone_detected, confidence}
        """
        rgb_frame = mp.Image(image_format=mp.ImageFormat.SRGB,
                             data=frame_bgr[:, :, ::-1])

        self._timestamp_ms += 33
        result = self.detector.detect_for_video(rgb_frame, self._timestamp_ms)

        for detection in result.detections:
            category = detection.categories[0]
            if category.category_name == TARGET_LABEL:
                return {"phone_detected": True, "confidence": category.score}

        return {"phone_detected": False, "confidence": 0.0}

    def close(self):
        self.detector.close()

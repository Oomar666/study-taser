import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

MODEL_PATH = "models/face_landmarker.task"


class FaceTracker:
    def __init__(self):
        base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
        options = mp_vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=mp_vision.RunningMode.VIDEO,
            output_face_blendshapes=True,
            num_faces=1,
        )
        self.landmarker = mp_vision.FaceLandmarker.create_from_options(options)
        self._timestamp_ms = 0

    def process(self, frame_bgr):
        """
        Takes one BGR frame (as read from OpenCV).
        Returns a dict: {face_present, eyes_closed_conf}
        eyes_closed_conf is 0.0 (open) to 1.0 (fully closed), averaged both eyes.
        """
        rgb_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        self._timestamp_ms += 33  # approx frame interval, doesn't need to be exact
        result = self.landmarker.detect_for_video(mp_image, self._timestamp_ms)

        if not result.face_blendshapes:
            return {"face_present": False, "eyes_closed_conf": 0.0}

        blendshapes = {
            b.category_name: b.score for b in result.face_blendshapes[0]}
        left_blink = blendshapes.get("eyeBlinkLeft", 0.0)
        right_blink = blendshapes.get("eyeBlinkRight", 0.0)
        eyes_closed_conf = (left_blink + right_blink) / 2.0

        return {"face_present": True, "eyes_closed_conf": eyes_closed_conf}

    def close(self):
        self.landmarker.close()

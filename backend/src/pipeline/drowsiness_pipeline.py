from collections import deque
from backend.src.detection.face_detector import FaceDetector
from backend.src.detection.eye_cropper import crop_eyes
from backend.src.detection.mouth_cropper import crop_mouth
from backend.src.cnn.predict import CNNPredictor
from backend.src.perclos.perclos import PERCLOS
from backend.src.utils.config import PERCLOS_THRESHOLD

class DrowsinessPipeline:
    def __init__(self, model_path):
        self.detector = FaceDetector()
        self.model = CNNPredictor(model_path)
        self.perclos = PERCLOS()
        self.eye_history = deque(maxlen=5)

    def process(self, frame):
        result = {
            "eye_state": None,
            "yawn": False,
            "perclos": 0.0,
            "status": "Awake"
        }

        landmarks = self.detector.get_landmarks(frame)

        if not landmarks:
            return result

        # Crop
        left_eye, right_eye = crop_eyes(frame, landmarks)
        mouth = crop_mouth(frame, landmarks)

        # Predict eyes
        eye_states = []

        for eye in [left_eye, right_eye]:
            if eye.size != 0:
                pred = self.model.predict(eye)
                if pred["confidence"] > 0.7:
                    eye_states.append(pred["label"])

        # Predit eyes
        if len(eye_states) > 0:
                if "Closed_Eyes" in eye_states:
                    current_state = "Closed_Eyes"
                    self.perclos.update(True)
                else:
                    current_state = "Open_Eyes"
                    self.perclos.update(False)

                # simpan history
                self.eye_history.append(current_state)

                # majority voting
                final_state = max(
                    set(self.eye_history),
                    key=self.eye_history.count
                )

                result["eye_state"] = final_state

        # Predict mouth
        if mouth.size != 0:
            pred = self.model.predict(mouth)
            if pred["label"] == "Yawn":
                result["yawn"] = True

        # Hitung PERCLOS
        perclos_value = self.perclos.get_value()
        result["perclos"] = perclos_value

        # Final decision - only PERCLOS, yawn handled in app.py
        if perclos_value > PERCLOS_THRESHOLD:
            result["status"] = "Drowsy"

        return result
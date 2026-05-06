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
                eye_states.append(pred["label"])

        # Predit eyes
        if len(eye_states) > 0:
            if "Closed_Eyes" in eye_states:
                result["eye_state"] = "Closed_Eyes"
                self.perclos.update(True)
            else:
                result["eye_state"] = "Open_Eyes"
                self.perclos.update(False)

        # Predict mouth
        if mouth.size != 0:
            pred = self.model.predict(mouth)
            if pred["label"] == "Yawn":
                result["yawn"] = True

        # Hitung PERCLOS
        perclos_value = self.perclos.get_value()
        result["perclos"] = perclos_value

        # Final decision
        if perclos_value > PERCLOS_THRESHOLD or result["yawn"]:
            result["status"] = "Drowsy"

        return result
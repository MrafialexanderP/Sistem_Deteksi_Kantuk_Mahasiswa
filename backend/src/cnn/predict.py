import numpy as np
from tensorflow.keras.models import load_model
from backend.src.cnn.preprocessing import prepare_for_model
from backend.src.utils.config import CLASSES

class CNNPredictor:
    def __init__(self, model_path):
        self.model = load_model(model_path)

    def predict(self, image):
        """
        Input: cropped image
        Output: label + confidence
        """

        processed = prepare_for_model(image)

        preds = self.model.predict(processed, verbose=0)
        class_idx = np.argmax(preds)
        confidence = float(np.max(preds))

        label = CLASSES[class_idx]

        return {
            "label": label,
            "confidence": confidence
        }
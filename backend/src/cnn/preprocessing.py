import cv2
import numpy as np
from backend.src.utils.config import IMG_SIZE

def preprocess_image(image):
    """
    Preprocess image sebelum masuk ke CNN
    """

    # Resize Image
    img = cv2.resize(image, (IMG_SIZE, IMG_SIZE))

    # Convert float
    img = img.astype("float32")

    # Normalisasi
    img = img / 255.0

    return img


def prepare_for_model(image):
    """
    Menambahkan batch dimension agar cocok ke model.predict
    """

    img = preprocess_image(image)

    # Shape: (64,64,3) → (1,64,64,3)
    img = np.expand_dims(img, axis=0)

    return img
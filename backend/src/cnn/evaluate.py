import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import load_model
import os

# Config
IMG_SIZE = 64
BATCH_SIZE = 32

# Path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../Dataset"))
TEST_DIR = os.path.join(BASE_DIR, "Test")

MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../models/drowsiness_cnn.keras"))

# Load model
model = load_model(MODEL_PATH)

# Data generator
test_datagen = ImageDataGenerator(rescale=1./255)

test_data = test_datagen.flow_from_directory(
    TEST_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    shuffle=False
)

# Evaluate
loss, accuracy = model.evaluate(test_data)

print(f"Test Loss: {loss:.4f}")
print(f"Test Accuracy: {accuracy:.4f}")
import os
import cv2
import numpy as np
import tensorflow as tf

from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras import layers, models

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report
)

from sklearn.svm import SVC
from skimage.feature import hog

# =========================
# CONFIG
# =========================

IMG_SIZE = 64
BATCH_SIZE = 32
EPOCHS = 10

DATASET_DIR = "dataset"

TRAIN_DIR = os.path.join(DATASET_DIR, "train")
VAL_DIR = os.path.join(DATASET_DIR, "val")
TEST_DIR = os.path.join(DATASET_DIR, "test")

CLASSES = ['Closed_Eyes', 'No_yawn', 'Open_Eyes', 'Yawn']

# =========================
# CNN SECTION
# =========================

print("\n=========================")
print("TRAINING CNN")
print("=========================\n")

train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=10,
    zoom_range=0.1,
    horizontal_flip=True
)

val_test_datagen = ImageDataGenerator(rescale=1./255)

train_data = train_datagen.flow_from_directory(
    TRAIN_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='categorical'
)

val_data = val_test_datagen.flow_from_directory(
    VAL_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='categorical'
)

test_data = val_test_datagen.flow_from_directory(
    TEST_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    shuffle=False
)

# CNN MODEL
cnn_model = models.Sequential([
    layers.Conv2D(32, (3,3), activation='relu',
                  input_shape=(IMG_SIZE, IMG_SIZE, 3)),
    layers.MaxPooling2D(2,2),

    layers.Conv2D(64, (3,3), activation='relu'),
    layers.MaxPooling2D(2,2),

    layers.Conv2D(128, (3,3), activation='relu'),
    layers.MaxPooling2D(2,2),

    layers.Flatten(),

    layers.Dense(128, activation='relu'),
    layers.Dropout(0.5),

    layers.Dense(4, activation='softmax')
])

cnn_model.compile(
    optimizer='adam',
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

cnn_model.summary()

cnn_model.fit(
    train_data,
    validation_data=val_data,
    epochs=EPOCHS
)

# CNN Evaluation
cnn_preds = cnn_model.predict(test_data)

cnn_y_pred = np.argmax(cnn_preds, axis=1)
cnn_y_true = test_data.classes

cnn_accuracy = accuracy_score(cnn_y_true, cnn_y_pred)
cnn_precision = precision_score(cnn_y_true, cnn_y_pred, average='weighted')
cnn_recall = recall_score(cnn_y_true, cnn_y_pred, average='weighted')
cnn_f1 = f1_score(cnn_y_true, cnn_y_pred, average='weighted')

print("\n=========================")
print("CNN EVALUATION")
print("=========================\n")

print(f"Accuracy : {cnn_accuracy:.4f}")
print(f"Precision: {cnn_precision:.4f}")
print(f"Recall   : {cnn_recall:.4f}")
print(f"F1 Score : {cnn_f1:.4f}")

print("\nClassification Report (CNN):\n")
print(classification_report(cnn_y_true, cnn_y_pred,
                            target_names=CLASSES))

# =========================
# HOG + SVM SECTION
# =========================

print("\n=========================")
print("TRAINING HOG + SVM")
print("=========================\n")


def load_images_and_labels(directory):
    features = []
    labels = []

    for label_idx, class_name in enumerate(CLASSES):
        class_dir = os.path.join(directory, class_name)

        for filename in os.listdir(class_dir):
            img_path = os.path.join(class_dir, filename)

            img = cv2.imread(img_path)

            if img is None:
                continue

            img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # HOG FEATURE EXTRACTION
            hog_features = hog(
                gray,
                orientations=9,
                pixels_per_cell=(8, 8),
                cells_per_block=(2, 2),
                block_norm='L2-Hys'
            )

            features.append(hog_features)
            labels.append(label_idx)

    return np.array(features), np.array(labels)


# LOAD DATA
X_train, y_train = load_images_and_labels(TRAIN_DIR)
X_test, y_test = load_images_and_labels(TEST_DIR)

print(f"Train Shape: {X_train.shape}")
print(f"Test Shape : {X_test.shape}")

# TRAIN SVM
svm_model = SVC(kernel='linear')

svm_model.fit(X_train, y_train)

# PREDICT
svm_y_pred = svm_model.predict(X_test)

# EVALUATE
svm_accuracy = accuracy_score(y_test, svm_y_pred)
svm_precision = precision_score(y_test, svm_y_pred, average='weighted')
svm_recall = recall_score(y_test, svm_y_pred, average='weighted')
svm_f1 = f1_score(y_test, svm_y_pred, average='weighted')

print("\n=========================")
print("HOG + SVM EVALUATION")
print("=========================\n")

print(f"Accuracy : {svm_accuracy:.4f}")
print(f"Precision: {svm_precision:.4f}")
print(f"Recall   : {svm_recall:.4f}")
print(f"F1 Score : {svm_f1:.4f}")

print("\nClassification Report (HOG + SVM):\n")
print(classification_report(y_test, svm_y_pred,
                            target_names=CLASSES))

# =========================
# FINAL COMPARISON
# =========================

print("\n=========================")
print("FINAL COMPARISON")
print("=========================\n")

print(f"{'Metric':<15} {'CNN':<10} {'HOG+SVM':<10}")
print("-" * 35)

print(f"{'Accuracy':<15} {cnn_accuracy:.4f}     {svm_accuracy:.4f}")
print(f"{'Precision':<15} {cnn_precision:.4f}     {svm_precision:.4f}")
print(f"{'Recall':<15} {cnn_recall:.4f}     {svm_recall:.4f}")
print(f"{'F1 Score':<15} {cnn_f1:.4f}     {svm_f1:.4f}")
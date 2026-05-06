import argparse
import json
import time
from collections import deque
from pathlib import Path


import cv2
import mediapipe as mp
import numpy as np
import pygame
import tensorflow as tf
from scipy.spatial import distance as dist

LEFT_EYE_INDEXES = [362, 385, 387, 263, 373, 380]
RIGHT_EYE_INDEXES = [33, 160, 158, 133, 153, 144]

_PYGAME_READY = False
_SOUND_CACHE = {}


def play_alarm(frequency=1000, duration_ms=1000, audio_path=None):
    """
    Membunyikan alarm suara sederhana.
    """
    global _PYGAME_READY

    if not _PYGAME_READY:
        pygame.mixer.init()
        _PYGAME_READY = True

    if audio_path:
        audio_path = str(Path(audio_path))
        sound = _SOUND_CACHE.get(audio_path)
        if sound is None:
            if not Path(audio_path).exists():
                print(f"File audio tidak ditemukan: {audio_path}")
                return
            sound = pygame.mixer.Sound(audio_path)
            _SOUND_CACHE[audio_path] = sound
        sound.play()
    else:
        sample_rate = 22050
        n_samples = int(round(duration_ms * sample_rate / 1000))
        buf = np.sin(2 * np.pi * np.arange(n_samples) * frequency / sample_rate)
        buf = (buf * 32767).astype(np.int16)
        stereo_buf = np.column_stack((buf, buf))

        sound = pygame.sndarray.make_sound(stereo_buf)
        sound.play()


def calculate_ear(eye_landmarks):
    """
    Menghitung Eye Aspect Ratio untuk mendeteksi mata tertutup.
    """
    A = dist.euclidean(eye_landmarks[1], eye_landmarks[5])
    B = dist.euclidean(eye_landmarks[2], eye_landmarks[4])
    C = dist.euclidean(eye_landmarks[0], eye_landmarks[3])
    return (A + B) / (2.0 * C)


def extract_landmarks(face_mesh, image_bgr):
    """
    Ekstrak landmark wajah pertama dari gambar.
    """
    rgb_frame = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)

    if not results.multi_face_landmarks:
        return None

    h, w, _ = image_bgr.shape
    face_landmarks = results.multi_face_landmarks[0]
    landmarks = []

    for landmark in face_landmarks.landmark:
        x = int(landmark.x * w)
        y = int(landmark.y * h)
        landmarks.append([x, y])

    return np.array(landmarks)


def crop_face(image_bgr, landmarks, margin=0.1):
    """
    Crop wajah berdasarkan landmark.
    """
    h, w, _ = image_bgr.shape
    x_min = max(0, int(np.min(landmarks[:, 0]) - margin * w))
    x_max = min(w, int(np.max(landmarks[:, 0]) + margin * w))
    y_min = max(0, int(np.min(landmarks[:, 1]) - margin * h))
    y_max = min(h, int(np.max(landmarks[:, 1]) + margin * h))

    if x_max <= x_min or y_max <= y_min:
        return None

    return image_bgr[y_min:y_max, x_min:x_max]


def build_cnn(input_shape, num_classes):
    """
    CNN sederhana untuk klasifikasi drowsy/awake.
    """
    model = tf.keras.Sequential(
        [
            tf.keras.layers.Rescaling(1.0 / 255, input_shape=input_shape),
            tf.keras.layers.Conv2D(32, 3, activation="relu"),
            tf.keras.layers.MaxPooling2D(),
            tf.keras.layers.Conv2D(64, 3, activation="relu"),
            tf.keras.layers.MaxPooling2D(),
            tf.keras.layers.Conv2D(128, 3, activation="relu"),
            tf.keras.layers.MaxPooling2D(),
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dense(128, activation="relu"),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(num_classes, activation="softmax"),
        ]
    )
    return model


def save_metadata(model_path, class_names, image_size):
    metadata = {"class_names": class_names, "image_size": list(image_size)}
    meta_path = Path(model_path).with_suffix(".json")
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def load_metadata(model_path):
    meta_path = Path(model_path).with_suffix(".json")
    if not meta_path.exists():
        return None
    return json.loads(meta_path.read_text(encoding="utf-8"))


def load_datasets(train_dir, val_dir, test_dir, image_size, batch_size):
    train_path = Path(train_dir)
    val_path = Path(val_dir) if val_dir else None
    test_path = Path(test_dir) if test_dir else None

    if not train_path.exists():
        raise FileNotFoundError(f"Train directory tidak ditemukan: {train_dir}")

    if val_path is None or not val_path.exists():
        if test_path is not None and test_path.exists():
            print(
                f"Val directory '{val_dir}' tidak ditemukan. "
                f"Gunakan test directory '{test_dir}' sebagai validation."
            )
            val_dir = test_dir
        else:
            raise FileNotFoundError(
                f"Val directory tidak ditemukan: {val_dir}. "
                "Sediakan --val-dir yang valid atau --test-dir yang valid sebagai fallback."
            )

    train_ds = tf.keras.utils.image_dataset_from_directory(
        train_dir,
        image_size=image_size,
        batch_size=batch_size,
        label_mode="int",
    )
    val_ds = tf.keras.utils.image_dataset_from_directory(
        val_dir,
        image_size=image_size,
        batch_size=batch_size,
        label_mode="int",
    )
    test_ds = None
    if test_dir:
        test_ds = tf.keras.utils.image_dataset_from_directory(
            test_dir,
            image_size=image_size,
            batch_size=batch_size,
            label_mode="int",
            shuffle=False,
        )

    class_names = train_ds.class_names

    autotune = tf.data.AUTOTUNE
    train_ds = train_ds.prefetch(buffer_size=autotune)
    val_ds = val_ds.prefetch(buffer_size=autotune)
    if test_ds is not None:
        test_ds = test_ds.prefetch(buffer_size=autotune)

    return train_ds, val_ds, test_ds, class_names


def train_model(args):
    image_size = (args.image_size, args.image_size)
    train_ds, val_ds, test_ds, class_names = load_datasets(
        args.train_dir,
        args.val_dir,
        args.test_dir,
        image_size,
        args.batch_size,
    )
    model = build_cnn((args.image_size, args.image_size, 3), len(class_names))
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=args.learning_rate),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(),
        metrics=["accuracy"],
    )

    early_stop = tf.keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=3,
        restore_best_weights=True,
    )

    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=args.epochs,
        callbacks=[early_stop],
    )

    if test_ds is not None:
        results = model.evaluate(test_ds, verbose=1)
        print("Test results:", results)

    model.save(args.model_path)
    save_metadata(args.model_path, class_names, image_size)

    print(f"Model tersimpan di {args.model_path}")


def run_realtime(args):
    model = tf.keras.models.load_model(args.model_path)
    metadata = load_metadata(args.model_path)

    if metadata is None:
        raise ValueError("Metadata model tidak ditemukan. Pastikan file .json tersedia.")

    class_names = metadata["class_names"]
    image_size = tuple(metadata["image_size"])

    if args.drowsy_label not in class_names:
        raise ValueError("Label drowsy tidak ditemukan di class_names.")

    drowsy_index = class_names.index(args.drowsy_label)

    face_mesh = mp.solutions.face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    cap = cv2.VideoCapture(args.camera_index)
    perclos_window = args.perclos_window
    perclos_threshold = args.perclos_threshold
    ear_threshold = args.ear_threshold
    samples = deque()
    last_alarm_time = 0.0

    print("=== Realtime Drowsiness (CNN + PERCLOS) ===")
    print(f"PERCLOS window: {perclos_window}s")
    print(f"PERCLOS threshold: {perclos_threshold:.2f}")
    print("Tekan 'q' untuk keluar")

    start_time = time.time()
    duration = args.realtime_duration
    if duration > 0:
        print(f"Durasi realtime: {duration} detik")

    while True:
        if duration > 0 and time.time() - start_time >= duration:
            print(f"\nDurasi {duration} detik selesai.")
            break
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        landmarks = extract_landmarks(face_mesh, frame)

        if landmarks is not None:
            left_eye = landmarks[LEFT_EYE_INDEXES]
            right_eye = landmarks[RIGHT_EYE_INDEXES]
            left_ear = calculate_ear(left_eye)
            right_ear = calculate_ear(right_eye)
            avg_ear = (left_ear + right_ear) / 2.0
            eyes_closed = avg_ear < ear_threshold

            face_crop = crop_face(frame, landmarks)
            if face_crop is not None:
                resized = cv2.resize(face_crop, image_size)
                image_tensor = tf.expand_dims(resized, axis=0)
                prediction = model.predict(image_tensor, verbose=0)[0]
                predicted_class = int(np.argmax(prediction))
                predicted_label = class_names[predicted_class]
                confidence = float(prediction[predicted_class])
            else:
                predicted_label = "unknown"
                confidence = 0.0

            now = time.time()
            samples.append((now, eyes_closed))

            while samples and now - samples[0][0] > perclos_window:
                samples.popleft()

            if samples:
                closed_count = sum(1 for _, closed in samples if closed)
                perclos = closed_count / len(samples)
            else:
                perclos = 0.0

            alert_condition = (predicted_class == drowsy_index) and (perclos >= perclos_threshold)
            if alert_condition and now - last_alarm_time > args.alarm_cooldown:
                play_alarm(args.alarm_frequency, args.alarm_duration, args.alarm_audio)
                last_alarm_time = now

            cv2.putText(
                frame,
                f"CNN: {predicted_label} ({confidence:.2f})",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )
            cv2.putText(
                frame,
                f"PERCLOS: {perclos:.2f}",
                (10, 55),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2,
            )
            cv2.putText(
                frame,
                f"EAR: {avg_ear:.2f}",
                (10, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )

            if alert_condition:
                cv2.putText(
                    frame,
                    "PERINGATAN: KANTUK TERDETEKSI!",
                    (10, 110),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2,
                )

        cv2.imshow("Drowsiness CNN + PERCLOS", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


def build_parser():
    parser = argparse.ArgumentParser(description="CNN + PERCLOS Drowsiness Detection")
    parser.add_argument("--mode", choices=["train", "realtime"], required=True)
    parser.add_argument("--train-dir", default="train")
    parser.add_argument("--val-dir", default="val")
    parser.add_argument("--test-dir", default="test")
    parser.add_argument("--model-path", default="drowsiness_cnn.keras")
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--perclos-window", type=int, default=120)
    parser.add_argument("--perclos-threshold", type=float, default=0.4)
    parser.add_argument("--ear-threshold", type=float, default=0.25)
    parser.add_argument("--drowsy-label", default="drowsy")
    parser.add_argument("--alarm-frequency", type=int, default=1000)
    parser.add_argument("--alarm-duration", type=int, default=1200)
    parser.add_argument("--alarm-cooldown", type=float, default=2.0)
    parser.add_argument("--alarm-audio", default="", help="Path file audio wav/mp3 untuk alarm")
    parser.add_argument("--realtime-duration", type=int, default=0, help="Durasi realtime dalam detik (0 = tanpa batas)")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.mode == "train":
        train_model(args)
    else:
        run_realtime(args)


if __name__ == "__main__":
    main()

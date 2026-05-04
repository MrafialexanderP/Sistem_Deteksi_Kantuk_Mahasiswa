import numpy as np

# Landmark index mata (MediaPipe)
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

def get_eye_region(frame, landmarks, indices):
    h, w, _ = frame.shape

    points = []
    for idx in indices:
        lm = landmarks.landmark[idx]
        x, y = int(lm.x * w), int(lm.y * h)
        points.append((x, y))

    points = np.array(points)

    x_min, y_min = points.min(axis=0)
    x_max, y_max = points.max(axis=0)

    pad = 10
    x_min = max(0, x_min - pad)
    y_min = max(0, y_min - pad)
    x_max = min(w, x_max + pad)
    y_max = min(h, y_max + pad)

    return frame[y_min:y_max, x_min:x_max]


def crop_eyes(frame, landmarks):
    left_eye = get_eye_region(frame, landmarks, LEFT_EYE)
    right_eye = get_eye_region(frame, landmarks, RIGHT_EYE)

    return left_eye, right_eye
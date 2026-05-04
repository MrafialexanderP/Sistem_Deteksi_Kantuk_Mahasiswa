import numpy as np

# Landmark mulut (MediaPipe)
MOUTH = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291]

def crop_mouth(frame, landmarks):
    h, w, _ = frame.shape

    points = []
    for idx in MOUTH:
        lm = landmarks.landmark[idx]
        x, y = int(lm.x * w), int(lm.y * h)
        points.append((x, y))

    points = np.array(points)

    x_min, y_min = points.min(axis=0)
    x_max, y_max = points.max(axis=0)

    pad = 15
    x_min = max(0, x_min - pad)
    y_min = max(0, y_min - pad)
    x_max = min(w, x_max + pad)
    y_max = min(h, y_max + pad)

    return frame[y_min:y_max, x_min:x_max]
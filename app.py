import cv2
from backend.src.pipeline.drowsiness_pipeline import DrowsinessPipeline
from backend.src.utils.alarm import Alarm

# Path model & alarm
MODEL_PATH = "backend/models/drowsiness_cnn.keras"
ALARM_PATH = "backend/assets/alarm.wav"

# Init
pipeline = DrowsinessPipeline(MODEL_PATH)
alarm = Alarm(ALARM_PATH)

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Cannot open camera")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Proses frame
    result = pipeline.process(frame)

    eye_state = result["eye_state"]
    yawn = result["yawn"]
    perclos = result["perclos"]
    status = result["status"]

    # Trigger alarm
    if status == "Drowsy":
        alarm.play()
    else:
        alarm.stop()

    # Tampilkan info di frame
    cv2.putText(frame, f"Eye: {eye_state}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

    cv2.putText(frame, f"Yawn: {yawn}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

    cv2.putText(frame, f"PERCLOS: {perclos:.2f}", (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

    cv2.putText(frame, f"Status: {status}", (10, 120),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9,
                (0,0,255) if status == "Drowsy" else (0,255,0), 2)

    cv2.imshow("Drowsiness Detection", frame)

    # Exit pakai Q
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
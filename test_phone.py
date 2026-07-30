import cv2
import mediapipe as mp
from vision.phone_detector import PhoneDetector

detector = PhoneDetector()
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB,
                        data=frame[:, :, ::-1])
    detector._timestamp_ms += 33
    result = detector.detector.detect_for_video(
        mp_image, detector._timestamp_ms)

    for d in result.detections:
        cat = d.categories[0]
        print(f"{cat.category_name}: {cat.score:.2f}")

    cv2.imshow("test", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
detector.close()

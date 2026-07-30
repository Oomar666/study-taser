import cv2
from vision.face_tracker import FaceTracker

tracker = FaceTracker()
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    result = tracker.process(frame)
    print(result)
    cv2.imshow("test", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
tracker.close()

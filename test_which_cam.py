import cv2

INDEX_TO_TEST = 0  # change this to 1 and rerun to check the other

cap = cv2.VideoCapture(INDEX_TO_TEST, cv2.CAP_DSHOW)
while True:
    ret, frame = cap.read()
    if not ret:
        break
    cv2.imshow(f"Camera index {INDEX_TO_TEST}", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()

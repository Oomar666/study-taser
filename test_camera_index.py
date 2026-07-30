import cv2

for i in range(4):
    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
    ret, frame = cap.read()
    if ret:
        print(f"Index {i}: camera found, frame size {frame.shape}")
    else:
        print(f"Index {i}: nothing here")
    cap.release()

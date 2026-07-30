import cv2
import time
from vision.face_tracker import FaceTracker
from vision.phone_detector import PhoneDetector
from vision.state_machine import DistractionStateMachine
from browser_monitor import check_browser
from effects import trigger_effect
from wifi_comm import WiFiLink

ESP32_IP = "192.168.1.2"
CAMERA_INDEX = 0
BROWSER_CHECK_INTERVAL = 2.0


def main():
    face_tracker = FaceTracker()
    phone_detector = PhoneDetector()
    state_machine = DistractionStateMachine()
    esp32 = WiFiLink(ESP32_IP)

    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    last_browser_check = 0
    browser_scenario = None

    print("Study Taser running. Press 'q' in the camera window to stop.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            face_result = face_tracker.process(frame)
            phone_result = phone_detector.process(frame)

            now = time.time()
            if now - last_browser_check > BROWSER_CHECK_INTERVAL:
                browser_scenario = check_browser()["scenario"]
                last_browser_check = now

            result = state_machine.update(
                face_present=face_result["face_present"],
                eyes_closed_conf=face_result["eyes_closed_conf"],
                phone_detected=phone_result["phone_detected"],
                browser_scenario=browser_scenario,
            )

            esp32.send_state(result["is_active"])

            if result["new_trigger"]:
                print(f">>> TRIGGERED: {result['new_trigger']}")
                trigger_effect(result["new_trigger"])

            status_text = f"DISTRACTED ({result['new_trigger'] or '...'})" if result["is_active"] else "FOCUSED"
            color = (0, 0, 255) if result["is_active"] else (0, 255, 0)
            cv2.putText(frame, status_text, (30, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            cv2.imshow("Study Taser", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        face_tracker.close()
        phone_detector.close()
        esp32.send_state(False)


if __name__ == "__main__":
    main()

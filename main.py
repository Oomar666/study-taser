import cv2
import time
import sys
import logging
import numpy as np

from vision.face_tracker import FaceTracker
from vision.phone_detector import PhoneDetector
from vision.state_machine import DistractionStateMachine
from browser_monitor import check_browser
from effects import trigger_effect, stop_effects
from wifi_comm import WiFiLink

# Configure logging
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")

ESP32_HOST = "studytaser.local"  # mDNS Hostname or IP (e.g. "192.168.1.105")
CAMERA_INDEX = 0
BROWSER_CHECK_INTERVAL = 1.0


def draw_modern_hud(frame: np.ndarray, state_result: dict, wifi_status: bool, target_host: str, window_title: str, fps: float) -> np.ndarray:
    """
    Renders a modern, elegant, non-cluttered HUD overlay onto the OpenCV frame.
    """
    h, w = frame.shape[:2]
    is_active = state_result["is_active"]
    primary_scenario = state_result["primary_scenario"]
    progress = state_result["warning_progress"]

    overlay = frame.copy()

    # 1. Top Glassmorphism Status Header (Banner Height: 65px)
    banner_h = 65
    if is_active:
        # Pulsing Red Alert when Distracted
        pulse = int(time.time() * 5) % 2 == 0
        banner_bg = (10, 10, 210) if pulse else (10, 10, 160)
        status_text = f"DISTRACTED - {primary_scenario.upper() if primary_scenario else 'ALERT'} TRIGGERED!"
        status_sub = "TASER & ALARM ACTIVE"
        accent_color = (255, 255, 255)
    elif primary_scenario is not None and progress > 0.0:
        # Amber / Gold Warning Badge during countdown threshold
        banner_bg = (0, 120, 210)
        status_text = f"WARNING: {primary_scenario.upper()} DETECTED"
        status_sub = f"Counting Down... ({int(progress * 100)}%)"
        accent_color = (255, 255, 255)
    else:
        # Sleek Emerald Green when Focused
        banner_bg = (15, 110, 35)
        status_text = "FOCUSED - MONITORING ACTIVE"
        status_sub = "All Systems Nominal"
        accent_color = (255, 255, 255)

    # Render translucent banner background
    cv2.rectangle(overlay, (0, 0), (w, banner_h), banner_bg, -1)
    cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

    # Status Header Text
    cv2.putText(frame, status_text, (20, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.75, accent_color, 2, cv2.LINE_AA)
    cv2.putText(frame, status_sub, (20, 53), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (220, 220, 220), 1, cv2.LINE_AA)

    # 2. Sleek Warning Progress Bar (Renders under top banner during warning countdown)
    if primary_scenario is not None and not is_active:
        bar_x, bar_y = 20, 72
        bar_w, bar_h_px = w - 40, 8
        fill_w = int(bar_w * progress)

        # Background track
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h_px), (40, 40, 40), -1)
        # Progress fill
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h_px), (0, 180, 255), -1)

    # 3. Bottom Glassmorphism Footer (Footer Height: 35px)
    footer_h = 35
    footer_overlay = frame.copy()
    cv2.rectangle(footer_overlay, (0, h - footer_h), (w, h), (20, 20, 20), -1)
    cv2.addWeighted(footer_overlay, 0.8, frame, 0.2, 0, frame)

    # Wi-Fi Link Indicator
    wifi_text = f"Wi-Fi: {'CONNECTED' if wifi_status else 'SEARCHING'} ({target_host})"
    wifi_color = (40, 230, 40) if wifi_status else (40, 40, 230)
    cv2.putText(frame, wifi_text, (15, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.42, wifi_color, 1, cv2.LINE_AA)

    # Active Window Title (Truncated if too long)
    if window_title:
        clean_title = window_title[:30] + "..." if len(window_title) > 30 else window_title
        cv2.putText(frame, f"App: {clean_title}", (w // 2 - 100, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1, cv2.LINE_AA)

    # FPS Counter
    cv2.putText(frame, f"FPS: {fps:.1f}", (w - 90, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (220, 220, 220), 1, cv2.LINE_AA)

    return frame


def main():
    logging.info("Initializing Study Taser Distraction Monitor...")

    # Initialize Computer Vision Modules & State Machine
    face_tracker = FaceTracker()
    phone_detector = PhoneDetector()
    state_machine = DistractionStateMachine()
    esp32 = WiFiLink(ESP32_HOST)

    # Open Camera Capture with graceful index fallback
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW if sys.platform.startswith("win") else cv2.CAP_ANY)
    if not cap.isOpened():
        logging.warning(f"Could not open camera index {CAMERA_INDEX}. Falling back to camera index 0...")
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW if sys.platform.startswith("win") else cv2.CAP_ANY)
        if not cap.isOpened():
            logging.error("No valid webcam found! Exiting.")
            esp32.close()
            sys.exit(1)

    logging.info("Webcam active. Press 'q' or 'ESC' in the camera window to stop.")

    last_browser_check = 0.0
    browser_info = {"scenario": None, "window_title": ""}
    prev_time = time.time()
    fps = 0.0
    was_active = False

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            # FPS calculation
            curr_time = time.time()
            dt = curr_time - prev_time
            if dt > 0:
                fps = 0.9 * fps + 0.1 * (1.0 / dt)
            prev_time = curr_time

            # 1. Process Vision Trackers
            face_result = face_tracker.process(frame)
            phone_result = phone_detector.process(frame)

            # 2. Check Browser / Active Window Title periodically
            if curr_time - last_browser_check > BROWSER_CHECK_INTERVAL:
                browser_info = check_browser()
                last_browser_check = curr_time

            # 3. Evaluate State Machine
            state_result = state_machine.update(
                face_present=face_result["face_present"],
                eyes_closed_conf=face_result["eyes_closed_conf"],
                phone_detected=phone_result["phone_detected"],
                browser_scenario=browser_info["scenario"],
            )

            is_active = state_result["is_active"]

            # 4. Non-blocking Asynchronous Transmission to ESP32 over Wi-Fi
            esp32.send_state(is_active)

            # 5. Handle Trigger / Recovery Effects
            if is_active:
                if state_result["new_trigger"]:
                    logging.info(f">>> DISTRACTION EVENT TRIGGERED: [{state_result['new_trigger']}]")
                    try:
                        trigger_effect(state_result["new_trigger"])
                    except Exception as e:
                        logging.error(f"Failed to launch trigger effect: {e}")
                was_active = True
            else:
                if was_active:
                    logging.info(">>> RECOVERED FOCUS: Instantly stopping sound effects and popups...")
                    try:
                        stop_effects()
                    except Exception as e:
                        logging.error(f"Error stopping effects: {e}")
                    was_active = False

            # 6. Render Modern HUD Overlay
            hud_frame = draw_modern_hud(
                frame,
                state_result,
                wifi_status=esp32.is_connected,
                target_host=ESP32_HOST,
                window_title=browser_info.get("window_title", ""),
                fps=fps,
            )

            # 7. Render Window
            cv2.imshow("Study Taser - Focus Monitor", hud_frame)

            # 8. Keyboard Controls (Press 'q' or ESC to exit)
            key = cv2.waitKey(1) & 0xFF
            if key in [ord('q'), ord('Q'), 27]:
                logging.info("Exit key pressed. Stopping Study Taser...")
                break

    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received.")
    finally:
        logging.info("Cleaning up resources...")
        try:
            stop_effects()
        except Exception:
            pass
        cap.release()
        cv2.destroyAllWindows()
        face_tracker.close()
        phone_detector.close()
        esp32.close()
        logging.info("Study Taser stopped cleanly.")


if __name__ == "__main__":
    main()

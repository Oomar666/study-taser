# Study Taser

A real-time distraction monitoring system that combines computer vision, browser activity tracking, and wireless hardware actuation to enforce study focus. When the user is detected as distracted, the system sends a Wi-Fi trigger to a standalone ESP32-S3 microcontroller, which fires a relay-driven vibration motor and alarm buzzer.

---

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Distraction Scenarios](#distraction-scenarios)
- [Hardware](#hardware)
- [Software Stack](#software-stack)
- [Project Structure](#project-structure)
- [Setup and Installation](#setup-and-installation)
- [Usage](#usage)
- [ESP32 Firmware](#esp32-firmware)
- [Configuration](#configuration)
- [Future Improvements](#future-improvements)
- [License](#license)

---

## Overview

Study Taser bridges software-based visual detection with physical hardware actuation. A Python application runs on the host PC, processing a live webcam feed through MediaPipe and TensorFlow Lite models to detect loss of focus. When a distraction state is confirmed, the PC transmits an HTTP command over Wi-Fi to an ESP32-S3 microcontroller, which is completely untethered from the PC and powered by a 12V battery pack stepped down to 5V. The ESP32 then triggers a 5V low-level relay and active buzzer to physically alert the user.

All distraction states clear **instantly** the moment the user returns to a focused position. Audio effects, image popups, and hardware actuators shut off in the same frame.

---

## System Architecture

```
+-------------------+        Wi-Fi (HTTP)        +-------------------+
|                   |  --- /on  (distracted) ---> |                   |
|   Host PC         |  --- /off (focused)   ---> |   ESP32-S3        |
|   (Python App)    |  <-- /status (health) ---  |   (Standalone)    |
|                   |                             |                   |
|  - Webcam Feed    |                             |  - 5V Relay       |
|  - Face Tracking  |                             |  - Active Buzzer  |
|  - Phone Detect   |                             |  - Vibration Motor|
|  - Browser Monitor|                             |  - 12V Battery    |
+-------------------+                             +-------------------+
```

Communication is handled over local Wi-Fi using mDNS (`http://studytaser.local`). The ESP32 exposes three HTTP endpoints: `/on`, `/off`, and `/status`. A 5-second safety watchdog on the ESP32 automatically disarms actuators if the PC stops sending heartbeat signals.

---

## Distraction Scenarios

The state machine evaluates four independent distraction categories. Each has a configurable trigger threshold to prevent false positives.

| Scenario        | Detection Method                        | Trigger Threshold | Description                                      |
|-----------------|-----------------------------------------|-------------------|--------------------------------------------------|
| **Look Away**   | YuNet face detection fails              | 2.0 seconds       | Face absent from frame continuously               |
| **Doomscroll**  | EfficientDet phone detection            | 0.5 seconds       | Smartphone detected in frame                      |
| **Sleeping**    | Face present, eyes closed (conf > 0.4)  | 3.0 seconds       | Eyes closed while face is still visible            |
| **Social Media**| Active window title contains keywords   | 3.0 seconds       | YouTube, Facebook, Instagram, or TikTok detected  |
| **Chess**       | Active window title contains keywords   | 3.0 seconds       | Chess.com detected in active browser tab           |

All scenarios use **instant recovery** (0.0s clear delay). The moment all conditions clear, the system returns to the focused state.

---

## Hardware

### Components

| Component                  | Specification                                    |
|----------------------------|--------------------------------------------------|
| Microcontroller            | ESP32-S3-DevKit                                  |
| Relay                      | 5V 1-Channel Low-Level Trigger Relay             |
| Buzzer                     | Active High Buzzer                               |
| Motor                      | Heavy vibration motor                            |
| Power Supply               | 12V battery pack with 5V step-down converter     |
| Camera                     | Standard USB webcam                              |
| Prototyping                | Perfboard, jumper wires                          |

### Pin Configuration

| Pin       | GPIO | Mode               | Logic                                      |
|-----------|------|--------------------|--------------------------------------------|
| RELAY_PIN | 0    | OUTPUT_OPEN_DRAIN  | LOW = Relay ON (pull to GND), HIGH = Float (Relay OFF) |
| BUZZER_PIN| 6    | OUTPUT             | HIGH = Buzzer ON, LOW = Buzzer OFF         |

> **Note:** GPIO 0 must remain in `OUTPUT_OPEN_DRAIN` mode. Standard push-pull output causes 3.3V logic leakage across the 5V relay optocoupler.

---

## Software Stack

| Layer          | Technology                                           |
|----------------|------------------------------------------------------|
| Language       | Python 3.13, C++ (Arduino)                           |
| Face Tracking  | MediaPipe Face Landmarker (`face_landmarker.task`)   |
| Phone Detection| MediaPipe / TFLite (`efficientdet_lite0.tflite`)     |
| Camera         | OpenCV (`cv2`)                                       |
| Browser Monitor| pygetwindow                                          |
| Wi-Fi Client   | requests (non-blocking, threaded)                    |
| Audio          | pygame                                               |
| Image Popups   | Tkinter, Pillow                                      |
| Firmware       | Arduino ESP32 Core 3.3.11                            |
| Board Package  | esp32:esp32:esp32s3                                  |

---

## Project Structure

```
study-taser/
|-- main.py                          # Application entry point, camera loop, HUD overlay
|-- effects.py                       # Sound playback and image popup system
|-- wifi_comm.py                     # Async Wi-Fi HTTP client with heartbeat
|-- browser_monitor.py               # Active window title monitoring
|-- serial_comm.py                   # Legacy serial communication (unused)
|
|-- vision/
|   |-- __init__.py
|   |-- face_tracker.py              # MediaPipe face landmarker and blink detection
|   |-- phone_detector.py            # TFLite phone detection model
|   |-- state_machine.py             # Distraction state evaluation engine
|
|-- models/
|   |-- face_landmarker.task          # MediaPipe face landmarker model
|   |-- efficientdet_lite0.tflite     # EfficientDet object detection model
|
|-- assets/
|   |-- images/
|   |   |-- away/                     # Popup images for look-away scenario
|   |   |-- phone/                    # Popup images for phone scenario
|   |   |-- sleeping/                 # Popup images for sleeping scenario
|   |   |-- social_media/             # Popup images for social media scenario
|   |   |-- chess/                    # Popup images for chess scenario
|   |-- sounds/
|       |-- away/                     # Sound clips for look-away scenario
|       |-- phone/                    # Sound clips for phone scenario
|       |-- sleeping/                 # Sound clips for sleeping scenario
|       |-- social_media/             # Sound clips for social media scenario
|       |-- chess/                    # Sound clips for chess scenario
|
|-- esp_st_firmware_copy_20260828160433/
|   |-- esp_st_firmware_copy_20260828160433.ino   # ESP32-S3 Arduino firmware
|
|-- test_*.py                         # Individual test scripts for each module
```

---

## Setup and Installation

### Prerequisites

- Python 3.10 or higher
- A USB webcam
- ESP32-S3 with Arduino IDE configured (board package `esp32:esp32:esp32s3`)
- Local Wi-Fi network

### Python Environment

```powershell
# Create and activate virtual environment (Windows PowerShell)
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install opencv-python mediapipe requests pygame Pillow pygetwindow
```

### ESP32 Firmware

1. Open `esp_st_firmware_copy_20260828160433/esp_st_firmware_copy_20260828160433.ino` in Arduino IDE.
2. Set the board to `ESP32-S3 Dev Module` under Tools > Board.
3. Update the Wi-Fi credentials in the firmware if your network differs.
4. Upload the firmware to the ESP32-S3.

---

## Usage

```powershell
# Activate virtual environment
.\venv\Scripts\activate

# Run the monitor
python main.py
```

The application opens a camera window with a real-time HUD overlay displaying:

- **Top banner:** Current state (Focused / Warning / Distracted) with scenario label
- **Progress bar:** Visual countdown during warning threshold
- **Bottom footer:** FPS counter, active window title, and Wi-Fi connection status

Press `q` or `ESC` in the camera window to exit.

---

## ESP32 Firmware

The ESP32 firmware operates as a standalone Wi-Fi HTTP server with three endpoints:

| Endpoint  | Method | Action                                    |
|-----------|--------|-------------------------------------------|
| `/on`     | GET    | Activates relay and buzzer                |
| `/off`    | GET    | Deactivates relay and buzzer              |
| `/status` | GET    | Returns current system state as JSON      |

The firmware includes:

- **mDNS responder:** Accessible at `http://studytaser.local` without needing to know the IP address.
- **Safety watchdog:** Automatically deactivates all actuators after 5 seconds without a heartbeat signal.
- **Auto-reconnect:** Monitors Wi-Fi connectivity and attempts background reconnection if the link drops.
- **Serial passthrough:** Accepts `1` and `0` commands over UART at 115200 baud as a fallback.

---

## Configuration

Key parameters can be adjusted at the top of each source file:

### main.py

| Parameter               | Default              | Description                        |
|-------------------------|----------------------|------------------------------------|
| `ESP32_HOST`            | `"studytaser.local"` | ESP32 hostname or IP address       |
| `CAMERA_INDEX`          | `0`                  | OpenCV camera device index         |
| `BROWSER_CHECK_INTERVAL`| `1.0`               | Seconds between browser title checks |

### vision/state_machine.py

| Parameter               | Default | Description                              |
|-------------------------|---------|------------------------------------------|
| `EYES_CLOSED_THRESHOLD` | `0.4`   | Confidence threshold for closed eyes     |
| Phone trigger            | `0.5s`  | Continuous detection before flagging     |
| Away trigger             | `2.0s`  | Continuous absence before flagging       |
| Sleeping trigger         | `3.0s`  | Continuous eyes-closed before flagging   |
| Browser triggers         | `3.0s`  | Continuous browser match before flagging |

### browser_monitor.py

Social media and chess keywords can be extended by modifying the `KEYWORDS` dictionary.

---

## Future Improvements

- Design and fabricate a custom PCB to replace the perfboard prototype.
- 3D-print an enclosure for the ESP32 and relay assembly.
- Add a configuration GUI for adjusting thresholds without editing source files.
- Implement a session analytics dashboard to track distraction frequency over time.
- Support additional distraction categories through the keyword dictionary.

---

## License

This project is for personal and educational use.
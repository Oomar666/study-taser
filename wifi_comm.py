import time
import logging
import threading
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")


class WiFiLink:
    """
    Handles non-blocking asynchronous HTTP requests to the ESP32-S3 over local Wi-Fi.
    Fires HTTP requests in a background thread to prevent OpenCV video stutter.
    Maintains periodic heartbeat signals while active to satisfy ESP32 safety watchdog.
    """

    def __init__(self, esp32_ip: str = "studytaser.local", timeout: float = 2.0, retries: int = 1, heartbeat_interval: float = 1.5):
        # Format base URL
        if not esp32_ip.startswith("http://") and not esp32_ip.startswith("https://"):
            self.base_url = f"http://{esp32_ip}"
        else:
            self.base_url = esp32_ip

        self.timeout = timeout
        self.retries = retries
        self.heartbeat_interval = heartbeat_interval

        self._last_sent = None
        self._last_send_time = 0.0
        self.is_connected = True
        self._lock = threading.Lock()

    def send_state(self, is_active: bool, force: bool = False):
        """
        Sends state to ESP32: True -> /on, False -> /off.
        Fires request if state changed, or if heartbeat interval elapsed while active.
        """
        now = time.time()
        state_changed = (is_active != self._last_sent)
        heartbeat_due = is_active and (now - self._last_send_time > self.heartbeat_interval)

        if not force and not state_changed and not heartbeat_due:
            return

        endpoint = "/on" if is_active else "/off"
        url = self.base_url + endpoint

        self._last_sent = is_active
        self._last_send_time = now

        # Dispatch non-blocking background thread for HTTP request
        thread = threading.Thread(target=self._send_worker, args=(url, is_active), daemon=True)
        thread.start()

    def _send_worker(self, url: str, is_active: bool):
        for attempt in range(1, self.retries + 1):
            try:
                response = requests.get(url, timeout=self.timeout)
                if response.status_code == 200:
                    with self._lock:
                        self.is_connected = True
                    return
            except requests.RequestException:
                pass

        with self._lock:
            self.is_connected = False
        logging.warning(f"[Wi-Fi] Unable to reach ESP32 at {url}")

    def close(self):
        """Turn off actuators on exit."""
        self.send_state(False, force=True)
        logging.info("[Wi-Fi] WiFiLink closed.")

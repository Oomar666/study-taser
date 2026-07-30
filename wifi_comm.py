import requests


class WiFiLink:
    def __init__(self, esp32_ip, timeout=3.0, retries=2):
        self.base_url = f"http://{esp32_ip}"
        self.timeout = timeout
        self.retries = retries
        self._last_sent = None

    def send_state(self, is_active):
        if is_active == self._last_sent:
            return
        endpoint = "/on" if is_active else "/off"

        for attempt in range(1, self.retries + 2):
            try:
                requests.get(self.base_url + endpoint, timeout=self.timeout)
                self._last_sent = is_active
                return
            except requests.exceptions.RequestException as e:
                print(f"WiFi request attempt {attempt} failed: {e}")

        print(f"WiFi request to {endpoint} failed after all retries.")

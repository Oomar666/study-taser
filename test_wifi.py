import time
from wifi_comm import WiFiLink

esp32_ip = "192.168.1.2"
link = WiFiLink(esp32_ip)

print("Turning ON for 3 seconds...")
link.send_state(True)
time.sleep(3)

print("Turning OFF...")
link.send_state(False)

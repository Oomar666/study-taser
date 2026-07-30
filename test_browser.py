import time
from browser_monitor import check_browser

print("Checking active window every 2 seconds. Switch to different tabs/apps to test.")
print("Press Ctrl+C to stop.\n")

try:
    while True:
        result = check_browser()
        print(result)
        time.sleep(2)
except KeyboardInterrupt:
    pass

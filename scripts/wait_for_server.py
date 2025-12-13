import time
import requests
import sys

url = "http://localhost:8021/v1/models"
max_retries = 30
for i in range(max_retries):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("Server is ready!")
            sys.exit(0)
    except requests.exceptions.ConnectionError:
        pass
    print(f"Waiting for server... ({i+1}/{max_retries})")
    time.sleep(2)

print("Server failed to start.")
sys.exit(1)

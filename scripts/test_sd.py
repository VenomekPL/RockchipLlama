import requests
import json
import time
import os

def test_image_generation():
    url = "http://localhost:8021/v1/images/generations"
    
    payload = {
        "prompt": "A futuristic city on Mars, high quality, 8k",
        "n": 1,
        "size": "512x512",
        "response_format": "url"
    }
    
    print(f"Sending request to {url}...")
    start_time = time.time()
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Time taken: {time.time() - start_time:.2f}s")
            print(json.dumps(result, indent=2))
            
            # Check if file exists
            data = result['data'][0]
            if 'url' in data:
                image_url = data['url']
                print(f"Image URL: {image_url}")
                # The URL is relative, e.g. /SDimages/gen_....png
                # We can check if the file exists locally since we are on the server
                local_path = image_url.lstrip('/')
                if os.path.exists(local_path):
                    print(f"Verified: File exists at {local_path}")
                else:
                    print(f"Warning: File not found at {local_path}")
        else:
            print(f"Failed with status {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_image_generation()

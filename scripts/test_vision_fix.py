import requests
import base64
import os
import json
import time

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def test_vision():
    # Image path
    image_path = "models/qwen2-vl-2b/demo_Linux_aarch64/demo.jpg"
    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        # Try fallback
        image_path = "external/rknn-llm/examples/multimodal_model_demo/data/demo.jpg"
        if not os.path.exists(image_path):
             print(f"Error: Fallback image not found at {image_path}")
             return

    print(f"Using image: {image_path}")
    base64_image = encode_image(image_path)

    url = "http://localhost:8021/v1/chat/completions"
    
    payload = {
        "model": "qwen2-vl-2b",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Describe this image in detail."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300,
        "temperature": 0.7
    }

    headers = {
        "Content-Type": "application/json"
    }

    print("Sending request to server...")
    start_time = time.time()
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        end_time = time.time()
        
        print(f"\nResponse received in {end_time - start_time:.2f}s:")
        print("-" * 50)
        print(result['choices'][0]['message']['content'])
        print("-" * 50)
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Is it running on port 8021?")
    except Exception as e:
        print(f"Error: {e}")
        if 'response' in locals():
            print(f"Response content: {response.text}")

if __name__ == "__main__":
    test_vision()

import requests
import base64
import json
import os

# Configuration
API_URL = "http://localhost:8021/v1/chat/completions"
# Ensure you have the Qwen2-VL model loaded or set as preferred
MODEL_NAME = "qwen2-vl-2b" 
# Path to an example image
IMAGE_PATH = "models/qwen2-vl-2b/demo_Linux_aarch64/demo.jpg"

def encode_image_to_base64(path):
    """Reads an image file and converts it to a base64 string."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Image not found at {path}")
        
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def main():
    print(f"🖼️  Processing image: {IMAGE_PATH}")
    
    try:
        # 1. Encode the image
        base64_image = encode_image_to_base64(IMAGE_PATH)
        
        # 2. Construct the payload
        # This follows the OpenAI Vision API format
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": "Describe what you see in this image in detail."
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
            "max_tokens": 512,
            "temperature": 0.7
        }
        
        # 3. Send the request
        print("🚀 Sending request to server...")
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        
        # 4. Print the result
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        print("\n✅ Response received:")
        print("-" * 40)
        print(content)
        print("-" * 40)
        print(f"Usage: {result.get('usage', {})}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Server response: {e.response.text}")

if __name__ == "__main__":
    main()

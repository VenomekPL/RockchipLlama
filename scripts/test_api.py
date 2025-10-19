#!/usr/bin/env python3
"""
Test script for RockchipLlama API
Demonstrates OpenAI-compatible endpoints
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8080"


def test_root():
    """Test root endpoint"""
    print("=" * 60)
    print("Testing Root Endpoint")
    print("=" * 60)
    response = requests.get(f"{BASE_URL}/")
    print(json.dumps(response.json(), indent=2))
    print()


def test_models():
    """Test models list endpoint"""
    print("=" * 60)
    print("Testing /v1/models Endpoint")
    print("=" * 60)
    response = requests.get(f"{BASE_URL}/v1/models")
    data = response.json()
    print(f"Available models: {len(data['data'])}")
    for model in data['data']:
        print(f"  - {model['id']}")
    print()


def test_chat_completion(stream=False):
    """Test chat completion endpoint"""
    print("=" * 60)
    print(f"Testing /v1/chat/completions {'(Streaming)' if stream else '(Non-streaming)'}")
    print("=" * 60)
    
    payload = {
        "model": "gemma-3-270m",
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": "What is the capital of France?"}
        ],
        "max_tokens": 150,
        "temperature": 0.7,
        "stream": stream
    }
    
    if stream:
        # Streaming request
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json=payload,
            stream=True
        )
        
        print("Streaming response:")
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]  # Remove 'data: ' prefix
                    if data == '[DONE]':
                        print("\n[DONE]")
                        break
                    try:
                        chunk = json.loads(data)
                        if chunk['choices'][0].get('delta', {}).get('content'):
                            content = chunk['choices'][0]['delta']['content']
                            print(content, end='', flush=True)
                    except json.JSONDecodeError:
                        pass
        print()
    else:
        # Non-streaming request
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json=payload
        )
        data = response.json()
        
        print(f"Request ID: {data['id']}")
        print(f"Model: {data['model']}")
        print(f"\nAssistant Response:")
        print(data['choices'][0]['message']['content'])
        print(f"\nTokens Used:")
        print(f"  Prompt: {data['usage']['prompt_tokens']}")
        print(f"  Completion: {data['usage']['completion_tokens']}")
        print(f"  Total: {data['usage']['total_tokens']}")
    
    print()


def test_health():
    """Test health endpoint"""
    print("=" * 60)
    print("Testing /v1/health Endpoint")
    print("=" * 60)
    response = requests.get(f"{BASE_URL}/v1/health")
    print(json.dumps(response.json(), indent=2))
    print()


if __name__ == "__main__":
    print("\n🚀 RockchipLlama API Test Suite\n")
    
    try:
        # Run all tests
        test_root()
        test_health()
        test_models()
        test_chat_completion(stream=False)
        test_chat_completion(stream=True)
        
        print("=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60)
        print("\n📖 Interactive API Documentation:")
        print(f"   {BASE_URL}/docs\n")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server")
        print(f"   Make sure the server is running on {BASE_URL}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

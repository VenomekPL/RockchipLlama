#!/usr/bin/env python3
"""
Simple inference test - verify each API works with actual text generation
"""
import requests
import json

BASE_URL = "http://localhost:8080"

def test_openai_chat():
    """Test OpenAI chat endpoint"""
    print("=" * 70)
    print("🔵 Testing OpenAI Chat Completion API")
    print("=" * 70)
    
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={
            "model": "qwen3-0.6b",
            "messages": [
                {"role": "user", "content": "Write a haiku about coding"}
            ],
            "max_tokens": 100,
            "temperature": 0.7
        }
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Model: {data['model']}")
        print(f"Content: {data['choices'][0]['message']['content']}")
        print(f"Tokens: {data['usage']['completion_tokens']} generated, {data['usage']['prompt_tokens']} prompt")
        print("✅ OpenAI API working!")
    else:
        print(f"❌ Error: {response.text}")
    print()


def test_ollama_generate():
    """Test Ollama generate endpoint"""
    print("=" * 70)
    print("🦙 Testing Ollama Generate API")
    print("=" * 70)
    
    response = requests.post(
        f"{BASE_URL}/api/generate",
        json={
            "model": "qwen3-0.6b",
            "prompt": "Write a haiku about artificial intelligence",
            "stream": False,
            "options": {
                "num_predict": 100,
                "temperature": 0.7
            }
        }
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {data['response']}")
        print(f"Done: {data['done']}")
        print(f"Duration: {data.get('total_duration', 0) / 1_000_000:.2f}ms")
        print("✅ Ollama Generate API working!")
    else:
        print(f"❌ Error: {response.text}")
    print()


def test_ollama_chat():
    """Test Ollama chat endpoint"""
    print("=" * 70)
    print("🦙💬 Testing Ollama Chat API")
    print("=" * 70)
    
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={
            "model": "qwen3-0.6b",
            "messages": [
                {"role": "user", "content": "Say hello in 3 languages"}
            ],
            "stream": False,
            "options": {
                "num_predict": 100,
                "temperature": 0.7
            }
        }
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Content: {data['message']['content']}")
        print(f"Done: {data['done']}")
        print("✅ Ollama Chat API working!")
    else:
        print(f"❌ Error: {response.text}")
    print()


def test_ollama_tags():
    """Test Ollama model list"""
    print("=" * 70)
    print("🏷️  Testing Ollama Tags API")
    print("=" * 70)
    
    response = requests.get(f"{BASE_URL}/api/tags")
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data['models'])} models:")
        for model in data['models']:
            print(f"  - {model['name']} ({model['details']['format']})")
        print("✅ Ollama Tags API working!")
    else:
        print(f"❌ Error: {response.text}")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🎯 RockchipLlama API Test Suite")
    print("=" * 70)
    print()
    
    # Test all endpoints
    test_openai_chat()
    test_ollama_generate()
    test_ollama_chat()
    test_ollama_tags()
    
    print("=" * 70)
    print("🎉 All tests complete!")
    print("=" * 70)

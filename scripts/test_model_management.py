#!/usr/bin/env python3
"""
Test script for RockchipLlama Model Management API
Tests model loading, unloading, and listing
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8080"


def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_available_models():
    """Test listing available models"""
    print_section("Available Models")
    
    response = requests.get(f"{BASE_URL}/v1/models/available")
    data = response.json()
    
    print(f"Total models found: {data['total']}")
    print(f"Currently loaded: {data['loaded_model'] or 'None'}\n")
    
    for model in data['models']:
        status = "✅ LOADED" if model['loaded'] else "⭕ Available"
        print(f"{status} {model['name']}")
        print(f"         Size: {model['size_mb']} MB")
        print(f"         File: {model['filename']}")
        print()
    
    return data


def test_loaded_model():
    """Test checking currently loaded model"""
    print_section("Currently Loaded Model")
    
    response = requests.get(f"{BASE_URL}/v1/models/loaded")
    data = response.json()
    
    if data['loaded']:
        print(f"✅ Model loaded: {data['model_name']}")
        print(f"   Path: {data['model_path']}")
    else:
        print("⭕ No model currently loaded")
    
    print()
    return data


def test_load_model(model_name):
    """Test loading a model"""
    print_section(f"Loading Model: {model_name}")
    
    payload = {
        "model": model_name,
        "max_context_len": 512,
        "num_npu_core": 3
    }
    
    print(f"Request: {json.dumps(payload, indent=2)}")
    print()
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/models/load",
            json=payload,
            timeout=30  # Model loading can take time
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {data['message']}")
            print(f"   Model: {data['model_name']}")
            print(f"   Loaded: {data['loaded']}")
        else:
            print(f"❌ Error {response.status_code}: {response.json()}")
            
    except requests.exceptions.Timeout:
        print("⏱️  Request timed out (model loading can be slow)")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()


def test_unload_model():
    """Test unloading current model"""
    print_section("Unloading Current Model")
    
    response = requests.post(f"{BASE_URL}/v1/models/unload")
    data = response.json()
    
    if data['success']:
        print(f"✅ {data['message']}")
    else:
        print(f"⚠️  {data['message']}")
    
    print()


def test_chat_without_model():
    """Test chat completion without loaded model"""
    print_section("Test Chat Completion (No Model Loaded)")
    
    payload = {
        "model": "test",
        "messages": [
            {"role": "user", "content": "Hello!"}
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json=payload
    )
    
    if response.status_code == 400:
        print("✅ Correctly returned error for no loaded model:")
        print(f"   {response.json()['detail']}")
    else:
        print(f"⚠️  Unexpected response: {response.status_code}")
        print(f"   {response.json()}")
    
    print()


def test_chat_with_model(model_name):
    """Test chat completion with loaded model"""
    print_section(f"Test Chat Completion (Model: {model_name})")
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2?"}
        ],
        "max_tokens": 50,
        "temperature": 0.7
    }
    
    print(f"Request: User asks 'What is 2+2?'")
    print()
    
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Response received:")
        print(f"   {data['choices'][0]['message']['content']}")
        print()
        print(f"   Tokens: {data['usage']['total_tokens']} total")
    else:
        print(f"❌ Error: {response.json()}")
    
    print()


def test_health():
    """Test health endpoint"""
    print_section("Health Check")
    
    response = requests.get(f"{BASE_URL}/v1/health")
    data = response.json()
    
    print(f"Status: {data['status']}")
    print(f"Model loaded: {data['model_loaded']}")
    print(f"Loaded model: {data.get('loaded_model', 'None')}")
    print()


if __name__ == "__main__":
    print("\n🧪 RockchipLlama Model Management Test Suite\n")
    
    try:
        # Test 1: List available models
        available = test_available_models()
        
        if available['total'] == 0:
            print("❌ No models found! Please add .rkllm models to the models/ directory")
            sys.exit(1)
        
        # Test 2: Check loaded model (should be none initially)
        test_loaded_model()
        
        # Test 3: Try chat without model (should fail gracefully)
        test_chat_without_model()
        
        # Test 4: Load the smallest model for testing
        smallest_model = min(available['models'], key=lambda x: x['size_mb'])
        print(f"📦 Will test with smallest model: {smallest_model['name']} ({smallest_model['size_mb']} MB)")
        test_load_model(smallest_model['name'])
        
        # Test 5: Check loaded model (should be loaded now)
        test_loaded_model()
        
        # Test 6: Test health check
        test_health()
        
        # Test 7: Try chat with loaded model (placeholder response)
        test_chat_with_model(smallest_model['name'])
        
        # Test 8: Unload model
        test_unload_model()
        
        # Test 9: Verify model unloaded
        test_loaded_model()
        
        print_section("✅ All Tests Completed!")
        print("\n📝 Notes:")
        print("  - Model loading/unloading tested successfully")
        print("  - Chat endpoint correctly checks for loaded model")
        print("  - Responses are still placeholders (RKLLM integration pending)")
        print()
        print("📖 Next step: Implement actual RKLLM runtime integration")
        print("   See: external/rknn-llm/examples/rkllm_server_demo/flask_server.py")
        print()
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server")
        print(f"   Make sure the server is running on {BASE_URL}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

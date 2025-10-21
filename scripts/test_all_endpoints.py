#!/usr/bin/env python3
"""
Comprehensive test of ALL API endpoints
Tests OpenAI completion, OpenAI chat, Ollama generate, and Ollama chat
"""
import requests
import json
import time

BASE_URL = "http://localhost:8080"

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_result(success, message):
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")

def test_server_status():
    """Check if server is running"""
    print_header("1. Server Status Check")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        data = response.json()
        print_result(True, f"Server: {data['name']} v{data['version']}")
        print(f"   Loaded model: {data.get('loaded_model', 'None')}")
        return True
    except Exception as e:
        print_result(False, f"Server not reachable: {e}")
        return False

def test_openai_completion():
    """Test OpenAI /v1/completions endpoint"""
    print_header("2. OpenAI Completion API (POST /v1/completions)")
    
    payload = {
        "model": "qwen3-0.6b",
        "prompt": "Write three fun facts about oranges:\n1.",
        "max_tokens": 150,
        "temperature": 0.7,
        "top_p": 0.9
    }
    
    print(f"Request: {json.dumps(payload, indent=2)}")
    
    try:
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/v1/completions",
            json=payload,
            timeout=30
        )
        elapsed = time.time() - start
        
        print(f"\nStatus: {response.status_code}")
        print(f"Time: {elapsed:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['text']
            print(f"\nResponse:")
            print(f"  Text: {content[:200]}...")
            print(f"  Tokens: prompt={data['usage']['prompt_tokens']}, "
                  f"completion={data['usage']['completion_tokens']}, "
                  f"total={data['usage']['total_tokens']}")
            print(f"  Finish reason: {data['choices'][0]['finish_reason']}")
            
            if len(content) > 0:
                print_result(True, "OpenAI Completion working - got text!")
                return True
            else:
                print_result(False, "OpenAI Completion returned empty text")
                return False
        else:
            print(f"Error: {response.text}")
            print_result(False, f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_result(False, f"Exception: {e}")
        return False

def test_openai_chat():
    """Test OpenAI /v1/chat/completions endpoint"""
    print_header("3. OpenAI Chat Completion API (POST /v1/chat/completions)")
    
    payload = {
        "model": "qwen3-0.6b",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Tell me a joke about programming"}
        ],
        "max_tokens": 150,
        "temperature": 0.8
    }
    
    print(f"Request: {json.dumps(payload, indent=2)}")
    
    try:
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json=payload,
            timeout=30
        )
        elapsed = time.time() - start
        
        print(f"\nStatus: {response.status_code}")
        print(f"Time: {elapsed:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            print(f"\nResponse:")
            print(f"  Content: {content[:200]}...")
            print(f"  Role: {data['choices'][0]['message']['role']}")
            print(f"  Tokens: prompt={data['usage']['prompt_tokens']}, "
                  f"completion={data['usage']['completion_tokens']}")
            print(f"  Finish reason: {data['choices'][0]['finish_reason']}")
            
            if len(content) > 0:
                print_result(True, "OpenAI Chat working - got text!")
                return True
            else:
                print_result(False, "OpenAI Chat returned empty text")
                return False
        else:
            print(f"Error: {response.text}")
            print_result(False, f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_result(False, f"Exception: {e}")
        return False

def test_ollama_generate():
    """Test Ollama /api/generate endpoint"""
    print_header("4. Ollama Generate API (POST /api/generate)")
    
    payload = {
        "model": "qwen3-0.6b",
        "prompt": "Write a haiku about artificial intelligence",
        "stream": False,
        "options": {
            "num_predict": 150,
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40
        }
    }
    
    print(f"Request: {json.dumps(payload, indent=2)}")
    
    try:
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/api/generate",
            json=payload,
            timeout=30
        )
        elapsed = time.time() - start
        
        print(f"\nStatus: {response.status_code}")
        print(f"Time: {elapsed:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            content = data['response']
            print(f"\nResponse:")
            print(f"  Text: {content[:200]}...")
            print(f"  Done: {data['done']}")
            print(f"  Model: {data['model']}")
            if 'total_duration' in data:
                print(f"  Total duration: {data['total_duration'] / 1_000_000:.2f}ms")
            if 'prompt_eval_count' in data:
                print(f"  Prompt tokens: {data.get('prompt_eval_count', 0)}")
            if 'eval_count' in data:
                print(f"  Completion tokens: {data.get('eval_count', 0)}")
            
            if len(content) > 0:
                print_result(True, "Ollama Generate working - got text!")
                return True
            else:
                print_result(False, "Ollama Generate returned empty text")
                return False
        else:
            print(f"Error: {response.text}")
            print_result(False, f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_result(False, f"Exception: {e}")
        return False

def test_ollama_chat():
    """Test Ollama /api/chat endpoint"""
    print_header("5. Ollama Chat API (POST /api/chat)")
    
    payload = {
        "model": "qwen3-0.6b",
        "messages": [
            {"role": "system", "content": "You are a creative writer."},
            {"role": "user", "content": "Write one sentence about space exploration"}
        ],
        "stream": False,
        "options": {
            "num_predict": 150,
            "temperature": 0.8
        }
    }
    
    print(f"Request: {json.dumps(payload, indent=2)}")
    
    try:
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json=payload,
            timeout=30
        )
        elapsed = time.time() - start
        
        print(f"\nStatus: {response.status_code}")
        print(f"Time: {elapsed:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            content = data['message']['content']
            print(f"\nResponse:")
            print(f"  Content: {content[:200]}...")
            print(f"  Role: {data['message']['role']}")
            print(f"  Done: {data['done']}")
            print(f"  Model: {data['model']}")
            
            if len(content) > 0:
                print_result(True, "Ollama Chat working - got text!")
                return True
            else:
                print_result(False, "Ollama Chat returned empty text")
                return False
        else:
            print(f"Error: {response.text}")
            print_result(False, f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_result(False, f"Exception: {e}")
        return False

def test_ollama_tags():
    """Test Ollama /api/tags endpoint"""
    print_header("6. Ollama Tags API (GET /api/tags)")
    
    try:
        response = requests.get(f"{BASE_URL}/api/tags", timeout=5)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            print(f"\nFound {len(models)} models:")
            for model in models:
                print(f"  • {model['name']}")
                print(f"    Format: {model['details']['format']}")
                print(f"    Family: {model['details'].get('family', 'unknown')}")
            
            print_result(True, f"Ollama Tags working - found {len(models)} models")
            return True
        else:
            print(f"Error: {response.text}")
            print_result(False, f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_result(False, f"Exception: {e}")
        return False

def test_openai_models():
    """Test OpenAI /v1/models endpoint"""
    print_header("7. OpenAI Models API (GET /v1/models)")
    
    try:
        response = requests.get(f"{BASE_URL}/v1/models", timeout=5)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            models = data.get('data', [])
            print(f"\nFound {len(models)} models:")
            for model in models:
                print(f"  • {model['id']}")
                print(f"    Owner: {model.get('owned_by', 'unknown')}")
            
            print_result(True, f"OpenAI Models working - found {len(models)} models")
            return True
        else:
            print(f"Error: {response.text}")
            print_result(False, f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_result(False, f"Exception: {e}")
        return False

def main():
    print("\n" + "=" * 70)
    print("  🎯 COMPREHENSIVE API TEST SUITE")
    print("  Testing ALL endpoints (OpenAI + Ollama)")
    print("=" * 70)
    
    results = {}
    
    # Test 1: Server status
    if not test_server_status():
        print("\n❌ Server not running! Start it with:")
        print("   cd /home/angeiv/AI/RockchipLlama")
        print("   source venv/bin/activate")
        print("   python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8080")
        return
    
    # Test all endpoints
    results['openai_completion'] = test_openai_completion()
    results['openai_chat'] = test_openai_chat()
    results['ollama_generate'] = test_ollama_generate()
    results['ollama_chat'] = test_ollama_chat()
    results['ollama_tags'] = test_ollama_tags()
    results['openai_models'] = test_openai_models()
    
    # Summary
    print_header("📊 TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\nResults: {passed}/{total} tests passed\n")
    
    for test_name, success in results.items():
        icon = "✅" if success else "❌"
        print(f"  {icon} {test_name.replace('_', ' ').title()}")
    
    print("\n" + "=" * 70)
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Both APIs are working correctly!")
    elif passed > 0:
        print("⚠️  SOME TESTS FAILED - Check the output above")
    else:
        print("❌ ALL TESTS FAILED - There may be a generation issue")
    
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()

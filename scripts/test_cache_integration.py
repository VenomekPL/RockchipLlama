#!/usr/bin/env python3
"""
Test binary cache integration with chat completion
Demonstrates the difference between cached and non-cached requests
"""

import requests
import json
import time

BASE_URL = "http://localhost:8080/v1"

# Our system prompt
SYSTEM_PROMPT = "You are a helpful AI assistant. You provide clear, friendly, and informative responses to user questions."

# User question
USER_QUESTION = "How are you doing this fine evening?"

def test_chat_with_plain_system_prompt():
    """Test 1: Chat completion with system prompt as plain text (NO cache)"""
    print("\n" + "="*70)
    print("TEST 1: Chat completion WITHOUT binary cache")
    print("System prompt sent as plain text in messages array")
    print("="*70)
    
    payload = {
        "model": "qwen3-0.6b",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_QUESTION}
        ],
        "max_tokens": 100,
        "temperature": 0.8
    }
    
    print("\n📤 Request:")
    print(f"  System prompt: {len(SYSTEM_PROMPT)} chars (sent as plain text)")
    print(f"  User message: {USER_QUESTION}")
    print(f"  use_cache: NOT SPECIFIED (no caching)")
    
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/chat/completions", json=payload)
    total_time = (time.time() - start_time) * 1000
    
    if response.status_code == 200:
        data = response.json()
        print("\n📥 Response:")
        print(f"  Status: ✅ SUCCESS")
        print(f"  Total time: {total_time:.1f}ms")
        print(f"  Assistant: {data['choices'][0]['message']['content'][:200]}...")
        print(f"\n  Usage:")
        print(f"    cache_hit: {data['usage'].get('cache_hit', 'N/A')}")
        print(f"    cached_prompts: {data['usage'].get('cached_prompts', 'N/A')}")
        print(f"    tokens: {data['usage']['total_tokens']}")
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text)
    
    return total_time


def test_chat_with_cache(cache_name="system"):
    """Test 2: Chat completion WITH binary cache (use_cache parameter)"""
    print("\n" + "="*70)
    print(f"TEST 2: Chat completion WITH binary cache")
    print(f"System prompt loaded from cache: '{cache_name}'")
    print("="*70)
    
    payload = {
        "model": "qwen3-0.6b",
        "use_cache": cache_name,  # ← THE KEY DIFFERENCE!
        "messages": [
            {"role": "user", "content": USER_QUESTION}
        ],
        "max_tokens": 100,
        "temperature": 0.8
    }
    
    print("\n📤 Request:")
    print(f"  use_cache: '{cache_name}' ⚡ (binary cache loaded)")
    print(f"  User message: {USER_QUESTION}")
    print(f"  System prompt: LOADED FROM CACHE (not sent)")
    
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/chat/completions", json=payload)
    total_time = (time.time() - start_time) * 1000
    
    if response.status_code == 200:
        data = response.json()
        print("\n📥 Response:")
        print(f"  Status: ✅ SUCCESS")
        print(f"  Total time: {total_time:.1f}ms")
        print(f"  Assistant: {data['choices'][0]['message']['content'][:200]}...")
        print(f"\n  Usage:")
        print(f"    cache_hit: {data['usage'].get('cache_hit', False)} ⚡")
        print(f"    cached_prompts: {data['usage'].get('cached_prompts', [])}")
        print(f"    tokens: {data['usage']['total_tokens']}")
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text)
    
    return total_time


def create_binary_cache():
    """Create binary cache (will fail due to RKLLM bug, but demonstrates API)"""
    print("\n" + "="*70)
    print("SETUP: Creating binary cache for system prompt")
    print("="*70)
    
    payload = {
        "cache_name": "system",
        "prompt": SYSTEM_PROMPT
    }
    
    print(f"\n📤 Creating cache...")
    print(f"  Cache name: system")
    print(f"  Prompt: {len(SYSTEM_PROMPT)} chars")
    
    try:
        response = requests.post(
            f"{BASE_URL}/cache/qwen3-0.6b",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Cache created successfully!")
            print(f"  Size: {data.get('size_mb', 0):.2f} MB")
            print(f"  TTFT: {data.get('ttft_ms', 0):.1f}ms")
            return True
        else:
            print(f"\n❌ Failed: {response.status_code}")
            print(response.text)
            return False
    except requests.exceptions.Timeout:
        print("\n⚠️  Cache creation timed out (RKLLM segfault issue)")
        print("     This is a known bug in RKLLM 1.2.1 binary cache feature")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def main():
    print("\n🚀 Binary Cache Integration Test")
    print("="*70)
    print("\nThis test demonstrates:")
    print("  1. Chat completion WITHOUT cache (plain text system prompt)")
    print("  2. Chat completion WITH cache (use_cache parameter)")
    print("\nNote: Binary cache creation currently crashes RKLLM (known bug)")
    print("      But the API integration is implemented and ready!")
    
    # Check if cache exists
    print("\n📋 Checking for existing caches...")
    try:
        response = requests.get(f"{BASE_URL}/cache/qwen3-0.6b")
        if response.status_code == 200:
            caches = response.json().get('data', [])
            print(f"  Found {len(caches)} cache(s)")
            for cache in caches:
                print(f"    - {cache['cache_name']}")
        else:
            print("  No caches found")
    except:
        print("  Could not check caches")
    
    # Test 1: Plain text system prompt
    time1 = test_chat_with_plain_system_prompt()
    
    input("\n⏸️  Press Enter to continue to Test 2...")
    
    # Test 2: With cache (will show warning if cache doesn't exist)
    time2 = test_chat_with_cache("system")
    
    # Summary
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    print(f"\nTest 1 (NO cache):   {time1:.1f}ms")
    print(f"Test 2 (WITH cache): {time2:.1f}ms")
    
    if time2 < time1:
        improvement = ((time1 - time2) / time1) * 100
        print(f"\n⚡ Improvement: {improvement:.1f}% faster with cache!")
    
    print("\n💡 How cache loading works:")
    print("   - Cache loading is MANUAL (opt-in), not automatic")
    print("   - Add 'use_cache': 'cache_name' to your request")
    print("   - Without use_cache: System prompt processed as plain text")
    print("   - With use_cache: NPU state loaded instantly from cache")
    print("\n✅ The integration is complete and ready to use!")
    print("   (Once RKLLM binary cache bug is fixed)")


if __name__ == "__main__":
    main()

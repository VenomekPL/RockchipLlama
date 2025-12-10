#!/usr/bin/env python3
"""
Cache Performance Test Script
Verifies the effectiveness of binary prompt caching by comparing TTFT (Time To First Token)
with and without caching.
"""

import requests
import json
import time
import sys
import os

BASE_URL = "http://localhost:8080"
CACHE_NAME = "benchmark_system_prompt"

# A moderate system prompt
SYSTEM_PROMPT = """
You are an expert AI assistant specializing in computer science.
Your goal is to provide accurate, efficient, and well-structured code examples.
When answering questions, you should:
1. Analyze the problem thoroughly.
2. Break down the solution into logical steps.
3. Provide Python code that is clean, commented, and follows PEP 8 standards.
4. Explain the time and space complexity of your solution.
5. Suggest optimizations or alternative approaches if applicable.
""" * 100  # ~40k chars (approx 10k tokens)

USER_PROMPT = "Write a hello world function."

def get_loaded_model():
    """Get the currently loaded model name"""
    try:
        response = requests.get(f"{BASE_URL}/v1/models/loaded", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("loaded"):
                return data.get("model_name")
    except Exception as e:
        print(f"Error checking loaded model: {e}")
    return None

def create_cache(model_name):
    """Create a binary cache for the system prompt"""
    print(f"📦 Creating cache '{CACHE_NAME}' for model '{model_name}'...")
    start_time = time.perf_counter()
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/cache/{model_name}",
            json={
                "cache_name": CACHE_NAME,
                "prompt": SYSTEM_PROMPT
            },
            timeout=300
        )
        
        if response.status_code in [200, 201]:
            duration = (time.perf_counter() - start_time) * 1000
            data = response.json()
            print(f"   ✅ Cache created in {duration:.2f}ms")
            print(f"   Size: {data.get('size_mb', 0):.2f} MB")
            return True
        else:
            print(f"   ❌ Failed to create cache: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error creating cache: {e}")
        return False

def run_inference(model_name, use_cache=None, run_label="Baseline"):
    """Run inference and measure TTFT"""
    print(f"🚀 Running {run_label} inference...")
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT}
        ],
        "max_tokens": 10,
        "temperature": 0.1
    }
    
    if use_cache:
        payload["use_cache"] = use_cache
    
    start_time = time.perf_counter()
    try:
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json=payload,
            timeout=300
        )
        
        if response.status_code == 200:
            total_time = (time.perf_counter() - start_time) * 1000
            data = response.json()
            content = data['choices'][0]['message']['content']
            usage = data.get('usage', {})
            
            print(f"   ✅ Success! Total time: {total_time:.2f}ms")
            print(f"   Output: {content[:50]}...")
            print(f"   Cache hit: {usage.get('cache_hit')}")
            return total_time
        else:
            print(f"   ❌ Failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error during inference: {e}")
        return None

def main():
    print("=== Starting Cache Performance Test ===")
    
    # 1. Get model
    model_name = get_loaded_model()
    if not model_name:
        print("❌ No model loaded. Please load a model first.")
        sys.exit(1)
    print(f"ℹ️  Target Model: {model_name}")
    
    # 2. Run Baseline (No Cache)
    baseline_time = run_inference(model_name, use_cache=None, run_label="Baseline (No Cache)")
    if baseline_time is None:
        sys.exit(1)
        
    # 3. Create Cache
    if not create_cache(model_name):
        sys.exit(1)
        
    # 4. Run Cached Inference
    cached_time = run_inference(model_name, use_cache=CACHE_NAME, run_label="Cached")
    if cached_time is None:
        sys.exit(1)
        
    # 5. Compare
    print("\n=== Results ===")
    print(f"Baseline Time: {baseline_time:.2f}ms")
    print(f"Cached Time:   {cached_time:.2f}ms")
    
    improvement = baseline_time - cached_time
    percent = (improvement / baseline_time) * 100
    
    print(f"Improvement:   {improvement:.2f}ms ({percent:.1f}%)")
    
    if cached_time < baseline_time:
        print("✅ Caching is working and providing speedup!")
    else:
        print("⚠️  Caching did not provide speedup (might be overhead or small prompt).")

if __name__ == "__main__":
    main()

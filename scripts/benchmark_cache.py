#!/usr/bin/env python3
"""
Benchmark tool for RockchipLlama API server - Caching Performance.
Tests the performance impact of Binary Prompt Caching.
"""

import json
import time
import requests
import sys
import os
from datetime import datetime

BASE_URL = "http://localhost:8080"
MODEL_NAME = "qwen3-0.6b"
CACHE_NAME = "benchmark_system_prompt"

# A long system prompt to ensure significant prefill time
SYSTEM_PROMPT = """
You are an expert AI assistant specializing in computer science, software engineering, and system architecture. 
You have deep knowledge of distributed systems, cloud computing, and embedded devices.
Your goal is to provide accurate, concise, and technically detailed answers.
When answering, you should:
1. Analyze the problem thoroughly.
2. Break down complex concepts into understandable parts.
3. Provide code examples where applicable.
4. Cite relevant best practices and design patterns.
5. Consider performance implications, especially for ARM64 architectures like the Rockchip RK3588.
6. Always prioritize correctness and safety.
7. Use markdown formatting for clarity.
8. Be helpful and polite.
9. If you don't know the answer, admit it.
10. Keep your responses focused on the user's query.
(Repeating to increase length for benchmark purposes...)
""" * 5  # ~1500 chars

USER_PROMPT = "Explain the benefits of binary caching in NPU inference."

def get_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def run_inference(use_cache=None, label="Baseline"):
    print(f"\n🧪 Running {label} Inference...")
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": USER_PROMPT}
        ],
        "max_tokens": 100,
        "stream": True
    }
    
    if use_cache:
        payload["use_cache"] = use_cache
        # When using cache, the system prompt is already in the cache, 
        # so we don't send it in messages (or we send it as part of the cache definition)
        # The API expects 'use_cache' to refer to a pre-saved state.
    else:
        # For baseline, we include the full system prompt
        payload["messages"].insert(0, {"role": "system", "content": SYSTEM_PROMPT})

    start_time = time.perf_counter()
    first_token_time = None
    
    try:
        response = requests.post(f"{BASE_URL}/v1/chat/completions", json=payload, stream=True)
        
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
            return None

        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith("data: ") and line != "data: [DONE]":
                    if first_token_time is None:
                        first_token_time = time.perf_counter()
        
        end_time = time.perf_counter()
        
        ttft = (first_token_time - start_time) * 1000 if first_token_time else 0
        total_time = (end_time - start_time) * 1000
        
        print(f"   ✅ TTFT: {ttft:.2f} ms")
        print(f"   ⏱️ Total: {total_time:.2f} ms")
        
        return {"ttft": ttft, "total": total_time}
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def create_cache():
    print(f"\n💾 Creating Cache '{CACHE_NAME}'...")
    start_time = time.perf_counter()
    
    try:
        # Use messages to ensure prompt format matches exactly what the server expects
        response = requests.post(
            f"{BASE_URL}/v1/cache/{MODEL_NAME}",
            json={
                "cache_name": CACHE_NAME,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": SYSTEM_PROMPT}
                ]
            }
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            duration = (time.perf_counter() - start_time) * 1000
            print(f"   ✅ Cache created in {duration:.2f} ms")
            print(f"   📦 Size: {data.get('size_mb', 0)} MB")
            return True
        else:
            print(f"❌ Failed to create cache: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception creating cache: {e}")
        return False

def main():
    print(f"🚀 Starting Caching Benchmark for {MODEL_NAME}")
    print(f"📝 System Prompt Length: {len(SYSTEM_PROMPT)} chars")
    
    # 1. Baseline (No Cache)
    baseline_metrics = run_inference(use_cache=None, label="Baseline (No Cache)")
    if not baseline_metrics:
        return

    # 2. Create Cache
    if not create_cache():
        return

    # 3. Cached Run
    cached_metrics = run_inference(use_cache=CACHE_NAME, label="Cached")
    if not cached_metrics:
        return

    # 4. Generate Report
    speedup = baseline_metrics['ttft'] / cached_metrics['ttft'] if cached_metrics['ttft'] > 0 else 0
    
    report = {
        "timestamp": get_timestamp(),
        "model": MODEL_NAME,
        "system_prompt_len": len(SYSTEM_PROMPT),
        "baseline": baseline_metrics,
        "cached": cached_metrics,
        "speedup_factor": speedup,
        "ttft_reduction_ms": baseline_metrics['ttft'] - cached_metrics['ttft'],
        "ttft_reduction_percent": ((baseline_metrics['ttft'] - cached_metrics['ttft']) / baseline_metrics['ttft']) * 100
    }
    
    # Save to benchmarks folder
    filename = f"benchmarks/benchmark_cache_{MODEL_NAME}_{report['timestamp']}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
        
    print("\n============================================================")
    print(f"📊 CACHE BENCHMARK RESULTS")
    print("============================================================")
    print(f"Baseline TTFT: {baseline_metrics['ttft']:.2f} ms")
    print(f"Cached TTFT:   {cached_metrics['ttft']:.2f} ms")
    print(f"Speedup:       {speedup:.2f}x 🚀")
    print(f"Reduction:     {report['ttft_reduction_percent']:.1f}%")
    print(f"📄 Report saved to: {filename}")
    print("============================================================")

if __name__ == "__main__":
    main()

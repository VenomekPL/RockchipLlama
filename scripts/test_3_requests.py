#!/usr/bin/env python3
"""
Simple 3-request concurrent test - matches n_batch=3 exactly
Tests if RKLLM can handle exactly n_batch concurrent requests (no queueing)
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime


async def send_request(session, request_id, prompt):
    """Send a single request and track timing"""
    
    payload = {
        "model": "qwen3-0.6b",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 100,  # Short responses for faster test
        "temperature": 0.6,
        "stream": False
    }
    
    start = time.time()
    print(f"[{request_id}] 📤 Sending at {start:.3f}s: {prompt[:50]}...")
    
    try:
        async with session.post(
            "http://localhost:8080/v1/chat/completions",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=120)
        ) as response:
            end = time.time()
            duration = end - start
            
            if response.status == 200:
                data = await response.json()
                content = data['choices'][0]['message']['content']
                tokens = data.get('usage', {}).get('completion_tokens', 0)
                print(f"[{request_id}] ✅ Success at {end:.3f}s ({duration:.2f}s): {tokens} tokens")
                print(f"[{request_id}] Response: {content[:100]}...")
                return True, duration
            else:
                error = await response.text()
                print(f"[{request_id}] ❌ Error {response.status}: {error}")
                return False, duration
                
    except Exception as e:
        end = time.time()
        duration = end - start
        print(f"[{request_id}] ❌ Exception at {end:.3f}s ({duration:.2f}s): {e}")
        return False, duration


async def test_3_concurrent():
    """Test exactly 3 concurrent requests (matches n_batch=3)"""
    
    print("=" * 80)
    print("🧪 Testing n_batch=3 with EXACTLY 3 concurrent requests")
    print("=" * 80)
    print("Expected: All 3 requests process in parallel (no queueing)")
    print("If this crashes, RKLLM batch inference has a fundamental bug")
    print("If this works, the issue was with >n_batch requests (queueing)")
    print("=" * 80)
    print()
    
    # Three simple prompts
    prompts = [
        "What is Python? Answer in one sentence.",
        "What is JavaScript? Answer in one sentence.",
        "What is Rust? Answer in one sentence."
    ]
    
    test_start = time.time()
    
    async with aiohttp.ClientSession() as session:
        # Launch exactly 3 requests simultaneously
        tasks = [
            send_request(session, i+1, prompt)
            for i, prompt in enumerate(prompts)
        ]
        
        print("⏱️  Launching 3 requests simultaneously...")
        print()
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    test_end = time.time()
    total_duration = test_end - test_start
    
    print()
    print("=" * 80)
    print("📊 TEST RESULTS")
    print("=" * 80)
    print(f"Total duration: {total_duration:.2f}s")
    
    successes = sum(1 for r in results if isinstance(r, tuple) and r[0])
    failures = len(results) - successes
    
    print(f"Successful: {successes}/3")
    print(f"Failed: {failures}/3")
    
    if successes == 3:
        print()
        print("🎉 SUCCESS! RKLLM can handle n_batch=3 concurrent requests!")
        print("The previous crash was likely due to >n_batch requests or queueing.")
        print()
        avg_duration = sum(r[1] for r in results if isinstance(r, tuple)) / len(results)
        print(f"Average request duration: {avg_duration:.2f}s")
        print()
        print("✅ Phase 4.2: Multi-batch inference WORKS with exactly n_batch requests!")
        return 0
    else:
        print()
        print("❌ FAILURE: RKLLM crashed or errored with n_batch=3")
        print("This confirms RKLLM 1.2.1 has a batch inference bug.")
        print()
        print("⚠️  Recommendation: Keep n_batch=1 until RKLLM fixes this.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(test_3_concurrent())
    exit(exit_code)

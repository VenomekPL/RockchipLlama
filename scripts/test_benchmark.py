#!/usr/bin/env python3
"""
Quick benchmark test - runs a few requests to demonstrate performance measurement.
This is a simplified version for quick testing before running full benchmarks.
"""

import time
import requests
import json

BASE_URL = "http://localhost:8080"

def test_quick_benchmark():
    """Run 3 quick tests to measure TTFT and tokens/sec"""
    
    print("=" * 80)
    print("🧪 QUICK BENCHMARK TEST")
    print("=" * 80)
    print()
    
    # Check if model is loaded
    print("1️⃣ Checking model status...")
    try:
        response = requests.get(f"{BASE_URL}/v1/models/loaded", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("loaded"):
                print(f"   ✅ Model loaded: {data.get('model_name')}")
            else:
                print("   ❌ No model loaded. Please load a model first:")
                print("      curl -X POST http://localhost:8080/v1/models/load \\")
                print("           -H 'Content-Type: application/json' \\")
                print("           -d '{\"model\": \"google_gemma-3-270m-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588\"}'")
                return
    except Exception as e:
        print(f"   ❌ Error checking model: {e}")
        return
    
    print()
    
    # Test prompts
    test_prompts = [
        "Explain quantum computing in simple terms.",
        "Write a haiku about programming.",
        "What are the benefits of edge computing?"
    ]
    
    results = []
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"{i}️⃣ Test {i}/3: '{prompt[:50]}...'")
        
        try:
            start_time = time.perf_counter()
            first_token_time = None
            
            response = requests.post(
                f"{BASE_URL}/v1/chat/completions",
                json={
                    "model": "current",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 100,
                    "stream": True
                },
                stream=True,
                timeout=60
            )
            
            if response.status_code != 200:
                print(f"   ❌ Failed: HTTP {response.status_code}")
                continue
            
            response_text = []
            token_count = 0
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        
                        if data_str == '[DONE]':
                            break
                        
                        try:
                            chunk = json.loads(data_str)
                            
                            # Measure TTFT
                            if first_token_time is None:
                                first_token_time = time.perf_counter()
                            
                            # Extract content
                            choices = chunk.get('choices', [])
                            if choices:
                                delta = choices[0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    response_text.append(content)
                                    token_count += 1
                        
                        except json.JSONDecodeError:
                            continue
            
            end_time = time.perf_counter()
            
            ttft_ms = (first_token_time - start_time) * 1000 if first_token_time else 0
            total_time_ms = (end_time - start_time) * 1000
            generate_time_ms = total_time_ms - ttft_ms
            tokens_per_sec = (token_count / generate_time_ms * 1000) if generate_time_ms > 0 else 0
            
            response_full = ''.join(response_text)
            
            print(f"   ✅ Success!")
            print(f"      TTFT: {ttft_ms:.2f} ms")
            print(f"      Total time: {total_time_ms:.2f} ms")
            print(f"      Tokens: {token_count}")
            print(f"      Speed: {tokens_per_sec:.2f} tokens/sec")
            print(f"      Response: {response_full[:80]}...")
            
            results.append({
                'ttft_ms': ttft_ms,
                'total_time_ms': total_time_ms,
                'tokens_per_sec': tokens_per_sec,
                'token_count': token_count
            })
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    # Summary
    if results:
        print("=" * 80)
        print("📊 SUMMARY")
        print("=" * 80)
        print()
        
        avg_ttft = sum(r['ttft_ms'] for r in results) / len(results)
        avg_total = sum(r['total_time_ms'] for r in results) / len(results)
        avg_tps = sum(r['tokens_per_sec'] for r in results) / len(results)
        total_tokens = sum(r['token_count'] for r in results)
        
        print(f"Tests completed: {len(results)}/{len(test_prompts)}")
        print(f"Average TTFT: {avg_ttft:.2f} ms")
        print(f"Average total time: {avg_total:.2f} ms")
        print(f"Average speed: {avg_tps:.2f} tokens/sec")
        print(f"Total tokens generated: {total_tokens}")
        print()
        
        print("🎯 Next steps:")
        print("   • Run full performance suite: python benchmark.py --type performance")
        print("   • Run quality tests: python benchmark.py --type quality")
        print("   • Run all tests multiple times: python benchmark.py --type all --runs 3")
        print()


if __name__ == "__main__":
    test_quick_benchmark()

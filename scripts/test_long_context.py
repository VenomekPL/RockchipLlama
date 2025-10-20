#!/usr/bin/env python3
"""
Test long context capabilities with LongRoPE-enabled models

This script progressively tests increasing context lengths to find
the actual limit of your converted model.

Usage:
    python3 scripts/test_long_context.py
    python3 scripts/test_long_context.py --max-size 16384
    python3 scripts/test_long_context.py --model qwen-8k
"""
import requests
import time
import argparse
from typing import Optional

def test_long_context(
    model: str = "qwen3-0.6b",
    context_size: int = 4096,
    base_url: str = "http://localhost:8080"
) -> tuple[bool, Optional[str], float]:
    """
    Test model with specific context length
    
    Args:
        model: Model name
        context_size: Target context length in tokens (approx)
        base_url: Server URL
        
    Returns:
        (success, answer, elapsed_time)
    """
    # Generate long context (rough: 1 token ≈ 4 chars)
    # Using repetitive pattern to test positional encoding
    base_text = "The quick brown fox jumps over the lazy dog. "
    repetitions = (context_size * 4) // len(base_text)
    long_document = base_text * repetitions
    
    # Add unique marker near the end to test recall
    marker = f"\n\nIMPORTANT: The secret code is LONGROPE{context_size}. Remember this.\n\n"
    long_document += marker
    long_document += base_text * 10  # Add more text after marker
    
    # Ask about the marker (tests if model can remember from middle of long context)
    prompt = f"""Here is a long document:

{long_document}

Question: What was the secret code mentioned in the document?
Answer:"""
    
    approx_tokens = len(prompt) // 4
    print(f"📏 Testing ~{approx_tokens:,} tokens ({len(prompt):,} chars)")
    
    start = time.time()
    try:
        response = requests.post(
            f'{base_url}/v1/chat/completions',
            json={
                'model': model,
                'messages': [
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 50,
                'temperature': 0.1  # Low temp for factual recall
            },
            timeout=60  # Long timeout for large context
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            answer = data['choices'][0]['message']['content']
            
            # Check if answer contains the secret code
            expected = f"LONGROPE{context_size}"
            if expected in answer:
                print(f"✅ Perfect recall in {elapsed:.1f}s")
                print(f"   Answer: {answer.strip()}")
                return True, answer, elapsed
            else:
                print(f"⚠️  Completed but wrong answer in {elapsed:.1f}s")
                print(f"   Expected: {expected}")
                print(f"   Got: {answer.strip()}")
                return False, answer, elapsed
        else:
            print(f"❌ HTTP {response.status_code}")
            print(f"   {response.text[:200]}")
            return False, None, elapsed
            
    except requests.exceptions.Timeout:
        elapsed = time.time() - start
        print(f"⏱️  Timeout after {elapsed:.1f}s")
        return False, None, elapsed
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Error: {e}")
        return False, None, elapsed


def main():
    parser = argparse.ArgumentParser(
        description='Test long context capabilities of LongRoPE models'
    )
    parser.add_argument(
        '--model',
        default='qwen3-0.6b',
        help='Model name to test (default: qwen3-0.6b)'
    )
    parser.add_argument(
        '--max-size',
        type=int,
        default=16384,
        help='Maximum context size to test (default: 16384)'
    )
    parser.add_argument(
        '--base-url',
        default='http://localhost:8080',
        help='Server URL (default: http://localhost:8080)'
    )
    parser.add_argument(
        '--start-size',
        type=int,
        default=512,
        help='Starting context size (default: 512)'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🎯 LongRoPE Context Length Test")
    print("=" * 70)
    print(f"Model: {args.model}")
    print(f"Range: {args.start_size:,} → {args.max_size:,} tokens")
    print(f"Server: {args.base_url}")
    print()
    
    # Test sizes: exponential growth
    test_sizes = []
    size = args.start_size
    while size <= args.max_size:
        test_sizes.append(size)
        size *= 2
    
    results = []
    
    for size in test_sizes:
        print(f"\n{'='*70}")
        print(f"📋 Testing {size:,} token context")
        print('='*70)
        
        success, answer, elapsed = test_long_context(
            model=args.model,
            context_size=size,
            base_url=args.base_url
        )
        
        results.append({
            'size': size,
            'success': success,
            'elapsed': elapsed,
            'answer': answer
        })
        
        if not success:
            print(f"\n⚠️  Failed at {size:,} tokens - likely context limit reached")
            break
        
        # Cool down between tests (NPU needs rest)
        if size < args.max_size:
            print("\n⏳ Cooling down...")
            time.sleep(3)
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    print(f"{'Context Size':<15} {'Status':<10} {'Time (s)':<10} {'Result'}")
    print("-" * 70)
    
    for r in results:
        status = "✅ PASS" if r['success'] else "❌ FAIL"
        answer_preview = r['answer'][:30] if r['answer'] else "N/A"
        print(f"{r['size']:>13,} {status:<10} {r['elapsed']:>8.1f}   {answer_preview}...")
    
    # Determine maximum working context
    successful = [r for r in results if r['success']]
    if successful:
        max_working = successful[-1]['size']
        print("\n" + "=" * 70)
        print(f"✅ Maximum working context: {max_working:,} tokens")
        print("=" * 70)
        print(f"\n💡 Recommendation:")
        print(f"   Set max_context_len = {max_working} in config/inference_config.json")
        
        # Performance analysis
        if len(successful) > 1:
            print(f"\n📈 Performance Scaling:")
            base_time = successful[0]['elapsed']
            base_size = successful[0]['size']
            for r in successful[1:]:
                time_ratio = r['elapsed'] / base_time
                size_ratio = r['size'] / base_size
                print(f"   {r['size']:>6,} tokens: {r['elapsed']:>5.1f}s "
                      f"({time_ratio:.1f}x time for {size_ratio:.1f}x context)")
    else:
        print("\n❌ No successful tests - check server and model status")


if __name__ == '__main__':
    main()

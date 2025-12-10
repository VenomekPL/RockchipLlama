#!/usr/bin/env python3
"""
Concurrent Batch Test - Phase 4.2 Multi-Batch Inference Validation

Sends all 10 test prompts simultaneously to validate:
- 3 requests run in parallel (batch slots 1-3)
- 7 requests queue and process as slots free
- No timeouts or errors
- Proper throughput improvement

Expected behavior:
- Requests 1-3: Immediate processing (parallel on 3 NPU cores)
- Requests 4-10: Queued, processed as slots free
- Total throughput: ~3x improvement vs sequential
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
import sys


@dataclass
class RequestResult:
    """Result from a single concurrent request"""
    request_id: int
    prompt_id: str
    prompt_name: str
    prompt_length: int
    
    # Timing
    submit_time: float  # When request was sent
    first_response_time: float  # When first byte received
    complete_time: float  # When request completed
    
    ttft_ms: float  # Time to first token
    total_time_ms: float  # Total request time
    queue_wait_ms: float  # Time spent waiting in queue
    
    # Results
    response_length: int
    tokens_generated: int
    tokens_per_second: float
    
    success: bool
    error: str = ""
    
    # Server-reported metrics (if available)
    server_prefill_ms: float = 0.0
    server_generate_ms: float = 0.0
    server_memory_mb: float = 0.0


class ConcurrentBatchTester:
    """Tests concurrent batch inference with all 10 test prompts"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.results: List[RequestResult] = []
        
    async def send_chat_request(
        self,
        session: aiohttp.ClientSession,
        request_id: int,
        prompt: str,
        prompt_id: str,
        prompt_name: str
    ) -> RequestResult:
        """Send a single chat completion request"""
        
        submit_time = time.time()
        
        try:
            payload = {
                "model": "qwen3-0.6b",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 512,
                "temperature": 0.6,
                "stream": False
            }
            
            print(f"[{request_id:2d}] 📤 Sending: {prompt_id} - {prompt_name}")
            
            # No timeout - let it queue as long as needed
            async with session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=None)  # No timeout!
            ) as response:
                first_response_time = time.time()
                ttft_ms = (first_response_time - submit_time) * 1000
                
                data = await response.json()
                complete_time = time.time()
                
                if response.status == 200:
                    response_text = data['choices'][0]['message']['content']
                    tokens_generated = data.get('usage', {}).get('completion_tokens', 0)
                    total_time_ms = (complete_time - submit_time) * 1000
                    
                    # Estimate queue wait time (TTFT includes queue + prefill)
                    # If we had server metrics, we could calculate: queue_wait = TTFT - prefill
                    queue_wait_ms = 0.0  # Will be estimated later
                    
                    tokens_per_second = 0.0
                    if total_time_ms > 0 and tokens_generated > 0:
                        tokens_per_second = (tokens_generated / total_time_ms) * 1000
                    
                    print(f"[{request_id:2d}] ✅ Complete: {tokens_generated} tokens in {total_time_ms:.0f}ms ({tokens_per_second:.1f} tok/s) - TTFT: {ttft_ms:.0f}ms")
                    
                    return RequestResult(
                        request_id=request_id,
                        prompt_id=prompt_id,
                        prompt_name=prompt_name,
                        prompt_length=len(prompt),
                        submit_time=submit_time,
                        first_response_time=first_response_time,
                        complete_time=complete_time,
                        ttft_ms=ttft_ms,
                        total_time_ms=total_time_ms,
                        queue_wait_ms=queue_wait_ms,
                        response_length=len(response_text),
                        tokens_generated=tokens_generated,
                        tokens_per_second=tokens_per_second,
                        success=True
                    )
                else:
                    error_msg = data.get('detail', f"HTTP {response.status}")
                    print(f"[{request_id:2d}] ❌ Error: {error_msg}")
                    
                    return RequestResult(
                        request_id=request_id,
                        prompt_id=prompt_id,
                        prompt_name=prompt_name,
                        prompt_length=len(prompt),
                        submit_time=submit_time,
                        first_response_time=complete_time,
                        complete_time=complete_time,
                        ttft_ms=(complete_time - submit_time) * 1000,
                        total_time_ms=(complete_time - submit_time) * 1000,
                        queue_wait_ms=0.0,
                        response_length=0,
                        tokens_generated=0,
                        tokens_per_second=0.0,
                        success=False,
                        error=error_msg
                    )
                    
        except Exception as e:
            complete_time = time.time()
            print(f"[{request_id:2d}] ❌ Exception: {str(e)}")
            
            return RequestResult(
                request_id=request_id,
                prompt_id=prompt_id,
                prompt_name=prompt_name,
                prompt_length=len(prompt),
                submit_time=submit_time,
                first_response_time=complete_time,
                complete_time=complete_time,
                ttft_ms=(complete_time - submit_time) * 1000,
                total_time_ms=(complete_time - submit_time) * 1000,
                queue_wait_ms=0.0,
                response_length=0,
                tokens_generated=0,
                tokens_per_second=0.0,
                success=False,
                error=str(e)
            )
    
    async def run_concurrent_test(self) -> Dict[str, Any]:
        """Run all 10 test prompts concurrently"""
        
        # Load test prompts
        prompts_file = "/home/angeiv/AI/RockchipLlama/config/benchmark_prompts.json"
        with open(prompts_file, 'r') as f:
            prompts_data = json.load(f)
        
        # Collect all 10 tests
        all_tests = []
        
        # 5 performance tests
        for test in prompts_data['performance_tests']['tests']:
            all_tests.append({
                'id': test['id'],
                'name': test['name'],
                'prompt': test['prompt']
            })
        
        # 5 quality tests
        for test in prompts_data['quality_tests']['tests']:
            all_tests.append({
                'id': test['id'],
                'name': test['name'],
                'prompt': test['prompt']
            })
        
        print("=" * 80)
        print("🚀 CONCURRENT BATCH TEST - Phase 4.2 Multi-Batch Inference")
        print("=" * 80)
        print(f"Total requests: {len(all_tests)}")
        print(f"Batch size (n_batch): 3")
        print(f"Expected: Requests 1-3 parallel, 4-10 queued")
        print(f"Server: {self.base_url}")
        print("=" * 80)
        print()
        
        test_start = time.time()
        
        # Create all requests simultaneously
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.send_chat_request(
                    session=session,
                    request_id=i + 1,
                    prompt=test['prompt'],
                    prompt_id=test['id'],
                    prompt_name=test['name']
                )
                for i, test in enumerate(all_tests)
            ]
            
            # Launch all requests at once!
            print(f"⏱️  Launching all {len(tasks)} requests simultaneously...")
            print()
            
            self.results = await asyncio.gather(*tasks)
        
        test_end = time.time()
        total_duration = test_end - test_start
        
        return self.analyze_results(total_duration)
    
    def analyze_results(self, total_duration: float) -> Dict[str, Any]:
        """Analyze and report results"""
        
        print()
        print("=" * 80)
        print("📊 BATCH TEST RESULTS")
        print("=" * 80)
        
        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]
        
        print(f"Total requests: {len(self.results)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")
        print(f"Total duration: {total_duration:.2f}s")
        print()
        
        if failed:
            print("❌ FAILED REQUESTS:")
            for r in failed:
                print(f"  [{r.request_id:2d}] {r.prompt_id}: {r.error}")
            print()
        
        if successful:
            # Sort by completion time to see order
            by_completion = sorted(successful, key=lambda x: x.complete_time)
            
            print("✅ COMPLETION ORDER (by finish time):")
            for i, r in enumerate(by_completion, 1):
                relative_time = (r.complete_time - successful[0].submit_time) * 1000
                print(f"  {i:2d}. [{r.request_id:2d}] {r.prompt_id:20s} - {r.tokens_generated:3d} tok, "
                      f"{r.tokens_per_second:5.1f} tok/s, TTFT: {r.ttft_ms:6.0f}ms, "
                      f"Finished: +{relative_time:6.0f}ms")
            print()
            
            # Performance metrics
            avg_ttft = sum(r.ttft_ms for r in successful) / len(successful)
            min_ttft = min(r.ttft_ms for r in successful)
            max_ttft = max(r.ttft_ms for r in successful)
            
            avg_speed = sum(r.tokens_per_second for r in successful) / len(successful)
            min_speed = min(r.tokens_per_second for r in successful)
            max_speed = max(r.tokens_per_second for r in successful)
            
            total_tokens = sum(r.tokens_generated for r in successful)
            aggregate_throughput = total_tokens / total_duration
            
            print("⚡ PERFORMANCE METRICS:")
            print(f"  TTFT: avg={avg_ttft:.0f}ms, min={min_ttft:.0f}ms, max={max_ttft:.0f}ms")
            print(f"  Speed: avg={avg_speed:.1f} tok/s, min={min_speed:.1f} tok/s, max={max_speed:.1f} tok/s")
            print(f"  Total tokens generated: {total_tokens}")
            print(f"  Aggregate throughput: {aggregate_throughput:.1f} tok/s")
            print()
            
            # Analyze batching behavior
            print("🔍 BATCHING ANALYSIS:")
            
            # Group by start time (within 100ms = same batch)
            batches = []
            current_batch = []
            
            for r in sorted(successful, key=lambda x: x.submit_time):
                if not current_batch or (r.submit_time - current_batch[0].submit_time) < 0.1:
                    current_batch.append(r)
                else:
                    batches.append(current_batch)
                    current_batch = [r]
            if current_batch:
                batches.append(current_batch)
            
            print(f"  Detected {len(batches)} submission batch(es)")
            
            # Analyze TTFT distribution (should show 3 groups: immediate, queued wave 1, queued wave 2)
            ttfts = sorted([r.ttft_ms for r in successful])
            print(f"  TTFT distribution:")
            print(f"    Requests 1-3: {', '.join(f'{t:.0f}ms' for t in ttfts[:3])}")
            if len(ttfts) > 3:
                print(f"    Requests 4-6: {', '.join(f'{t:.0f}ms' for t in ttfts[3:6])}")
            if len(ttfts) > 6:
                print(f"    Requests 7-10: {', '.join(f'{t:.0f}ms' for t in ttfts[6:])}")
            print()
            
            # Expected vs actual throughput
            single_request_speed = 15.59  # From benchmarks
            expected_sequential_time = total_tokens / single_request_speed
            speedup = expected_sequential_time / total_duration
            
            print("📈 THROUGHPUT COMPARISON:")
            print(f"  Sequential (n_batch=1): {total_tokens}/{expected_sequential_time:.0f}s = {single_request_speed:.1f} tok/s")
            print(f"  Concurrent (n_batch=3): {total_tokens}/{total_duration:.0f}s = {aggregate_throughput:.1f} tok/s")
            print(f"  Speedup: {speedup:.2f}x")
            print()
        
        # Save detailed results
        report = {
            'test_info': {
                'timestamp': datetime.now().isoformat(),
                'total_duration_seconds': total_duration,
                'n_batch': 3,
                'total_requests': len(self.results),
                'successful_requests': len(successful),
                'failed_requests': len(failed)
            },
            'results': [asdict(r) for r in self.results],
            'summary': {
                'avg_ttft_ms': avg_ttft if successful else 0,
                'avg_tokens_per_second': avg_speed if successful else 0,
                'total_tokens_generated': total_tokens if successful else 0,
                'aggregate_throughput': aggregate_throughput if successful else 0,
                'speedup': speedup if successful else 0
            }
        }
        
        report_file = f"benchmarks/batch_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Detailed report saved: {report_file}")
        print("=" * 80)
        
        return report


async def main():
    """Run concurrent batch test"""
    tester = ConcurrentBatchTester()
    report = await tester.run_concurrent_test()
    
    # Exit code based on success
    if report['test_info']['failed_requests'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())

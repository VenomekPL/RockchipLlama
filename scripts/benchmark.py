#!/usr/bin/env python3
"""
Benchmark tool for RockchipLlama API server.
Measures performance metrics: TTFT (Time To First Token), tokens/sec, processing speed.
Runs tests from benchmark_prompts.json and generates comprehensive performance reports.
"""

import json
import time
import requests
import sys
import statistics
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
import argparse


@dataclass
class PerformanceMetrics:
    """Metrics for a single inference request"""
    prompt_id: str
    prompt_name: str
    prompt_length: int
    
    # Timing metrics
    ttft_ms: float  # Time to first token
    total_time_ms: float
    prefill_time_ms: float = 0.0
    generate_time_ms: float = 0.0
    
    # Token metrics
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    
    # Speed metrics
    tokens_per_second: float = 0.0
    input_tokens_per_second: float = 0.0
    
    # Memory
    memory_usage_mb: float = 0.0
    
    # Content
    prompt_text: str = ""  # The actual prompt
    response_text: str = ""  # The actual response
    success: bool = True
    error_message: str = ""
    
    def __post_init__(self):
        """Calculate derived metrics"""
        self.total_tokens = self.input_tokens + self.output_tokens
        
        # Calculate generation speed based on generation time (excluding prefill)
        # If generate_time_ms is available (from RKLLM), use it.
        # Otherwise, use total_time - ttft.
        gen_time = self.generate_time_ms
        if gen_time <= 0 and self.total_time_ms > 0:
             gen_time = self.total_time_ms - self.ttft_ms
             
        if gen_time > 0 and self.output_tokens > 0:
            self.tokens_per_second = (self.output_tokens / gen_time) * 1000
        
        if self.prefill_time_ms > 0 and self.input_tokens > 0:
            self.input_tokens_per_second = (self.input_tokens / self.prefill_time_ms) * 1000


@dataclass
class BenchmarkSummary:
    """Summary statistics across all benchmark runs"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    
    # Timing statistics
    avg_ttft_ms: float
    min_ttft_ms: float
    max_ttft_ms: float
    median_ttft_ms: float
    
    avg_total_time_ms: float
    min_total_time_ms: float
    max_total_time_ms: float
    
    # Token statistics
    avg_tokens_per_second: float
    min_tokens_per_second: float
    max_tokens_per_second: float
    median_tokens_per_second: float
    
    avg_input_tokens_per_second: float
    
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    
    # Memory
    avg_memory_mb: float
    max_memory_mb: float
    
    # Metadata
    model_name: str
    timestamp: str
    duration_seconds: float


class BenchmarkRunner:
    """Runs benchmark tests against the RockchipLlama API"""
    
    def __init__(self, base_url: str = "http://localhost:8021", timeout: int = 300):
        self.base_url = base_url
        self.timeout = timeout
        self.results: List[PerformanceMetrics] = []
        
    def load_prompts(self, prompts_file: str = "config/benchmark_prompts.json") -> Dict[str, Any]:
        """Load benchmark prompts from JSON file"""
        try:
            with open(prompts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Prompts file '{prompts_file}' not found!")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in prompts file: {e}")
            sys.exit(1)
    
    def check_model_loaded(self) -> Optional[str]:
        """Check if a model is loaded, return model name or None"""
        try:
            response = requests.get(f"{self.base_url}/v1/models/loaded", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("loaded") and data.get("model_name"):
                    return data["model_name"]
            return None
        except Exception as e:
            print(f"Error checking model status: {e}")
            return None
    
    def load_model(self, model_name: str, max_context_len: int = 512, num_npu_core: int = 3) -> bool:
        """Load a model for benchmarking"""
        print(f"\n🔄 Loading model: {model_name}")
        try:
            response = requests.post(
                f"{self.base_url}/v1/models/load",
                json={
                    "model": model_name,
                    "max_context_len": max_context_len,
                    "num_npu_core": num_npu_core
                },
                timeout=self.timeout
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"✅ Model loaded successfully!")
                    print(f"⏳ Waiting 5 seconds for model to stabilize...")
                    time.sleep(5)  # Give model time to fully initialize
                    return True
            print(f"❌ Failed to load model: {response.text}")
            return False
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def run_single_inference(self, prompt: str, prompt_id: str, prompt_name: str, 
                            temperature: float = 0.7, max_tokens: int = 2048) -> PerformanceMetrics:
        """Run a single inference and collect metrics"""
        
        metrics = PerformanceMetrics(
            prompt_id=prompt_id,
            prompt_name=prompt_name,
            prompt_length=len(prompt),
            prompt_text=prompt,  # Store the actual prompt
            ttft_ms=0.0,
            total_time_ms=0.0
        )
        
        try:
            # Start total timer
            start_time = time.perf_counter()
            first_token_time = None
            
            # Make streaming request
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": "current",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True
                },
                stream=True,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                metrics.success = False
                metrics.error_message = f"HTTP {response.status_code}: {response.text}"
                return metrics
            
            # Process streaming response
            response_chunks = []
            chunk_count = 0
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]  # Remove 'data: ' prefix
                        
                        if data_str == '[DONE]':
                            break
                        
                        try:
                            chunk_data = json.loads(data_str)
                            
                            # Record time to first token
                            if first_token_time is None and chunk_count == 0:
                                first_token_time = time.perf_counter()
                                metrics.ttft_ms = (first_token_time - start_time) * 1000
                            
                            # Extract content
                            choices = chunk_data.get('choices', [])
                            if choices:
                                delta = choices[0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    response_chunks.append(content)
                            
                            # Extract performance stats from usage (if available)
                            usage = chunk_data.get('usage', {})
                            if usage:
                                metrics.input_tokens = usage.get('prompt_tokens', metrics.input_tokens)
                                metrics.output_tokens = usage.get('completion_tokens', metrics.output_tokens)
                                
                                # Extract RKLLM perf stats if available
                                if 'prefill_time_ms' in usage:
                                    metrics.prefill_time_ms = usage['prefill_time_ms']
                                    # metrics.ttft_ms = usage['prefill_time_ms']  # Prefer measured TTFT
                                if 'generate_time_ms' in usage:
                                    metrics.generate_time_ms = usage['generate_time_ms']
                                if 'prefill_tokens' in usage:
                                    metrics.input_tokens = usage['prefill_tokens']
                                if 'generate_tokens' in usage:
                                    metrics.output_tokens = usage['generate_tokens']
                                if 'memory_usage_mb' in usage:
                                    metrics.memory_usage_mb = usage['memory_usage_mb']
                            
                            chunk_count += 1
                            
                        except json.JSONDecodeError as e:
                            print(f"⚠️ JSON decode error: {e} | Line: {line[:100]}...")
                            continue
            
            # End timer
            end_time = time.perf_counter()
            metrics.total_time_ms = (end_time - start_time) * 1000
            
            # If we never got first token time, use total time
            if metrics.ttft_ms == 0:
                metrics.ttft_ms = metrics.total_time_ms
            
            # Calculate generation time only if not provided by RKLLM perf stats
            # IMPORTANT: If RKLLM stats are missing, we fallback to client-side measurement
            if metrics.generate_time_ms == 0:
                metrics.generate_time_ms = metrics.total_time_ms - metrics.ttft_ms
            
            # Store response
            metrics.response_text = ''.join(response_chunks)
            
            # Estimate tokens if not provided (rough approximation: 4 chars per token)
            if metrics.input_tokens == 0:
                metrics.input_tokens = len(prompt) // 4
            if metrics.output_tokens == 0:
                # If we have response text, use a better approximation or count chunks if they were single tokens
                # For now, fallback to char length / 4 if no usage stats
                metrics.output_tokens = len(metrics.response_text) // 4
            
            # Recalculate derived metrics
            metrics.__post_init__()
            
        except requests.Timeout:
            metrics.success = False
            metrics.error_message = "Request timed out"
        except Exception as e:
            metrics.success = False
            metrics.error_message = str(e)
        
        return metrics
    
    def run_benchmark_suite(self, test_type: str = "performance", num_runs: int = 1) -> List[PerformanceMetrics]:
        """Run a suite of benchmark tests"""
        
        prompts_data = self.load_prompts()
        
        if test_type == "performance":
            tests = prompts_data.get("performance_tests", {}).get("tests", [])
        elif test_type == "quality":
            tests = prompts_data.get("quality_tests", {}).get("tests", [])
        else:
            print(f"Unknown test type: {test_type}")
            return []
        
        if not tests:
            print(f"No tests found for type: {test_type}")
            return []
        
        results = []
        total_tests = len(tests) * num_runs
        
        print(f"\n{'='*80}")
        print(f"🚀 Running {test_type.upper()} benchmark suite")
        print(f"   Tests: {len(tests)} prompts × {num_runs} run(s) = {total_tests} total inferences")
        print(f"{'='*80}\n")
        
        test_num = 0
        for run in range(num_runs):
            if num_runs > 1:
                print(f"\n{'─'*80}")
                print(f"📊 Run {run + 1}/{num_runs}")
                print(f"{'─'*80}\n")
            
            for test in tests:
                test_num += 1
                test_id = test.get('id', f'test_{test_num}')
                test_name = test.get('name', 'Unnamed Test')
                prompt = test.get('prompt', '')
                max_tokens = test.get('max_tokens', 2048)
                
                print(f"[{test_num}/{total_tests}] Testing: {test_name} (ID: {test_id})")
                print(f"   Prompt length: {len(prompt)} chars")
                
                metrics = self.run_single_inference(prompt, test_id, test_name, max_tokens=max_tokens)
                results.append(metrics)
                
                if metrics.success:
                    print(f"   ✅ Success!")
                    print(f"      TTFT: {metrics.ttft_ms:.2f} ms")
                    print(f"      Total time: {metrics.total_time_ms:.2f} ms")
                    print(f"      Tokens/sec: {metrics.tokens_per_second:.2f}")
                    print(f"      Output: {len(metrics.response_text)} chars ({metrics.output_tokens} tokens)")
                else:
                    print(f"   ❌ Failed: {metrics.error_message}")
                
                print()
        
        return results
    
    def calculate_summary(self, results: List[PerformanceMetrics], model_name: str, 
                         duration: float) -> BenchmarkSummary:
        """Calculate summary statistics from results"""
        
        successful = [r for r in results if r.success]
        
        if not successful:
            # Return empty summary if no successful requests
            return BenchmarkSummary(
                total_requests=len(results),
                successful_requests=0,
                failed_requests=len(results),
                avg_ttft_ms=0, min_ttft_ms=0, max_ttft_ms=0, median_ttft_ms=0,
                avg_total_time_ms=0, min_total_time_ms=0, max_total_time_ms=0,
                avg_tokens_per_second=0, min_tokens_per_second=0, max_tokens_per_second=0,
                median_tokens_per_second=0, avg_input_tokens_per_second=0,
                total_input_tokens=0, total_output_tokens=0, total_tokens=0,
                avg_memory_mb=0, max_memory_mb=0,
                model_name=model_name,
                timestamp=datetime.now().isoformat(),
                duration_seconds=duration
            )
        
        ttfts = [r.ttft_ms for r in successful]
        total_times = [r.total_time_ms for r in successful]
        tps = [r.tokens_per_second for r in successful if r.tokens_per_second > 0]
        input_tps = [r.input_tokens_per_second for r in successful if r.input_tokens_per_second > 0]
        memories = [r.memory_usage_mb for r in successful if r.memory_usage_mb > 0]
        
        return BenchmarkSummary(
            total_requests=len(results),
            successful_requests=len(successful),
            failed_requests=len(results) - len(successful),
            
            avg_ttft_ms=statistics.mean(ttfts) if ttfts else 0,
            min_ttft_ms=min(ttfts) if ttfts else 0,
            max_ttft_ms=max(ttfts) if ttfts else 0,
            median_ttft_ms=statistics.median(ttfts) if ttfts else 0,
            
            avg_total_time_ms=statistics.mean(total_times) if total_times else 0,
            min_total_time_ms=min(total_times) if total_times else 0,
            max_total_time_ms=max(total_times) if total_times else 0,
            
            avg_tokens_per_second=statistics.mean(tps) if tps else 0,
            min_tokens_per_second=min(tps) if tps else 0,
            max_tokens_per_second=max(tps) if tps else 0,
            median_tokens_per_second=statistics.median(tps) if tps else 0,
            
            avg_input_tokens_per_second=statistics.mean(input_tps) if input_tps else 0,
            
            total_input_tokens=sum(r.input_tokens for r in successful),
            total_output_tokens=sum(r.output_tokens for r in successful),
            total_tokens=sum(r.total_tokens for r in successful),
            
            avg_memory_mb=statistics.mean(memories) if memories else 0,
            max_memory_mb=max(memories) if memories else 0,
            
            model_name=model_name,
            timestamp=datetime.now().isoformat(),
            duration_seconds=duration
        )
    
    def print_summary(self, summary: BenchmarkSummary):
        """Print benchmark summary in a formatted way"""
        
        print(f"\n{'='*80}")
        print(f"📊 BENCHMARK SUMMARY")
        print(f"{'='*80}\n")
        
        print(f"Model: {summary.model_name}")
        print(f"Timestamp: {summary.timestamp}")
        print(f"Duration: {summary.duration_seconds:.2f} seconds")
        print()
        
        print(f"Requests:")
        print(f"  Total: {summary.total_requests}")
        print(f"  Successful: {summary.successful_requests} ✅")
        print(f"  Failed: {summary.failed_requests} ❌")
        print()
        
        if summary.successful_requests > 0:
            print(f"Time to First Token (TTFT):")
            print(f"  Average: {summary.avg_ttft_ms:.2f} ms")
            print(f"  Median: {summary.median_ttft_ms:.2f} ms")
            print(f"  Min: {summary.min_ttft_ms:.2f} ms")
            print(f"  Max: {summary.max_ttft_ms:.2f} ms")
            print()
            
            print(f"Total Inference Time:")
            print(f"  Average: {summary.avg_total_time_ms:.2f} ms ({summary.avg_total_time_ms/1000:.2f} sec)")
            print(f"  Min: {summary.min_total_time_ms:.2f} ms")
            print(f"  Max: {summary.max_total_time_ms:.2f} ms")
            print()
            
            print(f"Generation Speed (Tokens/Second):")
            print(f"  Average: {summary.avg_tokens_per_second:.2f} tokens/sec")
            print(f"  Median: {summary.median_tokens_per_second:.2f} tokens/sec")
            print(f"  Min: {summary.min_tokens_per_second:.2f} tokens/sec")
            print(f"  Max: {summary.max_tokens_per_second:.2f} tokens/sec")
            print()
            
            if summary.avg_input_tokens_per_second > 0:
                print(f"Input Processing Speed:")
                print(f"  Average: {summary.avg_input_tokens_per_second:.2f} tokens/sec")
                print()
            
            print(f"Token Statistics:")
            print(f"  Total Input Tokens: {summary.total_input_tokens:,}")
            print(f"  Total Output Tokens: {summary.total_output_tokens:,}")
            print(f"  Total Tokens: {summary.total_tokens:,}")
            print(f"  Avg Input/Request: {summary.total_input_tokens/summary.successful_requests:.1f}")
            print(f"  Avg Output/Request: {summary.total_output_tokens/summary.successful_requests:.1f}")
            print()
            
            if summary.avg_memory_mb > 0:
                print(f"Memory Usage:")
                print(f"  Average: {summary.avg_memory_mb:.2f} MB")
                print(f"  Max: {summary.max_memory_mb:.2f} MB")
                print()
        
        print(f"{'='*80}\n")
    
    def save_results(self, results: List[PerformanceMetrics], summary: BenchmarkSummary, 
                    output_file: str = "benchmark_results.json"):
        """Save detailed results to JSON file"""
        
        output = {
            "summary": asdict(summary),
            "detailed_results": [asdict(r) for r in results]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Detailed results saved to: {output_file}")

    def save_markdown_report(self, results: List[PerformanceMetrics], summary: BenchmarkSummary, 
                           output_file: str = None):
        """Save results to a Markdown report"""
        if output_file is None:
            # Default to replacing .json with .md, or appending .md
            if summary.model_name:
                output_file = f"benchmarks/benchmark_report_{summary.model_name}.md"
            else:
                output_file = "benchmarks/benchmark_report.md"
            
        with open(output_file, 'w', encoding='utf-8') as f:
            # Header
            f.write(f"# 📊 Benchmark Report: {summary.model_name}\n\n")
            f.write(f"**Date:** {summary.timestamp}\n")
            f.write(f"**Duration:** {summary.duration_seconds:.2f} seconds\n\n")
            
            # Summary Section
            f.write("## 📈 Performance Summary\n\n")
            f.write("| Metric | Value |\n")
            f.write("| :--- | :--- |\n")
            f.write(f"| **Total Requests** | {summary.total_requests} |\n")
            f.write(f"| **Successful** | {summary.successful_requests} ✅ |\n")
            f.write(f"| **Failed** | {summary.failed_requests} ❌ |\n")
            f.write(f"| **Avg Generation Speed** | **{summary.avg_tokens_per_second:.2f} tokens/sec** |\n")
            f.write(f"| **Avg TTFT** | {summary.avg_ttft_ms:.2f} ms |\n")
            f.write(f"| **Avg Total Time** | {summary.avg_total_time_ms:.2f} ms |\n")
            f.write(f"| **Total Output Tokens** | {summary.total_output_tokens:,} |\n")
            f.write(f"| **Avg Memory Usage** | {summary.avg_memory_mb:.2f} MB |\n\n")
            
            # Detailed Results
            f.write("## 📝 Detailed Results\n\n")
            
            for i, res in enumerate(results, 1):
                icon = "✅" if res.success else "❌"
                f.write(f"### {i}. {res.prompt_name} ({res.prompt_id}) {icon}\n\n")
                
                # Metrics Table
                f.write("| Metric | Value |\n")
                f.write("| :--- | :--- |\n")
                f.write(f"| **Status** | {'Success' if res.success else 'Failed'} |\n")
                f.write(f"| **TTFT** | {res.ttft_ms:.2f} ms |\n")
                f.write(f"| **Total Time** | {res.total_time_ms:.2f} ms |\n")
                f.write(f"| **Speed** | {res.tokens_per_second:.2f} t/s |\n")
                f.write(f"| **Input/Output** | {res.input_tokens} / {res.output_tokens} tokens |\n\n")
                
                if not res.success:
                    f.write(f"**Error:** `{res.error_message}`\n\n")
                    continue
                
                # Prompt
                f.write("#### 📥 Prompt\n")
                f.write("```text\n")
                f.write(res.prompt_text.strip())
                f.write("\n```\n\n")
                
                # Response
                f.write("#### 📤 Response\n")
                
                # Process thinking tags for collapsible view
                response_text = res.response_text.strip()
                if "<think>" in response_text and "</think>" in response_text:
                    response_text = response_text.replace("<think>", "<details><summary>Thinking Process</summary>\n\n")
                    response_text = response_text.replace("</think>", "\n</details>\n\n")
                
                f.write(f"{response_text}\n\n")
                
                f.write("---\n\n")
                
        print(f"📄 Markdown report saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark RockchipLlama API server performance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run performance tests (5 quick prompts)
  python benchmark.py --type performance
  
  # Run quality tests (5 detailed prompts)
  python benchmark.py --type quality
  
  # Run all tests multiple times
  python benchmark.py --type all --runs 3
  
  # Test specific model
  python benchmark.py --model google_gemma-3-270m-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588
  
  # Save detailed results
  python benchmark.py --output my_benchmark.json
        """
    )
    
    # Generate timestamped default filename
    timestamp = int(time.time())
    default_output = f'benchmarks/benchmark_results_{timestamp}.json'

    parser.add_argument('--url', default='http://localhost:8021',
                       help='Base URL of the API server (default: http://localhost:8021)')
    parser.add_argument('--type', choices=['performance', 'quality', 'all'], default='all',
                       help='Type of benchmark to run (default: all)')
    parser.add_argument('--runs', type=int, default=1,
                       help='Number of times to run each test (default: 1)')
    parser.add_argument('--model', type=str, default=None,
                       help='Model to load before benchmarking (optional, uses currently loaded model if not specified)')
    parser.add_argument('--output', type=str, default=None,
                       help=f'Output file for detailed results (default: {default_output})')
    parser.add_argument('--max-tokens', type=int, default=-1,
                       help='Maximum tokens to generate per request (default: -1 for unbound)')
    parser.add_argument('--timeout', type=int, default=300,
                       help='Request timeout in seconds (default: 300)')
    
    args = parser.parse_args()
    
    # Set default output if not provided
    if args.output is None:
        args.output = default_output
    
    runner = BenchmarkRunner(base_url=args.url, timeout=args.timeout)
    
    # Check or load model
    current_model = runner.check_model_loaded()
    
    if args.model:
        if not runner.load_model(args.model):
            print("❌ Failed to load specified model. Exiting.")
            sys.exit(1)
        model_name = args.model
    elif current_model:
        print(f"✅ Using currently loaded model: {current_model}")
        model_name = current_model
    else:
        print("❌ No model loaded and no model specified. Please:")
        print("   1. Load a model via API: POST /v1/models/load")
        print("   2. Or specify a model: python benchmark.py --model <model_name>")
        sys.exit(1)
    
    # Run benchmarks
    start_time = time.time()
    all_results = []
    
    if args.type in ['performance', 'all']:
        results = runner.run_benchmark_suite('performance', num_runs=args.runs)
        all_results.extend(results)
    
    if args.type in ['quality', 'all']:
        results = runner.run_benchmark_suite('quality', num_runs=args.runs)
        all_results.extend(results)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Calculate and display summary
    summary = runner.calculate_summary(all_results, model_name, duration)
    runner.print_summary(summary)
    
    # Save results
    runner.save_results(all_results, summary, args.output)
    
    # Save markdown report
    md_output = args.output.replace('.json', '.md')
    runner.save_markdown_report(all_results, summary, md_output)
    
    # Compare with expected performance (RK3588)
    if summary.successful_requests > 0:
        print(f"📈 Performance Comparison (RK3588 w8a8 models):")
        print(f"   Your result: {summary.avg_tokens_per_second:.2f} tokens/sec")
        print(f"   Expected ranges:")
        print(f"     • Qwen3-0.6B: ~32 tokens/sec")
        print(f"     • Qwen2-0.5B: ~42 tokens/sec")
        print(f"     • MiniCPM4-0.5B: ~45 tokens/sec")
        print(f"     • TinyLLAMA-1.1B: ~24 tokens/sec")
        print()


if __name__ == "__main__":
    main()

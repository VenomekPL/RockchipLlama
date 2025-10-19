#!/usr/bin/env python3
"""
Full benchmark tool with response capture for quality comparison.
Measures performance AND captures full responses to markdown for human review.
"""

import json
import time
import requests
import sys
import os
import statistics
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import argparse
import random
import string

# Add parent directory to path to import benchmark module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from benchmark import BenchmarkRunner, PerformanceMetrics, BenchmarkSummary


class FullBenchmarkRunner(BenchmarkRunner):
    """Extended benchmark runner that captures responses to markdown"""
    
    def __init__(self, base_url: str = "http://localhost:8080", timeout: int = 300, 
                 output_dir: str = "benchmarks"):
        super().__init__(base_url, timeout)
        self.output_dir = output_dir
        self.markdown_content = []
        self.current_model_name = None  # Store current model for filename
        
    def generate_filename(self, model_name: str) -> str:
        """Generate benchmark filename: benchmark_modelname_YYYYMMDD_nonce.md"""
        date_str = datetime.now().strftime("%Y%m%d")
        nonce = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        # Clean model name for filename (remove special chars)
        clean_name = model_name.replace('-', '_').replace('.', '_')
        # Shorten if too long
        if len(clean_name) > 30:
            clean_name = clean_name[:30]
        return f"benchmark_{clean_name}_{date_str}_{nonce}.md"
    
    def add_markdown_header(self, model_name: str):
        """Add markdown header for a model"""
        self.markdown_content.append(f"\n# Benchmark Results: {model_name}\n")
        self.markdown_content.append(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        self.markdown_content.append(f"**Model**: `{model_name}`\n")
        self.markdown_content.append(f"\n---\n")
    
    def add_markdown_summary(self, summary: BenchmarkSummary):
        """Add performance summary to markdown"""
        self.markdown_content.append(f"\n## Performance Summary\n\n")
        self.markdown_content.append(f"| Metric | Value |\n")
        self.markdown_content.append(f"|--------|-------|\n")
        self.markdown_content.append(f"| Total Requests | {summary.total_requests} |\n")
        self.markdown_content.append(f"| Successful | {summary.successful_requests} ✅ |\n")
        self.markdown_content.append(f"| Failed | {summary.failed_requests} ❌ |\n")
        self.markdown_content.append(f"| Avg TTFT | {summary.avg_ttft_ms:.2f} ms |\n")
        self.markdown_content.append(f"| Avg Tokens/sec | {summary.avg_tokens_per_second:.2f} |\n")
        self.markdown_content.append(f"| Total Tokens | {summary.total_tokens:,} |\n")
        self.markdown_content.append(f"| Duration | {summary.duration_seconds:.2f} sec |\n")
        self.markdown_content.append(f"\n---\n")
    
    def add_test_result(self, metrics: PerformanceMetrics, test_num: int):
        """Add individual test result to markdown"""
        self.markdown_content.append(f"\n## Test {test_num}: {metrics.prompt_name}\n")
        self.markdown_content.append(f"\n**ID**: `{metrics.prompt_id}`\n")
        
        # Performance metrics
        self.markdown_content.append(f"\n### Performance Metrics\n\n")
        self.markdown_content.append(f"| Metric | Value |\n")
        self.markdown_content.append(f"|--------|-------|\n")
        self.markdown_content.append(f"| TTFT | {metrics.ttft_ms:.2f} ms |\n")
        self.markdown_content.append(f"| Total Time | {metrics.total_time_ms:.2f} ms |\n")
        self.markdown_content.append(f"| Tokens/sec | {metrics.tokens_per_second:.2f} |\n")
        self.markdown_content.append(f"| Input Tokens | {metrics.input_tokens} |\n")
        self.markdown_content.append(f"| Output Tokens | {metrics.output_tokens} |\n")
        
        # Prompt
        self.markdown_content.append(f"\n### Prompt\n\n")
        self.markdown_content.append(f"```\n")
        # Use prompt_text field (not response_text!)
        prompt_text = metrics.prompt_text if hasattr(metrics, 'prompt_text') else ""
        prompt_preview = prompt_text[:500] if len(prompt_text) > 500 else prompt_text
        self.markdown_content.append(f"{prompt_preview}\n")
        if len(prompt_text) > 500:
            self.markdown_content.append(f"... (truncated)\n")
        self.markdown_content.append(f"```\n")
        
        # Response
        if metrics.success:
            self.markdown_content.append(f"\n### Response\n\n")
            self.markdown_content.append(f"```\n")
            # Use response_text for the actual response
            self.markdown_content.append(f"{metrics.response_text}\n")
            self.markdown_content.append(f"```\n")
        else:
            self.markdown_content.append(f"\n### Error\n\n")
            self.markdown_content.append(f"```\n")
            self.markdown_content.append(f"{metrics.error_message}\n")
            self.markdown_content.append(f"```\n")
        
        self.markdown_content.append(f"\n---\n")
    
    def save_markdown(self, filename: str):
        """Save accumulated markdown content to file"""
        filepath = os.path.join(self.output_dir, filename)
        os.makedirs(self.output_dir, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(''.join(self.markdown_content))
        
        print(f"\n📄 Benchmark report saved to: {filepath}")
        return filepath
    
    def run_full_benchmark(self, model_name: str, max_context_len: int = 16384, 
                          num_npu_core: int = 3) -> tuple:
        """Run complete benchmark with response capture"""
        
        print(f"\n{'='*80}")
        print(f"🚀 FULL BENCHMARK WITH RESPONSE CAPTURE")
        print(f"{'='*80}\n")
        
        # Load model
        print(f"📦 Loading model: {model_name}")
        if not self.load_model(model_name, max_context_len, num_npu_core):
            print(f"❌ Failed to load model")
            return None, None
        
        # Add header to markdown
        self.add_markdown_header(model_name)
        
        # Run all tests
        start_time = time.time()
        
        print(f"\n🧪 Running all tests (10 prompts)...")
        all_results = []
        
        # Performance tests
        perf_results = self.run_benchmark_suite("performance", num_runs=1)
        all_results.extend(perf_results)
        
        # Quality tests  
        qual_results = self.run_benchmark_suite("quality", num_runs=1)
        all_results.extend(qual_results)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate summary
        summary = self.calculate_summary(all_results, model_name, duration)
        
        # Add summary to markdown
        self.add_markdown_summary(summary)
        
        # Add individual test results
        for i, result in enumerate(all_results, 1):
            self.add_test_result(result, i)
        
        return all_results, summary


def main():
    parser = argparse.ArgumentParser(
        description="Full benchmark with response capture for quality comparison",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Benchmark single model with max context
  python scripts/benchmark_full.py --model google_gemma-3-270m-w8a8-opt0-hybrid0-npu3-ctx16384-rk3588
  
  # Benchmark all available models
  python scripts/benchmark_full.py --all-models
  
  # Custom output directory
  python scripts/benchmark_full.py --model <model> --output-dir my_benchmarks
        """
    )
    
    parser.add_argument('--url', default='http://localhost:8080',
                       help='Base URL of the API server (default: http://localhost:8080)')
    parser.add_argument('--model', type=str, default=None,
                       help='Model to benchmark (if not specified, will prompt for selection)')
    parser.add_argument('--all-models', action='store_true',
                       help='Benchmark all available models')
    parser.add_argument('--max-context', type=int, default=16384,
                       help='Maximum context length (default: 16384)')
    parser.add_argument('--npu-cores', type=int, default=3,
                       help='Number of NPU cores (default: 3 for RK3588)')
    parser.add_argument('--output-dir', type=str, default='benchmarks',
                       help='Output directory for benchmark results (default: benchmarks)')
    parser.add_argument('--timeout', type=int, default=600,
                       help='Request timeout in seconds (default: 600)')
    
    args = parser.parse_args()
    
    runner = FullBenchmarkRunner(base_url=args.url, timeout=args.timeout, 
                                  output_dir=args.output_dir)
    
    # Get available models if needed
    if args.all_models or not args.model:
        print("📋 Fetching available models...")
        try:
            response = requests.get(f"{args.url}/v1/models/available", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                
                if not models:
                    print("❌ No models available")
                    sys.exit(1)
                
                print(f"\nFound {len(models)} model(s):")
                for i, model in enumerate(models, 1):
                    print(f"  {i}. {model['name']} ({model['size_mb']:.1f} MB)")
                
                if args.all_models:
                    model_names = [m['name'] for m in models]
                elif not args.model:
                    print(f"\nEnter model number (1-{len(models)}) or 'all' for all models:")
                    choice = input("> ").strip()
                    if choice.lower() == 'all':
                        model_names = [m['name'] for m in models]
                    else:
                        try:
                            idx = int(choice) - 1
                            if 0 <= idx < len(models):
                                model_names = [models[idx]['name']]
                            else:
                                print("❌ Invalid choice")
                                sys.exit(1)
                        except ValueError:
                            print("❌ Invalid input")
                            sys.exit(1)
            else:
                print(f"❌ Failed to fetch models: HTTP {response.status_code}")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Error fetching models: {e}")
            sys.exit(1)
    else:
        model_names = [args.model]
    
    # Run benchmarks for each model
    all_summaries = []
    markdown_files = []
    
    for i, model_name in enumerate(model_names, 1):
        print(f"\n{'='*80}")
        print(f"📊 Benchmarking Model {i}/{len(model_names)}: {model_name}")
        print(f"{'='*80}")
        
        # Create new runner for each model (fresh markdown content)
        runner = FullBenchmarkRunner(base_url=args.url, timeout=args.timeout,
                                      output_dir=args.output_dir)
        
        results, summary = runner.run_full_benchmark(
            model_name,
            max_context_len=args.max_context,
            num_npu_core=args.npu_cores
        )
        
        if summary:
            # Print summary to console
            runner.print_summary(summary)
            all_summaries.append((model_name, summary))
            
            # Save markdown report (include model name in filename)
            filename = runner.generate_filename(model_name)
            filepath = runner.save_markdown(filename)
            markdown_files.append(filepath)
            
            # Save JSON data
            json_filename = filename.replace('.md', '.json')
            json_filepath = os.path.join(args.output_dir, json_filename)
            runner.save_results(results, summary, json_filepath)
        
        # Unload model between tests
        if i < len(model_names):
            print(f"\n⏳ Unloading model...")
            try:
                requests.post(f"{args.url}/v1/models/unload", timeout=5)
                time.sleep(2)
            except:
                pass
    
    # Final summary
    print(f"\n{'='*80}")
    print(f"🎉 ALL BENCHMARKS COMPLETE")
    print(f"{'='*80}\n")
    
    print(f"Tested {len(model_names)} model(s):")
    for model_name, summary in all_summaries:
        print(f"\n📊 {model_name}:")
        print(f"   TTFT: {summary.avg_ttft_ms:.2f} ms")
        print(f"   Tokens/sec: {summary.avg_tokens_per_second:.2f}")
        print(f"   Success: {summary.successful_requests}/{summary.total_requests}")
    
    print(f"\n📁 Benchmark reports saved to: {args.output_dir}/")
    for filepath in markdown_files:
        print(f"   • {os.path.basename(filepath)}")
    
    print()


if __name__ == "__main__":
    main()

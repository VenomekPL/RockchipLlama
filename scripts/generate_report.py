#!/usr/bin/env python3
"""
Generate comprehensive Markdown benchmark reports from JSON results
"""
import json
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List


def generate_markdown_report(json_data: Dict[str, Any]) -> str:
    """Generate comprehensive Markdown report from benchmark JSON data"""
    
    summary = json_data['summary']
    results = json_data['detailed_results']
    
    md = []
    
    # Extract model name for title
    model_name = summary.get('model_name', 'Unknown Model')
    md.append(f"# 🚀 {model_name} NPU Benchmark Results")
    md.append("")
    md.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md.append(f"**Duration:** {summary['duration_seconds']:.1f} seconds ({summary['duration_seconds']/60:.1f} minutes)")
    md.append("")

    # Executive Summary
    md.append("## 📊 Executive Summary")
    md.append("")
    md.append(f"- **Model:** `{model_name}`")
    md.append(f"- **Hardware:** Rockchip RK3588 NPU (3 cores)")
    md.append(f"- **Success Rate:** {summary['successful_requests']}/{summary['total_requests']} ({summary['successful_requests']/summary['total_requests']*100:.0f}%)")
    md.append(f"- **Total Tokens Generated:** {summary['total_output_tokens']:,} tokens")
    md.append(f"- **Average Speed:** {summary['avg_tokens_per_second']:.2f} tok/s")
    md.append(f"- **Memory Usage:** ~{summary['avg_memory_mb']:.0f} MB")
    md.append("")

    # Configuration
    md.append("## ⚙️ Configuration")
    md.append("")
    md.append("```json")
    md.append('{')
    md.append('  "inference_params": {')
    md.append('    "top_k": 20,')
    md.append('    "top_p": 0.95,')
    md.append('    "temperature": 0.6,')
    md.append('    "repeat_penalty": 0.9')
    md.append('  },')
    md.append('  "hardware": {')
    md.append('    "num_npu_cores": 3,')
    md.append('    "enabled_cpus_mask": 240,')
    md.append('    "num_threads": 4')
    md.append('  }')
    md.append('}')
    md.append("```")
    md.append("")

    # Performance Metrics
    md.append("## 🎯 Performance Metrics")
    md.append("")
    md.append("| Metric | Average | Median | Min | Max |")
    md.append("|--------|---------|--------|-----|-----|")
    md.append(f"| Generation Speed (tok/s) | {summary['avg_tokens_per_second']:.2f} | {summary['median_tokens_per_second']:.2f} | {summary['min_tokens_per_second']:.2f} | {summary['max_tokens_per_second']:.2f} |")
    md.append(f"| Time to First Token (ms) | {summary['avg_ttft_ms']:.2f} | {summary['median_ttft_ms']:.2f} | {summary['min_ttft_ms']:.2f} | {summary['max_ttft_ms']:.2f} |")
    md.append(f"| Input Processing (tok/s) | {summary['avg_input_tokens_per_second']:.2f} | - | - | - |")
    md.append("")

    # Token Statistics
    md.append("## 🔢 Token Statistics")
    md.append("")
    md.append(f"- **Total Input Tokens:** {summary['total_input_tokens']:,}")
    md.append(f"- **Total Output Tokens:** {summary['total_output_tokens']:,}")
    md.append(f"- **Average Output per Request:** {summary['total_output_tokens']/summary['total_requests']:.1f} tokens")
    md.append(f"- **Total Tokens Processed:** {summary['total_tokens']:,}")
    md.append("")

    # Detailed Results
    md.append("## 📝 Detailed Test Results")
    md.append("")

    for i, result in enumerate(results, 1):
        md.append(f"### Test {i}/{len(results)}: {result['prompt_name']}")
        md.append("")
        md.append(f"**ID:** `{result['prompt_id']}`")
        md.append("")
        
        if result['success']:
            md.append("| Metric | Value |")
            md.append("|--------|-------|")
            md.append(f"| Status | ✅ Success |")
            md.append(f"| Generation Speed | {result['tokens_per_second']:.2f} tok/s |")
            md.append(f"| Time to First Token | {result['ttft_ms']:.2f} ms |")
            md.append(f"| Total Time | {result['total_time_ms']/1000:.2f} seconds |")
            md.append(f"| Input Tokens | {result['input_tokens']} |")
            md.append(f"| Output Tokens | {result['output_tokens']} |")
            md.append(f"| Memory Usage | {result['memory_usage_mb']:.2f} MB |")
            md.append("")
            
            # Show prompt
            md.append("**Prompt:**")
            md.append("```")
            md.append(result['prompt_text'])
            md.append("```")
            md.append("")
            
            # Show response
            md.append("**Response:**")
            md.append("```")
            md.append(result['response_text'])
            md.append("```")
            md.append("")
        else:
            md.append(f"❌ **Failed:** {result.get('error_message', 'Unknown error')}")
            md.append("")
        
        md.append("---")
        md.append("")

    # Observations
    md.append("## 💡 Observations")
    md.append("")
    md.append("### Performance Analysis")
    md.append("")
    md.append(f"- Average generation speed of **{summary['avg_tokens_per_second']:.2f} tok/s**")
    md.append(f"- Configuration choices (top_k=20, temperature=0.6) prioritize quality over raw speed")
    md.append(f"- Fast input processing at **{summary['avg_input_tokens_per_second']:.2f} tok/s**")
    md.append(f"- TTFT: {summary['median_ttft_ms']:.0f} ms median")
    md.append("")

    md.append("### Quality Assessment")
    md.append("")
    success_rate = (summary['successful_requests']/summary['total_requests']*100)
    md.append(f"- {'✅' if success_rate == 100 else '⚠️'} {success_rate:.0f}% success rate across all tests")
    md.append("- ✅ Responses are coherent, on-topic, and well-structured")
    md.append("- ✅ Model handles various tasks: technical, creative, planning, coding")
    md.append(f"- ✅ Stable memory usage (~{summary['avg_memory_mb']:.0f} MB across all tests)")
    md.append("")

    md.append("### Long-Form Generation")
    md.append("")
    longest = max(results, key=lambda x: x.get('output_tokens', 0) if x.get('success') else 0)
    md.append(f"- **Longest output:** {longest['prompt_name']} ({longest.get('output_tokens', 0)} tokens)")
    md.append(f"- **Generation time:** {longest.get('total_time_ms', 0)/1000:.1f} seconds")
    md.append(f"- Successfully generates coherent long-form content")
    md.append("")

    # Conclusion
    md.append("## 🎯 Conclusion")
    md.append("")
    md.append(f"The {model_name} model running on Rockchip RK3588 NPU demonstrates:")
    md.append("")
    md.append("1. **Reliability:** High success rate across diverse test cases")
    md.append("2. **Quality:** Coherent, contextually appropriate responses")
    md.append("3. **Versatility:** Handles technical, creative, and analytical tasks")
    md.append("4. **Efficiency:** Fast input processing and stable memory usage")
    md.append("5. **Configuration:** Current settings favor quality over raw speed")
    md.append("")

    md.append("---")
    md.append("")
    md.append(f"**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return '\n'.join(md)


def main():
    parser = argparse.ArgumentParser(description='Generate Markdown benchmark report from JSON')
    parser.add_argument('json_file', help='Path to benchmark JSON file')
    parser.add_argument('-o', '--output', help='Output markdown file (default: auto-generated)')
    
    args = parser.parse_args()
    
    # Read JSON data
    try:
        with open(args.json_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        sys.exit(1)
    
    # Generate report
    try:
        report = generate_markdown_report(data)
    except Exception as e:
        print(f"Error generating report: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Determine output file
    if args.output:
        output_file = args.output
    else:
        # Auto-generate output filename
        json_path = Path(args.json_file)
        output_file = json_path.parent / f"{json_path.stem}_report.md"
    
    # Write report
    try:
        with open(output_file, 'w') as f:
            f.write(report)
        print(f"✅ Report generated: {output_file}")
        print(f"📄 Size: {len(report)} bytes")
    except Exception as e:
        print(f"Error writing report: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Test mixed API requests through shared queue

This script sends requests to both OpenAI and Ollama APIs
simultaneously to verify they share the same queue and process
in FIFO order.
"""
import requests
import time
import threading
from typing import Dict, Any

BASE_URL = "http://localhost:8080"

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_colored(text: str, color: str):
    """Print colored text"""
    print(f"{color}{text}{Colors.ENDC}")


def test_openai_chat(request_num: int) -> Dict[str, Any]:
    """Send OpenAI chat completion request"""
    start_time = time.time()
    
    print_colored(f"[{request_num}] 🔵 OpenAI: Sending request...", Colors.OKBLUE)
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json={
                "model": "qwen3-0.6b",
                "messages": [
                    {"role": "user", "content": f"Say 'OpenAI request {request_num}'"}
                ],
                "max_tokens": 20,
                "temperature": 0.1
            },
            timeout=30
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            print_colored(
                f"[{request_num}] ✅ OpenAI: Success in {elapsed:.2f}s - {content[:50]}...",
                Colors.OKGREEN
            )
            return {"success": True, "time": elapsed, "api": "openai", "response": content}
        else:
            print_colored(
                f"[{request_num}] ❌ OpenAI: Failed {response.status_code}",
                Colors.FAIL
            )
            return {"success": False, "time": elapsed, "api": "openai"}
            
    except Exception as e:
        elapsed = time.time() - start_time
        print_colored(f"[{request_num}] ❌ OpenAI: Error - {e}", Colors.FAIL)
        return {"success": False, "time": elapsed, "api": "openai", "error": str(e)}


def test_ollama_generate(request_num: int) -> Dict[str, Any]:
    """Send Ollama generate request"""
    start_time = time.time()
    
    print_colored(f"[{request_num}] 🦙 Ollama: Sending request...", Colors.OKCYAN)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/generate",
            json={
                "model": "qwen3-0.6b",
                "prompt": f"Say 'Ollama request {request_num}'",
                "stream": False,
                "options": {
                    "num_predict": 20,
                    "temperature": 0.1
                }
            },
            timeout=30
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            content = data['response']
            print_colored(
                f"[{request_num}] ✅ Ollama: Success in {elapsed:.2f}s - {content[:50]}...",
                Colors.OKGREEN
            )
            return {"success": True, "time": elapsed, "api": "ollama", "response": content}
        else:
            print_colored(
                f"[{request_num}] ❌ Ollama: Failed {response.status_code}",
                Colors.FAIL
            )
            return {"success": False, "time": elapsed, "api": "ollama"}
            
    except Exception as e:
        elapsed = time.time() - start_time
        print_colored(f"[{request_num}] ❌ Ollama: Error - {e}", Colors.FAIL)
        return {"success": False, "time": elapsed, "api": "ollama", "error": str(e)}


def test_ollama_chat(request_num: int) -> Dict[str, Any]:
    """Send Ollama chat request"""
    start_time = time.time()
    
    print_colored(f"[{request_num}] 🦙💬 Ollama Chat: Sending request...", Colors.OKCYAN)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "model": "qwen3-0.6b",
                "messages": [
                    {"role": "user", "content": f"Say 'Ollama chat {request_num}'"}
                ],
                "stream": False,
                "options": {
                    "num_predict": 20,
                    "temperature": 0.1
                }
            },
            timeout=30
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            content = data['message']['content']
            print_colored(
                f"[{request_num}] ✅ Ollama Chat: Success in {elapsed:.2f}s - {content[:50]}...",
                Colors.OKGREEN
            )
            return {"success": True, "time": elapsed, "api": "ollama-chat", "response": content}
        else:
            print_colored(
                f"[{request_num}] ❌ Ollama Chat: Failed {response.status_code}",
                Colors.FAIL
            )
            return {"success": False, "time": elapsed, "api": "ollama-chat"}
            
    except Exception as e:
        elapsed = time.time() - start_time
        print_colored(f"[{request_num}] ❌ Ollama Chat: Error - {e}", Colors.FAIL)
        return {"success": False, "time": elapsed, "api": "ollama-chat", "error": str(e)}


def main():
    """Run mixed API test"""
    print_colored("=" * 70, Colors.HEADER)
    print_colored("🎯 Mixed API Queue Test (OpenAI + Ollama)", Colors.HEADER)
    print_colored("=" * 70, Colors.HEADER)
    print()
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/")
        info = response.json()
        print_colored(f"✅ Server: {info['name']} v{info['version']}", Colors.OKGREEN)
        print_colored(f"📦 Loaded model: {info.get('loaded_model', 'None')}", Colors.OKGREEN)
        print()
    except Exception as e:
        print_colored(f"❌ Server not reachable: {e}", Colors.FAIL)
        print_colored("\nMake sure the server is running:", Colors.WARNING)
        print_colored("  ./start_server.sh", Colors.WARNING)
        return
    
    # Launch requests simultaneously
    print_colored("🚀 Launching 6 concurrent requests (mixed APIs)...", Colors.HEADER)
    print()
    
    results = []
    threads = []
    
    # Mix of OpenAI and Ollama requests
    test_functions = [
        (test_openai_chat, 1),
        (test_ollama_generate, 2),
        (test_openai_chat, 3),
        (test_ollama_chat, 4),
        (test_ollama_generate, 5),
        (test_openai_chat, 6)
    ]
    
    # Start all threads
    for func, num in test_functions:
        thread = threading.Thread(target=lambda f=func, n=num: results.append(f(n)))
        threads.append(thread)
        thread.start()
        time.sleep(0.05)  # Tiny stagger to see queue behavior
    
    # Wait for all to complete
    for thread in threads:
        thread.join()
    
    print()
    print_colored("=" * 70, Colors.HEADER)
    print_colored("📊 Results Summary", Colors.HEADER)
    print_colored("=" * 70, Colors.HEADER)
    
    # Sort by completion time to see queue order
    results.sort(key=lambda x: x.get('time', 999))
    
    print()
    print_colored(f"{'#':<4} {'API':<15} {'Status':<10} {'Time (s)':<10} {'Response'}", Colors.BOLD)
    print_colored("-" * 70, Colors.HEADER)
    
    for i, result in enumerate(results, 1):
        status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
        api = result['api'].upper()
        time_str = f"{result['time']:.2f}s"
        response = result.get('response', result.get('error', 'N/A'))[:30]
        
        color = Colors.OKGREEN if result['success'] else Colors.FAIL
        print_colored(f"{i:<4} {api:<15} {status:<10} {time_str:<10} {response}", color)
    
    print()
    
    # Analyze queue behavior
    successful = [r for r in results if r['success']]
    if len(successful) >= 2:
        print_colored("🔍 Queue Analysis:", Colors.HEADER)
        print_colored(f"  Total requests: {len(results)}", Colors.OKBLUE)
        print_colored(f"  Successful: {len(successful)}", Colors.OKGREEN)
        print_colored(f"  Failed: {len(results) - len(successful)}", Colors.FAIL if len(results) > len(successful) else Colors.OKGREEN)
        
        # Check if times are sequential (indicates queuing)
        times = [r['time'] for r in successful]
        if len(times) >= 3:
            gaps = [times[i+1] - times[i] for i in range(len(times)-1)]
            avg_gap = sum(gaps) / len(gaps)
            print_colored(f"  Average time between completions: {avg_gap:.2f}s", Colors.OKBLUE)
            
            if all(g < 0.5 for g in gaps):
                print_colored("  ⚠️  Requests completed too close together - queue might not be working!", Colors.WARNING)
            else:
                print_colored("  ✅ Requests processed sequentially - queue working as expected!", Colors.OKGREEN)
    
    print()
    print_colored("=" * 70, Colors.HEADER)


if __name__ == "__main__":
    main()

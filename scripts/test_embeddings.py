#!/usr/bin/env python3
"""
Test script for embedding endpoints (OpenAI and Ollama)

Tests:
1. OpenAI single text embedding
2. OpenAI batch embeddings
3. Ollama single text embedding
4. Vector normalization verification
5. Dimension consistency
"""
import requests
import json
import math
import time

BASE_URL = "http://localhost:8080"
MODEL = "qwen3-0.6b-embedding"  # Dedicated embedding model

def print_header(title):
    """Print a formatted section header"""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print('=' * 70)

def verify_unit_vector(embedding):
    """Verify that embedding is a unit vector (L2 norm ≈ 1.0)"""
    norm = math.sqrt(sum(x * x for x in embedding))
    is_normalized = abs(norm - 1.0) < 0.01  # Allow 1% tolerance
    return is_normalized, norm

def test_openai_single_embedding():
    """Test OpenAI single text embedding"""
    print_header("TEST 1: OpenAI Single Embedding")
    
    url = f"{BASE_URL}/v1/embeddings"
    payload = {
        "model": MODEL,
        "input": "The quick brown fox jumps over the lazy dog"
    }
    
    print(f"📤 Request: POST {url}")
    print(f"   Input: {payload['input']}")
    
    start_time = time.time()
    response = requests.post(url, json=payload)
    elapsed_ms = (time.time() - start_time) * 1000
    
    print(f"⏱️  Response time: {elapsed_ms:.1f}ms")
    print(f"📊 Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"✅ Success!")
        print(f"   Model: {data['model']}")
        print(f"   Embedding count: {len(data['data'])}")
        print(f"   Dimensions: {len(data['data'][0]['embedding'])}")
        print(f"   Tokens: {data['usage']['prompt_tokens']}")
        
        # Verify normalization
        embedding = data['data'][0]['embedding']
        is_normalized, norm = verify_unit_vector(embedding)
        print(f"   Normalized: {'✅ Yes' if is_normalized else '❌ No'} (L2 norm: {norm:.6f})")
        
        # Show first 5 values
        print(f"   First 5 values: {embedding[:5]}")
        
        return True, len(embedding), embedding
    else:
        print(f"❌ Failed: {response.text}")
        return False, 0, None

def test_openai_batch_embeddings():
    """Test OpenAI batch embeddings"""
    print_header("TEST 2: OpenAI Batch Embeddings")
    
    url = f"{BASE_URL}/v1/embeddings"
    texts = [
        "Hello, world!",
        "Machine learning is fascinating",
        "The sky is blue"
    ]
    payload = {
        "model": MODEL,
        "input": texts
    }
    
    print(f"📤 Request: POST {url}")
    print(f"   Batch size: {len(texts)}")
    for i, text in enumerate(texts):
        print(f"   [{i}] {text}")
    
    start_time = time.time()
    response = requests.post(url, json=payload)
    elapsed_ms = (time.time() - start_time) * 1000
    
    print(f"⏱️  Response time: {elapsed_ms:.1f}ms ({elapsed_ms/len(texts):.1f}ms per text)")
    print(f"📊 Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"✅ Success!")
        print(f"   Model: {data['model']}")
        print(f"   Embeddings returned: {len(data['data'])}")
        
        dimensions = []
        for i, emb_data in enumerate(data['data']):
            embedding = emb_data['embedding']
            dim = len(embedding)
            dimensions.append(dim)
            is_normalized, norm = verify_unit_vector(embedding)
            
            print(f"   [{i}] Dimensions: {dim}, Normalized: {'✅' if is_normalized else '❌'} (norm: {norm:.6f})")
        
        # Check dimension consistency
        if len(set(dimensions)) == 1:
            print(f"   ✅ All embeddings have consistent dimensions: {dimensions[0]}")
            return True, dimensions[0]
        else:
            print(f"   ❌ Inconsistent dimensions: {dimensions}")
            return False, 0
    else:
        print(f"❌ Failed: {response.text}")
        return False, 0

def test_ollama_embedding():
    """Test Ollama embedding endpoint"""
    print_header("TEST 3: Ollama Embedding")
    
    url = f"{BASE_URL}/api/embed"
    payload = {
        "model": MODEL,
        "prompt": "What is the meaning of life?"
    }
    
    print(f"📤 Request: POST {url}")
    print(f"   Prompt: {payload['prompt']}")
    
    start_time = time.time()
    response = requests.post(url, json=payload)
    elapsed_ms = (time.time() - start_time) * 1000
    
    print(f"⏱️  Response time: {elapsed_ms:.1f}ms")
    print(f"📊 Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"✅ Success!")
        print(f"   Model: {data['model']}")
        print(f"   Dimensions: {len(data['embedding'])}")
        print(f"   Tokens: {data.get('prompt_eval_count', 'N/A')}")
        print(f"   Duration: {data.get('total_duration', 0) / 1_000_000:.1f}ms")
        
        # Verify normalization
        embedding = data['embedding']
        is_normalized, norm = verify_unit_vector(embedding)
        print(f"   Normalized: {'✅ Yes' if is_normalized else '❌ No'} (L2 norm: {norm:.6f})")
        
        # Show first 5 values
        print(f"   First 5 values: {embedding[:5]}")
        
        return True, len(embedding), embedding
    else:
        print(f"❌ Failed: {response.text}")
        return False, 0, None

def test_semantic_similarity(emb1, emb2, label1, label2):
    """Test semantic similarity using cosine similarity"""
    print_header(f"TEST 4: Semantic Similarity ({label1} vs {label2})")
    
    if emb1 is None or emb2 is None:
        print("⚠️  Skipping - embeddings not available")
        return
    
    # Cosine similarity (since vectors are normalized, this is just the dot product)
    similarity = sum(a * b for a, b in zip(emb1, emb2))
    
    print(f"   Cosine similarity: {similarity:.6f}")
    
    if similarity > 0.9:
        print(f"   ✅ High similarity (>{0.9})")
    elif similarity > 0.5:
        print(f"   ⚠️  Moderate similarity (0.5-0.9)")
    else:
        print(f"   ℹ️  Low similarity (<0.5)")

def main():
    """Run all embedding tests"""
    print("\n🔬 Embedding Endpoints Test Suite")
    print(f"   Target: {BASE_URL}")
    print(f"   Model: {MODEL}")
    
    # Test 1: OpenAI single
    success1, dim1, emb1 = test_openai_single_embedding()
    
    # Test 2: OpenAI batch
    success2, dim2 = test_openai_batch_embeddings()
    
    # Test 3: Ollama
    success3, dim3, emb3 = test_ollama_embedding()
    
    # Test 4: Semantic similarity (if we have embeddings)
    if success1 and success3:
        test_semantic_similarity(emb1, emb3, "OpenAI", "Ollama")
    
    # Summary
    print_header("SUMMARY")
    tests = [
        ("OpenAI Single Embedding", success1, dim1 if success1 else "N/A"),
        ("OpenAI Batch Embeddings", success2, dim2 if success2 else "N/A"),
        ("Ollama Embedding", success3, dim3 if success3 else "N/A")
    ]
    
    passed = sum(1 for _, success, _ in tests if success)
    total = len(tests)
    
    for name, success, dim in tests:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} - {name} (dim: {dim})")
    
    print(f"\n   {'=' * 66}")
    print(f"   Result: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"   🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"   ⚠️  SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    exit(main())

"""
Tests for embeddings API feature.

Tests cover:
- Pooling strategies (mean, cls, last)
- L2 normalization
- Adapter functions (OpenAI and Ollama embedding format conversion)
- Schema validation
"""
import math
import sys
import os
import pytest

# Add src to path to match the project's import style
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ============================================================================
# Pooling Strategy Tests
# ============================================================================

def _pool_embeddings(all_states, embd_size, num_tokens, strategy):
    """Replicate the pooling logic from rkllm_model.py get_embeddings()."""
    if strategy == "mean":
        embedding = [0.0] * embd_size
        for t in range(num_tokens):
            offset = t * embd_size
            for i in range(embd_size):
                embedding[i] += all_states[offset + i]
        embedding = [x / num_tokens for x in embedding]
    elif strategy == "cls":
        embedding = all_states[:embd_size]
    else:
        offset = (num_tokens - 1) * embd_size
        embedding = all_states[offset:offset + embd_size]
    return embedding


def _l2_normalize(embedding):
    """Replicate the normalization logic from rkllm_model.py get_embeddings()."""
    norm = math.sqrt(sum(x * x for x in embedding))
    if norm > 0:
        embedding = [x / norm for x in embedding]
    return embedding


class TestPoolingStrategies:
    """Test embedding pooling strategies."""

    # 3 tokens × 4 dimensions
    ALL_STATES = [
        1.0, 2.0, 3.0, 4.0,   # token 0 (CLS)
        5.0, 6.0, 7.0, 8.0,   # token 1
        9.0, 10.0, 11.0, 12.0  # token 2 (last)
    ]
    EMBD_SIZE = 4
    NUM_TOKENS = 3

    def test_last_pooling(self):
        result = _pool_embeddings(self.ALL_STATES, self.EMBD_SIZE, self.NUM_TOKENS, "last")
        assert result == [9.0, 10.0, 11.0, 12.0]

    def test_cls_pooling(self):
        result = _pool_embeddings(self.ALL_STATES, self.EMBD_SIZE, self.NUM_TOKENS, "cls")
        assert result == [1.0, 2.0, 3.0, 4.0]

    def test_mean_pooling(self):
        result = _pool_embeddings(self.ALL_STATES, self.EMBD_SIZE, self.NUM_TOKENS, "mean")
        expected = [5.0, 6.0, 7.0, 8.0]  # mean of each dimension
        assert result == expected

    def test_single_token_all_strategies_equal(self):
        """With a single token, all pooling strategies should return the same result."""
        states = [1.0, 2.0, 3.0]
        for strategy in ["mean", "cls", "last"]:
            result = _pool_embeddings(states, 3, 1, strategy)
            assert result == [1.0, 2.0, 3.0], f"Failed for strategy={strategy}"

    def test_unknown_strategy_defaults_to_last(self):
        result = _pool_embeddings(self.ALL_STATES, self.EMBD_SIZE, self.NUM_TOKENS, "unknown")
        assert result == [9.0, 10.0, 11.0, 12.0]


class TestL2Normalization:
    """Test L2 normalization of embeddings."""

    def test_unit_vector(self):
        embedding = [3.0, 4.0]
        result = _l2_normalize(embedding)
        assert abs(result[0] - 0.6) < 1e-6
        assert abs(result[1] - 0.8) < 1e-6

    def test_normalized_has_unit_length(self):
        embedding = [1.0, 2.0, 3.0, 4.0]
        result = _l2_normalize(embedding)
        length = math.sqrt(sum(x * x for x in result))
        assert abs(length - 1.0) < 1e-6

    def test_zero_vector_unchanged(self):
        embedding = [0.0, 0.0, 0.0]
        result = _l2_normalize(embedding)
        assert result == [0.0, 0.0, 0.0]

    def test_already_normalized(self):
        embedding = [1.0, 0.0, 0.0]
        result = _l2_normalize(embedding)
        assert abs(result[0] - 1.0) < 1e-6
        assert abs(result[1]) < 1e-6
        assert abs(result[2]) < 1e-6


# ============================================================================
# Adapter Tests
# ============================================================================

class TestOpenAIEmbeddingAdapters:
    """Test OpenAI embedding format conversion."""

    def test_single_text_to_internal(self):
        from api.adapters import openai_embedding_to_internal
        from api.schemas import EmbeddingRequest

        request = EmbeddingRequest(model="test-model", input="hello world")
        result = openai_embedding_to_internal(request)
        assert len(result) == 1
        assert result[0].prompt == "hello world"
        assert result[0].source_api == "openai"

    def test_batch_text_to_internal(self):
        from api.adapters import openai_embedding_to_internal
        from api.schemas import EmbeddingRequest

        request = EmbeddingRequest(model="test-model", input=["hello", "world"])
        result = openai_embedding_to_internal(request)
        assert len(result) == 2
        assert result[0].prompt == "hello"
        assert result[1].prompt == "world"

    def test_internal_to_openai_embedding(self):
        from api.adapters import internal_to_openai_embedding
        from models.inference_types import InferenceResponse

        responses = [
            InferenceResponse(embedding=[0.1, 0.2, 0.3], tokens_processed=5),
            InferenceResponse(embedding=[0.4, 0.5, 0.6], tokens_processed=3),
        ]
        result = internal_to_openai_embedding(responses, "test-model")
        assert result.object == "list"
        assert result.model == "test-model"
        assert len(result.data) == 2
        assert result.data[0].index == 0
        assert result.data[0].embedding == [0.1, 0.2, 0.3]
        assert result.data[1].index == 1
        assert result.usage.prompt_tokens == 8
        assert result.usage.total_tokens == 8


class TestOllamaEmbeddingAdapters:
    """Test Ollama embedding format conversion."""

    def test_ollama_to_internal(self):
        from api.adapters import ollama_embedding_to_internal
        from api.schemas import OllamaEmbeddingRequest

        request = OllamaEmbeddingRequest(model="test-model", prompt="hello world")
        result = ollama_embedding_to_internal(request)
        assert result.prompt == "hello world"
        assert result.source_api == "ollama"

    def test_internal_to_ollama_embedding(self):
        from api.adapters import internal_to_ollama_embedding
        from models.inference_types import InferenceResponse

        response = InferenceResponse(
            embedding=[0.1, 0.2, 0.3],
            tokens_processed=5,
            time_ms=100.0
        )
        result = internal_to_ollama_embedding(response, "test-model")
        assert result.model == "test-model"
        assert result.embedding == [0.1, 0.2, 0.3]
        assert result.prompt_eval_count == 5
        assert result.total_duration == 100_000_000  # ms to ns


# ============================================================================
# Schema Validation Tests
# ============================================================================

class TestEmbeddingSchemas:
    """Test embedding request/response schemas."""

    def test_openai_embedding_request_single_string(self):
        from api.schemas import EmbeddingRequest
        req = EmbeddingRequest(model="test", input="hello")
        assert req.input == "hello"
        assert req.encoding_format == "float"

    def test_openai_embedding_request_batch(self):
        from api.schemas import EmbeddingRequest
        req = EmbeddingRequest(model="test", input=["hello", "world"])
        assert isinstance(req.input, list)
        assert len(req.input) == 2

    def test_openai_embedding_response(self):
        from api.schemas import EmbeddingResponse, EmbeddingData, EmbeddingUsage
        resp = EmbeddingResponse(
            data=[EmbeddingData(embedding=[0.1, 0.2], index=0)],
            model="test",
            usage=EmbeddingUsage(prompt_tokens=3, total_tokens=3)
        )
        assert resp.object == "list"
        assert resp.data[0].object == "embedding"

    def test_ollama_embedding_request(self):
        from api.schemas import OllamaEmbeddingRequest
        req = OllamaEmbeddingRequest(model="test", prompt="hello")
        assert req.prompt == "hello"

    def test_ollama_embedding_response(self):
        from api.schemas import OllamaEmbeddingResponse
        resp = OllamaEmbeddingResponse(
            embedding=[0.1, 0.2],
            model="test",
            created_at="2025-01-01T00:00:00Z"
        )
        assert resp.embedding == [0.1, 0.2]


# ============================================================================
# Config Tests
# ============================================================================

class TestEmbeddingConfig:
    """Test embedding configuration in inference_config.json."""

    def test_config_has_embedding_model_section(self):
        import json
        config_path = os.path.join(
            os.path.dirname(__file__), '..', 'config', 'inference_config.json'
        )
        with open(config_path) as f:
            config = json.load(f)
        assert "embedding_model" in config
        emb = config["embedding_model"]
        assert "pooling_strategy" in emb
        assert emb["pooling_strategy"] in ("mean", "cls", "last")
        assert "normalize" in emb
        assert isinstance(emb["normalize"], bool)

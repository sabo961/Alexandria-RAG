"""
Tests for EmbeddingGenerator multi-model functionality.

Covers Story 0-1 acceptance criteria:
- AC1: Model registry with minilm/bge-large, default model, runtime selection
- AC2: Multi-model caching (subsequent calls return cached models)
- AC3: GPU/CPU device selection with logging
"""

import pytest
from unittest.mock import patch, MagicMock


class TestModelRegistry:
    """AC1: Model registry tests."""

    def test_embedding_models_registry_exists(self):
        """EMBEDDING_MODELS dict exists with required models."""
        from config import EMBEDDING_MODELS

        assert isinstance(EMBEDDING_MODELS, dict)
        assert "minilm" in EMBEDDING_MODELS
        assert "bge-large" in EMBEDDING_MODELS

    def test_minilm_config_correct(self):
        """minilm model config has correct name and dimension."""
        from config import EMBEDDING_MODELS

        minilm = EMBEDDING_MODELS["minilm"]
        assert minilm["name"] == "all-MiniLM-L6-v2"
        assert minilm["dim"] == 384

    def test_bge_large_config_correct(self):
        """bge-large model config has correct name and dimension."""
        from config import EMBEDDING_MODELS

        bge = EMBEDDING_MODELS["bge-large"]
        assert bge["name"] == "BAAI/bge-large-en-v1.5"
        assert bge["dim"] == 1024

    def test_default_embedding_model_exists(self):
        """DEFAULT_EMBEDDING_MODEL is set to valid model."""
        from config import DEFAULT_EMBEDDING_MODEL, EMBEDDING_MODELS

        assert DEFAULT_EMBEDDING_MODEL in EMBEDDING_MODELS

    def test_default_model_is_bge_large(self):
        """Default model should be bge-large per story requirements."""
        from config import DEFAULT_EMBEDDING_MODEL

        assert DEFAULT_EMBEDDING_MODEL == "bge-large"

    def test_embedding_device_config_exists(self):
        """EMBEDDING_DEVICE config exists with valid value."""
        from config import EMBEDDING_DEVICE

        assert EMBEDDING_DEVICE in ["auto", "cuda", "cpu"]


class TestEmbeddingGeneratorSingleton:
    """Test singleton pattern."""

    def test_singleton_returns_same_instance(self):
        """EmbeddingGenerator() always returns same instance."""
        from ingest_books import EmbeddingGenerator

        gen1 = EmbeddingGenerator()
        gen2 = EmbeddingGenerator()
        assert gen1 is gen2

    def test_models_cache_is_dict(self):
        """_models attribute is a dict for multi-model caching."""
        from ingest_books import EmbeddingGenerator

        gen = EmbeddingGenerator()
        assert hasattr(gen, "_models")
        assert isinstance(gen._models, dict)


class TestGetModelConfig:
    """Test get_model_config() method."""

    def test_get_model_config_minilm(self):
        """get_model_config returns correct config for minilm."""
        from ingest_books import EmbeddingGenerator

        gen = EmbeddingGenerator()
        config = gen.get_model_config("minilm")

        assert config["name"] == "all-MiniLM-L6-v2"
        assert config["dim"] == 384

    def test_get_model_config_bge_large(self):
        """get_model_config returns correct config for bge-large."""
        from ingest_books import EmbeddingGenerator

        gen = EmbeddingGenerator()
        config = gen.get_model_config("bge-large")

        assert config["name"] == "BAAI/bge-large-en-v1.5"
        assert config["dim"] == 1024

    def test_get_model_config_uses_default(self):
        """get_model_config with None uses DEFAULT_EMBEDDING_MODEL."""
        from ingest_books import EmbeddingGenerator
        from config import DEFAULT_EMBEDDING_MODEL, EMBEDDING_MODELS

        gen = EmbeddingGenerator()
        config = gen.get_model_config(None)

        expected = EMBEDDING_MODELS[DEFAULT_EMBEDDING_MODEL]
        assert config == expected

    def test_get_model_config_unknown_returns_none(self):
        """get_model_config returns None for unknown model_id."""
        from ingest_books import EmbeddingGenerator

        gen = EmbeddingGenerator()
        config = gen.get_model_config("nonexistent-model")

        assert config is None


class TestGetModelValidation:
    """Test get_model() validation."""

    def test_get_model_unknown_raises_valueerror(self):
        """get_model raises ValueError for unknown model_id."""
        from ingest_books import EmbeddingGenerator

        gen = EmbeddingGenerator()

        with pytest.raises(ValueError) as exc_info:
            gen.get_model("nonexistent-model")

        assert "Unknown model_id" in str(exc_info.value)
        assert "nonexistent-model" in str(exc_info.value)


class TestMultiModelCaching:
    """AC2: Multi-model caching tests."""

    def test_model_cached_after_load(self):
        """Loaded model is stored in _models cache."""
        from ingest_books import EmbeddingGenerator

        gen = EmbeddingGenerator()
        # Clear cache for clean test
        gen._models.clear()

        model = gen.get_model("minilm")

        assert "minilm" in gen._models
        assert gen._models["minilm"] is model

    def test_cached_model_returned_on_second_call(self):
        """Second call to get_model returns same cached instance."""
        from ingest_books import EmbeddingGenerator

        gen = EmbeddingGenerator()
        gen._models.clear()

        model1 = gen.get_model("minilm")
        model2 = gen.get_model("minilm")

        assert model1 is model2

    def test_different_models_cached_separately(self):
        """Different model_ids are cached independently."""
        from ingest_books import EmbeddingGenerator

        gen = EmbeddingGenerator()
        gen._models.clear()

        # Only test minilm to avoid downloading bge-large (1.3GB)
        model_minilm = gen.get_model("minilm")

        assert "minilm" in gen._models
        # bge-large should NOT be in cache yet
        assert "bge-large" not in gen._models


class TestDeviceSelection:
    """AC3: GPU/CPU device selection tests."""

    def test_device_selection_auto_without_cuda(self):
        """With EMBEDDING_DEVICE=auto and no CUDA, device should be cpu."""
        from ingest_books import EmbeddingGenerator
        import torch

        gen = EmbeddingGenerator()
        gen._models.clear()

        with patch.object(torch.cuda, "is_available", return_value=False):
            with patch("ingest_books.EMBEDDING_DEVICE", "auto"):
                model = gen.get_model("minilm")
                # Model should be on CPU
                assert model.device.type == "cpu"

    def test_device_selection_cpu_forced(self):
        """With EMBEDDING_DEVICE=cpu, model should be on CPU."""
        from ingest_books import EmbeddingGenerator

        gen = EmbeddingGenerator()
        gen._models.clear()

        with patch("ingest_books.EMBEDDING_DEVICE", "cpu"):
            model = gen.get_model("minilm")
            assert model.device.type == "cpu"


class TestEmbeddingGeneration:
    """Test generate_embeddings() method."""

    def test_generate_embeddings_returns_list(self):
        """generate_embeddings returns list of embedding vectors."""
        from ingest_books import EmbeddingGenerator

        gen = EmbeddingGenerator()
        texts = ["Hello world", "Test sentence"]

        embeddings = gen.generate_embeddings(texts, model_id="minilm")

        assert isinstance(embeddings, list)
        assert len(embeddings) == 2

    def test_generate_embeddings_correct_dimension(self):
        """Embeddings have correct dimension for model."""
        from ingest_books import EmbeddingGenerator

        gen = EmbeddingGenerator()
        texts = ["Test"]

        embeddings = gen.generate_embeddings(texts, model_id="minilm")

        assert len(embeddings[0]) == 384  # minilm dimension

    def test_generate_embeddings_module_function(self):
        """Module-level generate_embeddings function works."""
        from ingest_books import generate_embeddings

        embeddings = generate_embeddings(["Test"], model_id="minilm")

        assert len(embeddings) == 1
        assert len(embeddings[0]) == 384


class TestPrintConfig:
    """Test print_config shows embedding settings."""

    def test_print_config_shows_embedding_models(self, capsys):
        """print_config displays EMBEDDING_MODELS."""
        from config import print_config

        print_config()
        captured = capsys.readouterr()

        assert "EMBEDDING_MODELS" in captured.out
        assert "minilm" in captured.out or "bge-large" in captured.out

    def test_print_config_shows_default_model(self, capsys):
        """print_config displays DEFAULT_MODEL."""
        from config import print_config

        print_config()
        captured = capsys.readouterr()

        assert "DEFAULT_MODEL" in captured.out

    def test_print_config_shows_embedding_device(self, capsys):
        """print_config displays EMBEDDING_DEVICE."""
        from config import print_config

        print_config()
        captured = capsys.readouterr()

        assert "EMBEDDING_DEVICE" in captured.out

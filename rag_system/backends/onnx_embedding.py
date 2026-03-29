"""ONNX-based embedding backend with fallback support."""

import asyncio
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import numpy as np

from rag_system.backends.embedding import LocalHashEmbeddingBackend
from rag_system.core.base import EmbeddingBackend


class ONNXEmbeddingBackend(EmbeddingBackend):
    """ONNX-based embedding backend with automatic fallback.
    
    This backend uses ONNX Runtime for local transformer model inference.
    If the model is not available, it automatically falls back to LocalHashEmbeddingBackend.
    """
    
    def __init__(
        self,
        model_path: Path,
        dimension: int = 384,
        max_seq_length: int = 256,
        fallback_backend: Optional[EmbeddingBackend] = None,
    ):
        """Initialize ONNX embedding backend.
        
        Args:
            model_path: Path to the ONNX model file
            dimension: Embedding dimension
            max_seq_length: Maximum sequence length for tokenization
            fallback_backend: Fallback backend if ONNX model fails to load
        """
        self._model_path = Path(model_path)
        self._dimension = dimension
        self._max_seq_length = max_seq_length
        self._healthy = False
        self._session = None
        self._tokenizer = None
        
        # Initialize fallback
        if fallback_backend is None:
            self._fallback = LocalHashEmbeddingBackend(dimensions=dimension)
        else:
            self._fallback = fallback_backend
        
        # Try to load ONNX model
        self._load_model()
    
    def _load_model(self) -> None:
        """Attempt to load ONNX model."""
        if not self._model_path.exists():
            print(f"ONNX model not found at {self._model_path}, using fallback")
            return
        
        try:
            import onnxruntime as ort
            from transformers import AutoTokenizer
            
            # Load ONNX session
            self._session = ort.InferenceSession(
                str(self._model_path),
                providers=['CPUExecutionProvider']
            )
            
            # Load tokenizer from model directory
            tokenizer_dir = self._model_path.parent
            self._tokenizer = AutoTokenizer.from_pretrained(str(tokenizer_dir))
            
            self._healthy = True
            print(f"ONNX model loaded successfully from {self._model_path}")
            
        except Exception as e:
            print(f"Failed to load ONNX model: {e}, using fallback")
            self._healthy = False
    
    def embed_texts(self, texts: Sequence[str]) -> List[Tuple[float, ...]]:
        """Embed multiple texts synchronously.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors as tuples
        """
        if not self._healthy or self._session is None:
            return self._fallback.embed_texts(texts)
        
        try:
            import numpy as np
            
            # Tokenize
            inputs = self._tokenizer(
                list(texts),
                padding=True,
                truncation=True,
                max_length=self._max_seq_length,
                return_tensors='np',
            )
            
            # ONNX inference
            outputs = self._session.run(
                None,
                {
                    'input_ids': inputs['input_ids'],
                    'attention_mask': inputs['attention_mask'],
                }
            )
            
            # Mean pooling
            last_hidden_state = outputs[0]
            attention_mask = inputs['attention_mask']
            
            # Expand mask for broadcasting
            mask_expanded = np.expand_dims(attention_mask, -1)
            sum_embeddings = np.sum(last_hidden_state * mask_expanded, axis=1)
            sum_mask = np.sum(mask_expanded, axis=1)
            embeddings = sum_embeddings / np.clip(sum_mask, 1e-9, None)
            
            # L2 normalization
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / np.clip(norms, 1e-9, None)
            
            # Convert to tuples
            return [tuple(float(x) for x in emb) for emb in embeddings]
            
        except Exception as e:
            print(f"ONNX inference failed: {e}, using fallback")
            return self._fallback.embed_texts(texts)
    
    async def embed_texts_async(self, texts: Sequence[str]) -> List[Tuple[float, ...]]:
        """Embed multiple texts asynchronously.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors as tuples
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed_texts, texts)
    
    def is_healthy(self) -> bool:
        """Check if ONNX model is loaded and healthy."""
        return self._healthy
    
    def get_fallback(self) -> EmbeddingBackend:
        """Get the fallback backend."""
        return self._fallback

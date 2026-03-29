"""Cross-encoder reranker for fine-grained relevance scoring."""

from pathlib import Path
from typing import List, Sequence

import numpy as np

from rag_system.core.base import CandidateScore, IndexSnapshot, RerankerBackend
from rag_system.backends.reranker import LocalHeuristicReranker


class CrossEncoderReranker(RerankerBackend):
    """Cross-encoder based reranker with fallback support.
    
    Uses a cross-encoder model to score query-document pairs for fine-grained
    relevance scoring. Falls back to LocalHeuristicReranker if model unavailable.
    """
    
    def __init__(
        self,
        model_path: Path,
        max_candidates: int = 100,
        fallback: RerankerBackend = None,
    ):
        """Initialize cross-encoder reranker.
        
        Args:
            model_path: Path to the ONNX model file
            max_candidates: Maximum number of candidates to rerank
            fallback: Fallback reranker if model unavailable
        """
        self._model_path = Path(model_path)
        self._max_candidates = max_candidates
        self._healthy = False
        self._session = None
        self._tokenizer = None
        
        # Initialize fallback
        if fallback is None:
            self._fallback = LocalHeuristicReranker()
        else:
            self._fallback = fallback
        
        # Try to load model
        self._load_model()
        
        self.name = "cross-encoder"
        self.strategy = "cross-encoder-rerank"
    
    def _load_model(self) -> None:
        """Attempt to load cross-encoder model."""
        if not self._model_path.exists():
            print(f"Cross-encoder model not found at {self._model_path}, using fallback")
            return
        
        try:
            import onnxruntime as ort
            from transformers import AutoTokenizer
            
            self._session = ort.InferenceSession(
                str(self._model_path),
                providers=['CPUExecutionProvider']
            )
            
            tokenizer_dir = self._model_path.parent
            self._tokenizer = AutoTokenizer.from_pretrained(str(tokenizer_dir))
            
            self._healthy = True
            print(f"Cross-encoder model loaded from {self._model_path}")
            
        except Exception as e:
            print(f"Failed to load cross-encoder model: {e}, using fallback")
            self._healthy = False
    
    def rerank(
        self,
        query: str,
        snapshot: IndexSnapshot,
        candidates: Sequence[CandidateScore],
    ) -> List[CandidateScore]:
        """Rerank candidates using cross-encoder.
        
        Args:
            query: Search query
            snapshot: Index snapshot
            candidates: Initial candidate scores
            
        Returns:
            Reranked candidates
        """
        if not self._healthy or self._session is None:
            return self._fallback.rerank(query, snapshot, candidates)
        
        try:
            # Limit candidates
            candidates = list(candidates)[:self._max_candidates]
            
            if not candidates:
                return []
            
            # Build query-document pairs
            pairs = []
            for candidate in candidates:
                chunk = snapshot.chunks[candidate.index]
                pairs.append((query, chunk.text))
            
            if not pairs:
                return list(candidates)
            
            # Tokenize
            queries = [p[0] for p in pairs]
            docs = [p[1] for p in pairs]
            
            inputs = self._tokenizer(
                queries,
                docs,
                padding=True,
                truncation=True,
                max_length=512,
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
            
            # Get logits and apply sigmoid
            logits = outputs[0][:, 0]  # First position for classification
            scores = 1 / (1 + np.exp(-logits))  # Sigmoid
            
            # Combine with original scores
            reranked = []
            for i, candidate in enumerate(candidates):
                # Weighted combination: 40% heuristic + 60% cross-encoder
                combined_score = (
                    0.4 * candidate.retrieve_score +
                    0.6 * scores[i]
                )
                
                reranked.append(CandidateScore(
                    index=candidate.index,
                    retrieve_score=candidate.retrieve_score,
                    lexical_score=candidate.lexical_score,
                    title_score=candidate.title_score,
                    rerank_score=combined_score,
                    llm_score=scores[i],
                ))
            
            # Sort by rerank score
            reranked.sort(key=lambda c: c.rerank_score, reverse=True)
            
            return reranked
            
        except Exception as e:
            print(f"Cross-encoder reranking failed: {e}, using fallback")
            return self._fallback.rerank(query, snapshot, candidates)
    
    def is_healthy(self) -> bool:
        """Check if model is loaded and healthy."""
        return self._healthy
    
    def candidate_pool_size(self, top_k: int) -> int:
        """Calculate candidate pool size."""
        return min(top_k * 6, self._max_candidates)
    
    async def rerank_async(
        self,
        query: str,
        snapshot: IndexSnapshot,
        candidates: Sequence[CandidateScore],
    ) -> List[CandidateScore]:
        """Async version of rerank.
        
        Args:
            query: Search query
            snapshot: Index snapshot
            candidates: Initial candidate scores
            
        Returns:
            Reranked candidates
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.rerank, query, snapshot, candidates
        )

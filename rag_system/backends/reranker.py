"""Reranker backend implementations with async support."""

import asyncio
import json
from typing import Dict, List, Optional, Sequence

from ..core.base import RerankerBackend, IndexSnapshot, CandidateScore
from ..exceptions import ExternalServiceError
from ..utils.retry import retry_with_backoff, RetryConfig
from ..utils.text import shorten, tokenize
from .embedding import EmbeddingConnectionPool


class LocalHeuristicReranker(RerankerBackend):
    """Local heuristic-based reranker."""
    
    def __init__(self):
        self.name = "local-heuristic"
        self.strategy = "embedding+lexical-overlap"
    
    def rerank(
        self,
        query: str,
        snapshot: IndexSnapshot,
        candidates: Sequence[CandidateScore],
    ) -> List[CandidateScore]:
        """Rerank candidates using heuristic scoring."""
        if not candidates:
            return []
        
        max_lexical = max((c.lexical_score for c in candidates), default=1.0)
        max_lexical = max_lexical if max_lexical > 0 else 1.0
        
        ranked: List[CandidateScore] = []
        for candidate in candidates:
            normalized_lexical = candidate.lexical_score / max_lexical
            # Weights: Semantic 0.60, Lexical 0.30, Title 0.10
            score = (
                candidate.retrieve_score * 0.60 +
                normalized_lexical * 0.30 +
                candidate.title_score * 0.10
            )
            ranked.append(
                CandidateScore(
                    index=candidate.index,
                    retrieve_score=candidate.retrieve_score,
                    lexical_score=candidate.lexical_score,
                    title_score=candidate.title_score,
                    rerank_score=score,
                    llm_score=0.0,
                )
            )
        
        ranked.sort(
            key=lambda item: (
                item.rerank_score,
                item.retrieve_score,
                item.lexical_score,
                item.title_score,
            ),
            reverse=True,
        )
        return ranked
    
    async def rerank_async(
        self,
        query: str,
        snapshot: IndexSnapshot,
        candidates: Sequence[CandidateScore],
    ) -> List[CandidateScore]:
        """Async version (runs sync version in thread pool)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.rerank, query, snapshot, candidates)


class OpenAICompatibleListwiseReranker(RerankerBackend):
    """OpenAI-compatible listwise reranker."""
    
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        fallback: Optional[RerankerBackend] = None,
        timeout: int = 45,
        max_candidates: int = 12,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_candidates = max_candidates
        self.fallback = fallback or LocalHeuristicReranker()
        self.name = f"openai-compatible:{model}"
        self.strategy = "embedding+llm-listwise-rerank"
        self._connection_pool: Optional[EmbeddingConnectionPool] = None
        self._retry_config = RetryConfig(
            max_retries=max_retries,
            base_delay=retry_delay,
            max_delay=30.0,
            exponential_base=2.0,
            retryable_exceptions=(ExternalServiceError, asyncio.TimeoutError),
        )
    
    def candidate_pool_size(self, top_k: int) -> int:
        """Calculate candidate pool size."""
        return max(top_k * 8, self.max_candidates)
    
    async def _get_connection_pool(self) -> EmbeddingConnectionPool:
        """Get or create connection pool."""
        if self._connection_pool is None:
            self._connection_pool = EmbeddingConnectionPool(timeout=self.timeout)
        return self._connection_pool
    
    def _extract_json_object(self, text: str) -> str:
        """Extract JSON object from text."""
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise ValueError("Response does not contain a valid JSON object")
        return text[start:end + 1]
    
    async def _request_scores(
        self,
        query: str,
        snapshot: IndexSnapshot,
        candidates: Sequence[CandidateScore],
    ) -> Dict[int, float]:
        """Request LLM scores for candidates."""
        prompt_id_to_index: Dict[int, int] = {}
        candidate_blocks: List[str] = []
        
        for prompt_id, candidate in enumerate(candidates):
            chunk = snapshot.chunks[candidate.index]
            prompt_id_to_index[prompt_id] = candidate.index
            candidate_blocks.append(
                f"[{prompt_id}]\n"
                f"source: {chunk.source}\n"
                f"title: {chunk.title}\n"
                f"text: {shorten(chunk.text.replace(chr(10), ' '), width=360)}"
            )
        
        pool = await self._get_connection_pool()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a retrieval reranker. Score each candidate chunk from 0 to 1 based on "
                        "how well it can answer the user query. Return JSON only in the format "
                        '{"scores":[{"id":0,"score":0.0}]}.'
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Query:\n{query}\n\nCandidates:\n\n" + "\n\n".join(candidate_blocks)
                    ),
                },
            ],
            "max_tokens": 500,
        }
        
        try:
            data = await pool.post(
                f"{self.base_url}/v1/chat/completions",
                headers,
                payload,
            )
            
            raw_content = data["choices"][0]["message"]["content"]
            json_str = self._extract_json_object(raw_content)
            payload = json.loads(json_str)
            
            scores: Dict[int, float] = {}
            for item in payload.get("scores", []):
                try:
                    prompt_id = int(item["id"])
                    score = max(0.0, min(float(item["score"]), 1.0))
                except (KeyError, TypeError, ValueError):
                    continue
                original_index = prompt_id_to_index.get(prompt_id)
                if original_index is not None:
                    scores[original_index] = score
            
            return scores
        except Exception as e:
            raise ExternalServiceError(
                message=f"Failed to get rerank scores: {str(e)}",
                service="openai-compatible-reranker",
            ) from e
    
    async def _request_scores_with_retry(
        self,
        query: str,
        snapshot: IndexSnapshot,
        candidates: Sequence[CandidateScore],
    ) -> Dict[int, float]:
        """Request scores with retry logic."""
        return await retry_with_backoff(
            self._request_scores,
            query,
            snapshot,
            candidates,
            config=self._retry_config,
        )
    
    def rerank(
        self,
        query: str,
        snapshot: IndexSnapshot,
        candidates: Sequence[CandidateScore],
    ) -> List[CandidateScore]:
        """Sync version - runs async version in event loop."""
        return asyncio.run(self.rerank_async(query, snapshot, candidates))
    
    async def rerank_async(
        self,
        query: str,
        snapshot: IndexSnapshot,
        candidates: Sequence[CandidateScore],
    ) -> List[CandidateScore]:
        """Async rerank with LLM-enhanced scoring."""
        # First pass: heuristic rerank
        base_ranked = await self.fallback.rerank_async(query, snapshot, candidates)
        prompt_candidates = base_ranked[:min(len(base_ranked), self.max_candidates)]
        
        # Get LLM scores
        try:
            llm_scores = await self._request_scores_with_retry(
                query, snapshot, prompt_candidates
            )
        except Exception:
            # Fallback to base ranking on error
            return base_ranked
        
        # Merge scores
        merged: List[CandidateScore] = []
        for candidate in base_ranked:
            llm_score = llm_scores.get(candidate.index, 0.0)
            if candidate.index in llm_scores:
                final_score = candidate.rerank_score * 0.45 + llm_score * 0.55
            else:
                final_score = candidate.rerank_score
            
            merged.append(
                CandidateScore(
                    index=candidate.index,
                    retrieve_score=candidate.retrieve_score,
                    lexical_score=candidate.lexical_score,
                    title_score=candidate.title_score,
                    rerank_score=final_score,
                    llm_score=llm_score,
                )
            )
        
        merged.sort(
            key=lambda item: (
                item.rerank_score,
                item.llm_score,
                item.retrieve_score,
                item.lexical_score,
            ),
            reverse=True,
        )
        
        return merged
    
    async def close(self) -> None:
        """Close connection pool."""
        if self._connection_pool:
            await self._connection_pool.close()

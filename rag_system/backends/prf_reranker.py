"""Pseudo-Relevance Feedback reranker for query expansion."""

from collections import Counter, defaultdict
from typing import List, Set

from rag_system.core.base import IndexSnapshot, SearchHit
from rag_system.utils.text import tokenize


class PRFReranker:
    """Pseudo-Relevance Feedback reranker.
    
    Expands the original query based on terms from top-k initial results.
    This can improve recall by capturing related terms not in the original query.
    """
    
    def __init__(
        self,
        num_terms: int = 3,
        min_doc_freq: int = 2,
        term_weight: float = 0.3,
    ):
        """Initialize PRF reranker.
        
        Args:
            num_terms: Number of expansion terms to add
            min_doc_freq: Minimum document frequency for a term to be selected
            term_weight: Weight of expansion terms relative to original query
        """
        self._num_terms = num_terms
        self._min_doc_freq = min_doc_freq
        self._term_weight = term_weight
    
    def expand_query(
        self,
        query: str,
        initial_results: List[SearchHit],
        index_snapshot: IndexSnapshot,
    ) -> str:
        """Expand query using pseudo-relevance feedback.
        
        Args:
            query: Original query string
            initial_results: Initial search results (top-k)
            index_snapshot: Index snapshot with document info
            
        Returns:
            Expanded query string
        """
        if not initial_results:
            return query
        
        # Get expansion terms
        expansion_terms = self._get_expansion_terms(query, initial_results)
        
        if not expansion_terms:
            return query
        
        # Build expanded query
        expanded_terms = expansion_terms[:self._num_terms]
        expanded_query = f"{query} {' '.join(expanded_terms)}"
        
        return expanded_query
    
    def _get_expansion_terms(
        self,
        query: str,
        initial_results: List[SearchHit],
    ) -> List[str]:
        """Get expansion terms from initial results.
        
        Args:
            query: Original query
            initial_results: Initial search results
            
        Returns:
            List of expansion terms sorted by frequency
        """
        # Get original query terms
        original_terms = set(tokenize(query))
        
        # Collect term frequencies from top results
        term_freq = Counter()
        term_doc_freq = defaultdict(int)
        
        # Use top 10 results for feedback
        for hit in initial_results[:10]:
            chunk_text = hit.chunk.text
            terms = tokenize(chunk_text)
            
            # Count unique terms in this document
            doc_terms = set(terms)
            
            for term in terms:
                term_freq[term] += 1
            
            for term in doc_terms:
                term_doc_freq[term] += 1
        
        # Filter and sort terms
        expansion_terms = []
        
        for term, freq in term_freq.most_common():
            # Skip terms already in original query
            if term in original_terms:
                continue
            
            # Skip terms that don't meet minimum document frequency
            if term_doc_freq[term] < self._min_doc_freq:
                continue
            
            # Skip very short terms
            if len(term) < 2:
                continue
            
            # Skip numeric-only terms
            if term.isdigit():
                continue
            
            expansion_terms.append(term)
            
            if len(expansion_terms) >= self._num_terms * 2:
                break
        
        return expansion_terms
    
    def get_expansion_terms_with_scores(
        self,
        query: str,
        initial_results: List[SearchHit],
    ) -> List[tuple[str, int]]:
        """Get expansion terms with their scores.
        
        Args:
            query: Original query
            initial_results: Initial search results
            
        Returns:
            List of (term, score) tuples
        """
        original_terms = set(tokenize(query))
        term_freq = Counter()
        
        for hit in initial_results[:10]:
            terms = tokenize(hit.chunk.text)
            for term in terms:
                if term not in original_terms and len(term) >= 2:
                    term_freq[term] += 1
        
        return term_freq.most_common(self._num_terms * 2)

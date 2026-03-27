"""
Unit tests for utility functions.
"""

import pytest
import math
from rag_system.utils import (
    normalize_vector,
    dot_product,
    cosine_similarity,
    batch_items,
    extract_json_object,
    shorten,
    first_heading,
    first_non_empty_line,
)


class TestVectorOperations:
    """Tests for vector operations."""
    
    def test_normalize_simple_vector(self):
        """Test normalizing a simple 3D vector."""
        values = [3.0, 4.0, 0.0]  # 3-4-5 triangle
        normalized = normalize_vector(values)
        
        assert abs(normalized[0] - 0.6) < 0.001
        assert abs(normalized[1] - 0.8) < 0.001
        assert normalized[2] == 0.0
    
    def test_normalize_zero_vector(self):
        """Test normalizing zero vector returns zero vector."""
        values = [0.0, 0.0, 0.0]
        normalized = normalize_vector(values)
        
        assert normalized == (0.0, 0.0, 0.0)
    
    def test_normalize_already_normalized(self):
        """Test normalizing already normalized vector."""
        values = [1.0, 0.0, 0.0, 0.0]
        normalized = normalize_vector(values)
        
        assert normalized == (1.0, 0.0, 0.0, 0.0)
    
    def test_normalize_unit_vector(self):
        """Test normalizing unit vector."""
        values = [0.0, 1.0, 0.0]
        normalized = normalize_vector(values)
        
        assert normalized == (0.0, 1.0, 0.0)


class TestDotProduct:
    """Tests for dot product function."""
    
    def test_dot_product_orthogonal_vectors(self):
        """Test dot product of orthogonal vectors is zero."""
        v1 = [1.0, 0.0, 0.0]
        v2 = [0.0, 1.0, 0.0]
        
        result = dot_product(v1, v2)
        assert result == 0.0
    
    def test_dot_product_parallel_vectors(self):
        """Test dot product of parallel vectors."""
        v1 = [1.0, 2.0, 3.0]
        v2 = [2.0, 4.0, 6.0]
        
        result = dot_product(v1, v2)
        expected = 1*2 + 2*4 + 3*6
        assert result == expected
    
    def test_dot_product_same_vector(self):
        """Test dot product of vector with itself equals squared norm."""
        v = [3.0, 4.0]
        
        result = dot_product(v, v)
        expected = 3*3 + 4*4
        assert result == expected
    
    def test_dot_product_empty_vectors(self):
        """Test dot product of empty vectors."""
        result = dot_product([], [])
        assert result == 0.0


class TestCosineSimilarity:
    """Tests for cosine similarity function."""
    
    def test_cosine_similarity_same_vector(self):
        """Test cosine similarity of vector with itself is 1."""
        v = normalize_vector([1.0, 2.0, 3.0])
        
        result = cosine_similarity(v, v)
        assert abs(result - 1.0) < 0.001
    
    def test_cosine_similarity_orthogonal(self):
        """Test cosine similarity of orthogonal vectors is 0."""
        v1 = [1.0, 0.0, 0.0]
        v2 = [0.0, 1.0, 0.0]
        
        result = cosine_similarity(v1, v2)
        assert result == 0.0
    
    def test_cosine_similarity_opposite(self):
        """Test cosine similarity of opposite vectors is -1."""
        v1 = normalize_vector([1.0, 0.0, 0.0])
        v2 = normalize_vector([-1.0, 0.0, 0.0])
        
        result = cosine_similarity(v1, v2)
        assert abs(result - (-1.0)) < 0.001
    
    def test_cosine_similarity_empty_vectors(self):
        """Test cosine similarity with empty vectors."""
        result = cosine_similarity([], [])
        assert result == 0.0
    
    def test_cosine_similarity_partial_overlap(self):
        """Test cosine similarity with partial overlap."""
        v1 = normalize_vector([1.0, 1.0, 0.0])
        v2 = normalize_vector([1.0, 0.0, 0.0])
        
        result = cosine_similarity(v1, v2)
        # cos(45°) ≈ 0.707
        assert abs(result - 0.707) < 0.01


class TestBatchItems:
    """Tests for batch_items function."""
    
    def test_batch_items_exact_fit(self):
        """Test batching with exact fit."""
        items = [1, 2, 3, 4, 5, 6]
        batches = batch_items(items, 3)
        
        assert len(batches) == 2
        assert list(batches[0]) == [1, 2, 3]
        assert list(batches[1]) == [4, 5, 6]
    
    def test_batch_items_with_remainder(self):
        """Test batching with remainder."""
        items = [1, 2, 3, 4, 5]
        batches = batch_items(items, 2)
        
        assert len(batches) == 3
        assert list(batches[0]) == [1, 2]
        assert list(batches[1]) == [3, 4]
        assert list(batches[2]) == [5]
    
    def test_batch_items_empty(self):
        """Test batching empty list."""
        items = []
        batches = batch_items(items, 3)
        
        assert batches == []
    
    def test_batch_items_larger_than_batch(self):
        """Test batching when batch size larger than list."""
        items = [1, 2]
        batches = batch_items(items, 10)
        
        assert len(batches) == 1
        assert list(batches[0]) == [1, 2]


class TestExtractJsonObject:
    """Tests for extract_json_object function."""
    
    def test_extract_simple_json(self):
        """Test extracting simple JSON object."""
        text = 'Some text {"key": "value"} more text'
        result = extract_json_object(text)
        
        assert result == '{"key": "value"}'
    
    def test_extract_nested_json(self):
        """Test extracting nested JSON object."""
        text = 'Prefix {"outer": {"inner": "value"}} suffix'
        result = extract_json_object(text)
        
        assert result == '{"outer": {"inner": "value"}}'
    
    def test_extract_json_array(self):
        """Test extracting JSON with array."""
        text = 'Text [{"a": 1}, {"b": 2}] more'
        result = extract_json_object(text)
        # May extract array contents depending on implementation
        assert "{\"a\": 1}" in result or result == '[{"a": 1}, {"b": 2}]'
    
    def test_extract_no_json_raises_error(self):
        """Test that missing JSON raises error."""
        text = "No JSON here"
        
        with pytest.raises(RuntimeError) as exc_info:
            extract_json_object(text)
        
        assert "JSON" in str(exc_info.value) or "json" in str(exc_info.value).lower()
    
    def test_extract_unbalanced_braces_raises_error(self):
        """Test that unbalanced braces raise error."""
        text = "Text {key: value more text"
        
        with pytest.raises(RuntimeError):
            extract_json_object(text)


class TestShorten:
    """Tests for shorten function."""
    
    def test_shorten_short_string(self):
        """Test that short string is unchanged."""
        text = "Short"
        result = shorten(text, width=20)
        
        assert result == text
    
    def test_shorten_long_string(self):
        """Test that long string is shortened."""
        text = "This is a very long string that needs shortening"
        result = shorten(text, width=20)
        
        assert len(result) <= 20
        assert result.endswith("...")
    
    def test_shorten_exact_width(self):
        """Test string at exact width."""
        text = "Exactly twenty chars"
        result = shorten(text, width=20)
        
        assert len(result) <= 20
    
    def test_shorten_with_custom_width(self):
        """Test shortening with custom width."""
        text = "A longer piece of text for testing"
        result = shorten(text, width=10)
        
        assert len(result) == 10
        assert result.endswith("...")


class TestFirstHeading:
    """Tests for first_heading function."""
    
    def test_extract_h1(self):
        """Test extracting H1 heading."""
        text = "# Main Title\n\nContent here"
        result = first_heading(text, "fallback")
        
        assert result == "Main Title"
    
    def test_extract_h2(self):
        """Test extracting H2 heading."""
        text = "## Section Title\nContent"
        result = first_heading(text, "fallback")
        
        assert result == "Section Title"
    
    def test_extract_heading_with_spaces(self):
        """Test extracting heading with extra spaces."""
        text = "#   Spaced Title   \nContent"
        result = first_heading(text, "fallback")
        
        assert result == "Spaced Title"
    
    def test_fallback_no_heading(self):
        """Test fallback when no heading exists."""
        text = "Just content\nNo heading"
        result = first_heading(text, "fallback")
        
        assert result == "fallback"
    
    def test_empty_text_fallback(self):
        """Test fallback with empty text."""
        result = first_heading("", "default")
        
        assert result == "default"


class TestFirstNonEmptyLine:
    """Tests for first_non_empty_line function."""
    
    def test_first_line(self):
        """Test getting first non-empty line."""
        text = "First line\nSecond line"
        result = first_non_empty_line(text, "fallback")
        
        assert result == "First line"
    
    def test_skip_empty_lines(self):
        """Test skipping empty lines."""
        text = "\n\n\nFirst real line"
        result = first_non_empty_line(text, "fallback")
        
        assert result == "First real line"
    
    def test_skip_heading_marker(self):
        """Test that heading marker is stripped."""
        text = "# Heading\nContent"
        result = first_non_empty_line(text, "fallback")
        
        assert result == "Heading"
    
    def test_fallback_all_empty(self):
        """Test fallback when all lines empty."""
        text = "\n\n\n"
        result = first_non_empty_line(text, "fallback")
        
        assert result == "fallback"
    
    def test_single_line(self):
        """Test single line text."""
        text = "Only line"
        result = first_non_empty_line(text, "fallback")
        
        assert result == "Only line"

"""Utility functions for RAG system."""

from .retry import RetryConfig, retry_with_backoff, RetryableError
from .text import (
    tokenize,
    split_sentences,
    split_paragraphs,
    wrap_paragraph,
    chunk_text,
    first_heading,
    first_non_empty_line,
    shorten,
    normalize_vector,
    dot_product,
    cosine_similarity,
    batch_items,
)
from .file import (
    read_text_file,
    extract_word_file,
    extract_pdf_file,
    SUPPORTED_EXTENSIONS,
)
from .json_utils import extract_json_object, chat_message_to_text, post_json
from .file_security import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    sanitize_filename,
    validate_file_extension,
    validate_file_size,
    get_secure_path,
    get_file_extension,
    is_safe_filename,
)

__all__ = [
    "RetryConfig",
    "retry_with_backoff",
    "RetryableError",
    "tokenize",
    "split_sentences",
    "split_paragraphs",
    "wrap_paragraph",
    "chunk_text",
    "first_heading",
    "first_non_empty_line",
    "shorten",
    "normalize_vector",
    "dot_product",
    "cosine_similarity",
    "batch_items",
    "read_text_file",
    "extract_word_file",
    "extract_pdf_file",
    "SUPPORTED_EXTENSIONS",
    "extract_json_object",
    "chat_message_to_text",
    "post_json",
    "ALLOWED_EXTENSIONS",
    "MAX_FILE_SIZE",
    "sanitize_filename",
    "validate_file_extension",
    "validate_file_size",
    "get_secure_path",
    "get_file_extension",
    "is_safe_filename",
]

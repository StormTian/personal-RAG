"""CLI entry point for RAG system."""

import argparse
import asyncio
import sys
from pathlib import Path

from .rag_engine import RAGEngine
from .config import get_settings
from .exceptions import RAGError


def print_response(response):
    """Pretty print RAG response."""
    print(f"\nQuestion: {response.query}\n")
    print("Answer:")
    for line in response.answer_lines:
        print(f"- {line}")
    
    if response.hits:
        print("\nRetrieved Context:")
        for i, hit in enumerate(response.hits, 1):
            excerpt = hit.chunk.text.replace("\n", " ")[:88]
            if len(hit.chunk.text) > 88:
                excerpt += "..."
            print(f"[{i}] {hit.chunk.source} | score={hit.score:.3f}")
            print(f"    {excerpt}")


def run_interactive(engine):
    """Run interactive mode."""
    print("Entering interactive mode. Type 'exit' or 'quit' to end.\n")
    
    while True:
        try:
            query = input("You > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        
        if query.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        
        if not query:
            continue
        
        try:
            response = engine.answer(query)
            print_response(response)
            print()
        except RAGError as e:
            print(f"Error: {e.message}")
        except Exception as e:
            print(f"Unexpected error: {e}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="RAG System - Production-ready Retrieval-Augmented Generation"
    )
    parser.add_argument(
        "--library-dir",
        type=Path,
        default=None,
        help="Directory containing documents to index",
    )
    parser.add_argument(
        "--query", "-q",
        type=str,
        help="Single query to execute",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of results to retrieve",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show system statistics and exit",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Reload document library",
    )
    
    args = parser.parse_args()
    
    # Load configuration
    if args.config:
        from .config.loader import ConfigLoader
        loader = ConfigLoader(args.config)
        loader.load()
    
    settings = get_settings()
    library_dir = args.library_dir or settings.library_dir
    
    # Initialize engine
    try:
        print(f"Initializing RAG Engine...")
        print(f"Library directory: {library_dir}")
        engine = RAGEngine(library_dir)
        print(f"Ready! Indexed {len(engine._snapshot.chunks)} chunks from {len(engine._snapshot.documents)} documents\n")
    except Exception as e:
        print(f"Failed to initialize: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Handle commands
    if args.stats:
        stats = engine.stats()
        print("\nSystem Statistics")
        print("=" * 50)
        print(f"Library: {stats['library_dir']}")
        print(f"Documents: {stats['documents']}")
        print(f"Chunks: {stats['chunks']}")
        print(f"Embedding Backend: {stats['embedding_backend']}")
        print(f"Reranker Backend: {stats['reranker_backend']}")
        print(f"Supported Formats: {', '.join(stats['supported_formats'])}")
        return
    
    if args.reload:
        print("Reloading document library...")
        engine.reload()
        print("Reload complete!")
        return
    
    if args.query:
        try:
            response = engine.answer(args.query, top_k=args.top_k)
            print_response(response)
        except RAGError as e:
            print(f"Error: {e.message}", file=sys.stderr)
            sys.exit(1)
        return
    
    # Default to interactive mode
    run_interactive(engine)


if __name__ == "__main__":
    main()

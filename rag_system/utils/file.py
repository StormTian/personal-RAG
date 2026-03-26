"""File reading and extraction utilities."""

import os
import subprocess
from pathlib import Path
from typing import Set

SUPPORTED_EXTENSIONS = {
    ".md": "markdown",
    ".markdown": "markdown",
    ".txt": "text",
    ".doc": "word",
    ".docx": "word",
    ".pdf": "pdf",
}


def read_text_file(path: Path) -> str:
    """Read text file with multiple encoding attempts."""
    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_word_file(path: Path) -> str:
    """Extract text from Word document using textutil."""
    try:
        result = subprocess.run(
            [
                "textutil",
                "-convert", "txt",
                "-stdout",
                "-encoding", "UTF-8",
                str(path)
            ],
            check=True,
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("System missing textutil, cannot parse Word files") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode("utf-8", errors="ignore").strip()
        raise RuntimeError(stderr or "Word file parsing failed") from exc
    
    return result.stdout.decode("utf-8", errors="ignore")


def extract_pdf_file(path: Path) -> str:
    """Extract text from PDF file."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        parts = []
        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                parts.append(text)
        return "\n".join(parts)
    except ImportError:
        pass
    
    # Fallback to Swift script
    swift_script = f"""
import Foundation
import PDFKit

let url = URL(fileURLWithPath: "{str(path)}")
guard let document = PDFDocument(url: url) else {{
    fputs("failed to open pdf\\n", stderr)
    exit(1)
}}

var parts: [String] = []
for index in 0..<document.pageCount {{
    if let page = document.page(at: index), let text = page.string, 
       !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {{
        parts.append(text)
    }}
}}
print(parts.joined(separator: "\\n"))
"""
    try:
        result = subprocess.run(
            ["swift", "-"],
            input=swift_script.encode("utf-8"),
            check=True,
            capture_output=True,
            env={
                **os.environ,
                "SWIFT_MODULECACHE_PATH": "/tmp/rag_swift_cache",
                "CLANG_MODULE_CACHE_PATH": "/tmp/rag_swift_cache",
            },
        )
    except FileNotFoundError as exc:
        raise RuntimeError("System missing available PDF parsing capability, please install pypdf") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode("utf-8", errors="ignore").strip()
        raise RuntimeError(stderr or "PDF file parsing failed") from exc
    
    return result.stdout.decode("utf-8", errors="ignore")

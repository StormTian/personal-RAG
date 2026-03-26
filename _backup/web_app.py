from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from app import DOCUMENT_LIBRARY_DIR, ROOT, TinyRAG


STATIC_DIR = ROOT / "web"


def load_asset(path: Path, fallback: str = "") -> bytes:
    if not path.exists():
        return fallback.encode("utf-8")
    return path.read_bytes()


def parse_top_k(top_k_raw: str) -> int:
    try:
        return max(1, min(int(top_k_raw), 8))
    except ValueError as exc:
        raise ValueError("top_k 必须是整数。") from exc


def build_answer_payload(rag: TinyRAG, query: str, top_k_raw: str) -> Tuple[int, Dict[str, object]]:
    normalized_query = query.strip()
    if not normalized_query:
        return HTTPStatus.BAD_REQUEST, {"error": "请输入问题。"}

    try:
        top_k = parse_top_k(top_k_raw)
    except ValueError as exc:
        return HTTPStatus.BAD_REQUEST, {"error": str(exc)}

    return HTTPStatus.OK, rag.answer(query=normalized_query, top_k=top_k).to_dict()


def build_library_payload(rag: TinyRAG) -> Dict[str, object]:
    return {
        "status": "ok",
        **rag.stats(),
    }


def reload_library(rag: TinyRAG, library_dir: Optional[Path] = None) -> Tuple[int, Dict[str, object]]:
    try:
        rag.reload(library_dir=library_dir)
    except Exception as exc:
        return HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)}

    return HTTPStatus.OK, {"status": "ok", "message": "文档库重新入库完成。", **rag.stats()}


class RagHTTPRequestHandler(BaseHTTPRequestHandler):
    rag: TinyRAG
    index_html: bytes
    app_js: bytes
    styles_css: bytes

    server_version = "TinyRAGHTTP/0.3"

    def _send_bytes(self, body: bytes, content_type: str, status: int = HTTPStatus.OK) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        # CORS headers
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        """Handle CORS preflight requests"""
        self.send_response(HTTPStatus.OK)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def _send_json(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        self._send_bytes(
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8",
            status,
        )

    def _send_text(self, message: str, status: int) -> None:
        self._send_bytes(message.encode("utf-8"), "text/plain; charset=utf-8", status)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_bytes(self.index_html, "text/html; charset=utf-8")
            return
        if parsed.path == "/app.js":
            self._send_bytes(self.app_js, "application/javascript; charset=utf-8")
            return
        if parsed.path == "/styles.css":
            self._send_bytes(self.styles_css, "text/css; charset=utf-8")
            return
        if parsed.path == "/api/health":
            self._send_json(build_library_payload(self.rag))
            return
        if parsed.path == "/api/library":
            self._send_json(build_library_payload(self.rag))
            return
        if parsed.path == "/api/ask":
            query = parse_qs(parsed.query).get("q", [""])[0].strip()
            top_k_raw = parse_qs(parsed.query).get("top_k", ["3"])[0].strip()
            self._handle_question(query, top_k_raw)
            return
        self._send_text("Not Found", HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/reload":
            status, payload = reload_library(self.rag)
            self._send_json(payload, status)
            return
        if parsed.path != "/api/ask":
            self._send_text("Not Found", HTTPStatus.NOT_FOUND)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length) if content_length else b"{}"
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json({"error": "请求体不是合法 JSON。"}, HTTPStatus.BAD_REQUEST)
            return

        query = str(payload.get("query", "")).strip()
        top_k_raw = str(payload.get("top_k", 3)).strip()
        self._handle_question(query, top_k_raw)

    def _handle_question(self, query: str, top_k_raw: str) -> None:
        status, payload = build_answer_payload(self.rag, query, top_k_raw)
        self._send_json(payload, status)

    def log_message(self, format: str, *args: object) -> None:
        return


def build_handler(rag: TinyRAG) -> type[RagHTTPRequestHandler]:
    class Handler(RagHTTPRequestHandler):
        pass

    Handler.rag = rag
    Handler.index_html = load_asset(STATIC_DIR / "index.html")
    Handler.app_js = load_asset(STATIC_DIR / "app.js")
    Handler.styles_css = load_asset(STATIC_DIR / "styles.css")
    return Handler


def run_server(host: str, port: int, library_dir: Path) -> None:
    rag = TinyRAG(library_dir)
    handler = build_handler(rag)
    server = ThreadingHTTPServer((host, port), handler)
    print(f"RAG Web UI is running at http://{host}:{port}")
    print(f"Document library: {library_dir}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Tiny RAG web UI.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind.")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on.")
    parser.add_argument(
        "--library-dir",
        "--knowledge-dir",
        dest="library_dir",
        type=Path,
        default=DOCUMENT_LIBRARY_DIR,
        help="Directory that stores source documents.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    run_server(args.host, args.port, args.library_dir)


if __name__ == "__main__":
    main()

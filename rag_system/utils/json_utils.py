"""JSON utilities for API responses."""

import json
from typing import Any, Dict, List
import urllib.request
import urllib.error


def extract_json_object(text: str) -> str:
    """Extract JSON object from text."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("Response does not contain a valid JSON object")
    return text[start:end + 1]


def chat_message_to_text(content: object) -> str:
    """Extract text from chat message content."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text" and isinstance(item.get("text"), str):
                    parts.append(item["text"])
                elif isinstance(item.get("text"), dict) and isinstance(item["text"].get("value"), str):
                    parts.append(item["text"]["value"])
        return "\n".join(parts)
    raise ValueError("Unsupported message content type")


def post_json(
    url: str,
    headers: Dict[str, str],
    payload: Dict[str, object],
    timeout: int = 30,
) -> Dict[str, object]:
    """POST JSON data and return JSON response."""
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Request failed: {exc.code} {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Request failed: {exc.reason}") from exc

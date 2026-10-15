"""Normalize the existing Notion connector result for CU continuation.

The source is the response of the connected Notion tool, not an independently
authenticated Notion client. Never infer adoption from a free-text comment.
"""
import json

def ingest(payload, cu_url):
    from scripts.chat_notion_comment_adapter import parse_comments
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        raise ValueError("NOTION_PAYLOAD_INVALID")
    if isinstance(payload.get("structuredContent"), dict):
        inner = payload["structuredContent"]
        if isinstance(inner.get("results"), list):
            # Search results are pointers only; they are not decision records.
            return []
        return parse_comments(inner, cu_url)
    if "text" in payload:
        return parse_comments(payload, cu_url)
    raise ValueError("NOTION_PAYLOAD_UNSUPPORTED")

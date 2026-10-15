"""Normalize the existing Notion connector result for CU continuation.

The source is the response of the connected Notion tool, not an independently
authenticated Notion client. Never infer adoption from a free-text comment.
"""
import json

def ingest(payload, cu_url, page_url=None):
    from scripts.chat_notion_comment_adapter import parse_comments
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("sources"), list):
        # A bounded bundle is assembled from actual, previously fetched Notion
        # connector responses. Search hits alone must not become decisions.
        sources = payload["sources"]
        if len(sources) > 20:
            raise ValueError("NOTION_SOURCES_TOO_MANY")
        records = []
        for item in sources:
            if not isinstance(item, dict) or item.get("type") not in {"page", "comments"}:
                raise ValueError("NOTION_SOURCE_INVALID")
            if item["type"] == "page":
                url = item.get("page_url")
                if not isinstance(url, str):
                    raise ValueError("NOTION_PAGE_URL_REQUIRED")
                records.extend(ingest(item.get("response"), cu_url, url))
            else:
                records.extend(ingest(item.get("response"), cu_url))
        return records
    if page_url is not None:
        from scripts.chat_notion_page_evidence import page_evidence
        return page_evidence(payload, cu_url, page_url)
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

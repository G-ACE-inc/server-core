"""Extract bounded attributable context from existing Notion page fetch results.

No free-text inference of adoption; preserve page as evidence with UNKNOWN state.
"""
import json
import re
from html import unescape


def unwrap_tool_response(payload):
    """Accept actual MCP wrappers; explicit rejection is never page evidence."""
    for _ in range(8):
        if isinstance(payload, dict):
            if payload.get("isError") is True or payload.get("error"):
                raise ValueError("NOTION_TOOL_REJECTED")
            if "structuredContent" in payload and isinstance(payload["structuredContent"], dict):
                payload = payload["structuredContent"]
                continue
            if isinstance(payload.get("content"), list):
                blocks = payload["content"]
                if len(blocks) != 1 or not isinstance(blocks[0], dict) or blocks[0].get("type") != "text":
                    raise ValueError("NOTION_TOOL_CONTENT_AMBIGUOUS")
                payload = blocks[0].get("text")
                continue
            if isinstance(payload.get("text"), str) and payload["text"].lstrip().startswith("{"):
                payload = payload["text"]
                continue
            return payload
        if isinstance(payload, str) and payload.lstrip().startswith("{"):
            if len(payload) > 500000:
                raise ValueError("NOTION_INPUT_INVALID")
            payload = json.loads(payload)
            continue
        return payload
    raise ValueError("NOTION_TOOL_WRAPPER_DEPTH_INVALID")


def page_evidence(payload, cu_url, page_url, max_chars=1500):
    if not isinstance(page_url,str) or not page_url.startswith("https://app.notion.com/p/"):
        raise ValueError("PAGE_URL_INVALID")
    payload = unwrap_tool_response(payload)
    raw = payload.get("text") if isinstance(payload, dict) else payload
    if not isinstance(raw,str) or len(raw)>250000:
        raise ValueError("PAGE_INPUT_INVALID")
    if not isinstance(raw,str) or "<page " not in raw or "<content>" not in raw:
        raise ValueError("PAGE_FORMAT_INVALID")
    header=raw.split("<content>",1)[0]
    page_tags = re.findall(r'<page\s+url="([^"]+)"', header)
    if len(page_tags) != 1 or unescape(page_tags[0]) != page_url:
        raise ValueError("PAGE_SOURCE_MISMATCH")
    contents=raw.split("<content>",1)[1].split("</content>",1)[0]
    if cu_url not in contents:
        return []
    clean=unescape(re.sub(r"<[^>]*>"," ",contents))
    loc=clean.find(cu_url)
    summary=clean[max(0,loc-300):loc+max_chars-300].strip()[:max_chars]
    return [{"cu_url":cu_url,"kind":"OBSERVATION","state":"UNKNOWN",
             "summary":summary,"notion_url":page_url}]

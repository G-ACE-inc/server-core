"""Extract bounded attributable context from existing Notion page fetch results.

No free-text inference of adoption; preserve page as evidence with UNKNOWN state.
"""
import json
import re
from html import unescape

def page_evidence(payload, cu_url, page_url, max_chars=1500):
    if not isinstance(page_url,str) or not page_url.startswith("https://app.notion.com/p/"):
        raise ValueError("PAGE_URL_INVALID")
    if isinstance(payload,dict):
        raw=payload.get("structuredContent",{}).get("text") if isinstance(payload.get("structuredContent"),dict) else payload.get("text")
    else:
        raw=payload
    if not isinstance(raw,str) or len(raw)>250000:
        raise ValueError("PAGE_INPUT_INVALID")
    if raw.startswith("{"):
        data=json.loads(raw)
        raw=data.get("text","")
    if not isinstance(raw,str) or "<page " not in raw or "<content>" not in raw:
        raise ValueError("PAGE_FORMAT_INVALID")
    contents=raw.split("<content>",1)[1].split("</content>",1)[0]
    if cu_url not in contents:
        return []
    clean=unescape(re.sub(r"<[^>]*>"," ",contents))
    loc=clean.find(cu_url)
    summary=clean[max(0,loc-300):loc+max_chars-300].strip()[:max_chars]
    return [{"cu_url":cu_url,"kind":"OBSERVATION","state":"UNKNOWN",
             "summary":summary,"notion_url":page_url}]

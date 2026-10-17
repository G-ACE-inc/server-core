"""Parse bounded Notion discussion evidence for an existing GitHub CU."""
import xml.etree.ElementTree as ET

def parse_comments(envelope, cu_url):
    try:
        from scripts.chat_notion_page_evidence import unwrap_tool_response
    except ModuleNotFoundError:
        from chat_notion_page_evidence import unwrap_tool_response
    envelope = unwrap_tool_response(envelope)
    if isinstance(envelope, dict):
        envelope = envelope.get("text", "")
    if not isinstance(envelope, str) or len(envelope) > 500000:
        raise ValueError("NOTION_INPUT_INVALID")
    try:
        root = ET.fromstring(envelope)
    except ET.ParseError:
        raise ValueError("NOTION_FORMAT_INVALID") from None
    if root.tag != "discussions":
        raise ValueError("NOTION_FORMAT_INVALID")
    records = []
    for comment in sorted(root.iter("comment"), key=lambda x: x.attrib.get("datetime", ""), reverse=True):
        content = "".join(comment.itertext()).strip()
        url = comment.attrib.get("url", "")
        if cu_url not in content or not url.startswith("https://app.notion.com/"):
            continue
        records.append({"cu_url": cu_url, "kind": "OBSERVATION",
                        "state": "UNKNOWN", "summary": content[:1500],
                        "notion_url": url + "&comment_id=" + comment.attrib.get("id", "")})
        if len(records) >= 40:
            break
    return records

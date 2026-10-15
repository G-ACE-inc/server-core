"""Parse bounded Notion discussion evidence for an existing GitHub CU."""
import xml.etree.ElementTree as ET
import json

def parse_comments(envelope, cu_url):
    if isinstance(envelope, dict):
        envelope = envelope.get("text", "")
    if not isinstance(envelope, str) or len(envelope) > 500000:
        raise ValueError("NOTION_INPUT_INVALID")
    if envelope.lstrip().startswith("{"):
        envelope = json.loads(envelope).get("text", "")
    root = ET.fromstring(envelope)
    if root.tag != "discussions":
        raise ValueError("NOTION_FORMAT_INVALID")
    records = []
    for comment in root.iter("comment"):
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

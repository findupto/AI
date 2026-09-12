import re
from html import unescape


class ResearchEngine:
    """Optional online research adapter. Network access is controlled by Policy."""

    def __init__(self, policy):
        self.policy = policy

    def fetch(self, url: str) -> dict:
        if not self.policy.network_allowed():
            return {"ok": False, "error": "Network access is disabled by policy."}
        try:
            import requests
            response = requests.get(url, timeout=15, headers={"User-Agent": "Findupto-AI/0.1"})
            response.raise_for_status()
            text = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", response.text, flags=re.I)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", unescape(text)).strip()
            return {"ok": True, "url": url, "status": response.status_code, "text": text[:200_000]}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

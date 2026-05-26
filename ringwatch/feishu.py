from __future__ import annotations

from dataclasses import dataclass
import base64
import hashlib
import hmac
import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def gen_feishu_sign(secret: str, timestamp: int) -> str:
    string_to_sign = f"{timestamp}\n{secret}"
    digest = hmac.new(
        string_to_sign.encode("utf-8"),
        b"",
        digestmod=hashlib.sha256,
    ).digest()
    return base64.b64encode(digest).decode("utf-8")


@dataclass
class FeishuClient:
    webhook_url: str
    secret: str | None = None
    timeout: int = 20
    retries: int = 2
    retry_backoff_s: float = 1.0

    def build_payload(self, card: dict) -> dict:
        payload = {"msg_type": "interactive", "card": card}
        if self.secret:
            timestamp = int(time.time())
            payload["timestamp"] = str(timestamp)
            payload["sign"] = gen_feishu_sign(self.secret, timestamp)
        return payload

    def send_card(self, card: dict) -> dict:
        payload = self.build_payload(card)
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = Request(
            self.webhook_url,
            data=body,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        parsed = urlparse(self.webhook_url)
        host = parsed.hostname or "<unknown-host>"

        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    text = response.read().decode("utf-8", errors="replace")
                break
            except (HTTPError, URLError) as exc:
                last_error = exc
                if attempt >= self.retries:
                    return {
                        "error": f"Feishu webhook request failed after {attempt + 1} attempts",
                        "host": host,
                        "exception": repr(exc),
                    }
                time.sleep(self.retry_backoff_s * (2**attempt))
            except Exception as exc:  # noqa: BLE001 - keep daily digest resilient.
                last_error = exc
                return {
                    "error": "Feishu webhook request failed",
                    "host": host,
                    "exception": repr(exc),
                }
        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            return {"raw": text}
        if isinstance(result, dict):
            return result
        return {"raw": result}

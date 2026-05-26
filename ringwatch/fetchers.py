from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from email.utils import parsedate_to_datetime
from html import unescape
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
import re
import xml.etree.ElementTree as ET

from .config import AgentConfig
from .models import Competitor, NewsItem


USER_AGENT = "RingWatch/0.1 (+https://ringconn.com; product-intelligence)"


@dataclass
class FetchResult:
    items: list[NewsItem] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def build_google_news_url(query: str, locale: str) -> str:
    return f"https://news.google.com/rss/search?q={quote_plus(query)}&{locale}"


def fetch_url(url: str, timeout: int = 20) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is not None:
        return parsed.astimezone().replace(tzinfo=None)
    return parsed


def strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", unescape(text)).strip()


def _child_text(node: ET.Element, tag: str) -> str:
    child = node.find(tag)
    return (child.text or "").strip() if child is not None else ""


def parse_rss(xml_text: str, competitor: Competitor, query: str) -> list[NewsItem]:
    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    if channel is None:
        return []

    items: list[NewsItem] = []
    for item in channel.findall("item"):
        title = strip_html(_child_text(item, "title"))
        url = _child_text(item, "link")
        source_node = item.find("source")
        source = (source_node.text or "").strip() if source_node is not None else ""
        summary = strip_html(_child_text(item, "description"))
        published = parse_datetime(_child_text(item, "pubDate"))
        if not title or not url:
            continue
        items.append(
            NewsItem(
                competitor_id=competitor.id,
                competitor_name=competitor.name,
                query=query,
                title=title,
                url=url,
                source=source or "Google News",
                published=published,
                summary=summary,
            )
        )
    return items


def fetch_competitor_news(
    competitor: Competitor,
    config: AgentConfig,
    timeout: int = 20,
) -> FetchResult:
    result = FetchResult()
    for query in competitor.queries:
        url = build_google_news_url(query, config.google_news_locale)
        try:
            xml_text = fetch_url(url, timeout=timeout)
            result.items.extend(parse_rss(xml_text, competitor, query))
        except Exception as exc:  # noqa: BLE001 - keep the daily digest resilient.
            result.errors.append(f"{competitor.name}: {query}: {exc}")
    return result

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
import re


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold()).strip()


@dataclass
class Competitor:
    id: str
    name: str
    company: str
    priority: str
    products: list[str]
    rationale: str
    queries: list[str]
    official_urls: list[str] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, data: dict) -> "Competitor":
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            company=str(data.get("company", data["name"])),
            priority=str(data.get("priority", "watchlist")),
            products=[str(item) for item in data.get("products", [])],
            rationale=str(data.get("rationale", "")),
            queries=[str(item) for item in data.get("queries", [])],
            official_urls=[str(item) for item in data.get("official_urls", [])],
        )


@dataclass
class NewsItem:
    competitor_id: str
    competitor_name: str
    query: str
    title: str
    url: str
    source: str
    published: datetime | None = None
    summary: str = ""
    score: int = 0
    matched_terms: list[str] = field(default_factory=list)

    @property
    def key(self) -> str:
        basis = "|".join(
            [
                self.competitor_id,
                normalize_text(self.title),
                normalize_text(self.source),
                self.url.split("?", 1)[0],
            ]
        )
        return sha256(basis.encode("utf-8")).hexdigest()

    @property
    def display_date(self) -> str:
        if self.published is None:
            return "unknown date"
        return self.published.strftime("%Y-%m-%d")

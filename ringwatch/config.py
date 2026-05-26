from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from .models import Competitor


@dataclass
class AgentConfig:
    report_title: str
    lookback_days: int
    max_items: int
    min_score: int
    timezone: str
    send_empty_report: bool
    google_news_locale: str
    product_keywords: list[str]
    update_keywords: list[str]
    exclude_keywords: list[str]
    competitors: list[Competitor]


def load_config(path: str | Path) -> AgentConfig:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)

    agent = raw.get("agent", {})
    competitors = [Competitor.from_mapping(item) for item in raw.get("competitors", [])]
    if not competitors:
        raise ValueError(f"No competitors configured in {config_path}")

    return AgentConfig(
        report_title=str(agent.get("report_title", "Competitor Product Updates")),
        lookback_days=int(agent.get("lookback_days", 7)),
        max_items=int(agent.get("max_items", 12)),
        min_score=int(agent.get("min_score", 3)),
        timezone=str(agent.get("timezone", "Asia/Shanghai")),
        send_empty_report=bool(agent.get("send_empty_report", True)),
        google_news_locale=str(agent.get("google_news_locale", "hl=en-US&gl=US&ceid=US:en")),
        product_keywords=[str(item) for item in agent.get("product_keywords", [])],
        update_keywords=[str(item) for item in agent.get("update_keywords", [])],
        exclude_keywords=[str(item) for item in agent.get("exclude_keywords", [])],
        competitors=competitors,
    )

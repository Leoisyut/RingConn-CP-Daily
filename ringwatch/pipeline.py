from __future__ import annotations

from collections import OrderedDict
from datetime import datetime, timedelta

from .config import AgentConfig
from .models import NewsItem, normalize_text
from .state import SeenState


PRIORITY_SCORE = {
    "core": 3,
    "important": 2,
    "regional": 1,
    "watchlist": 1,
    "adjacent": 0,
}


def _relevance_terms(item: NewsItem, product_names: list[str] | None) -> list[str]:
    terms = [item.competitor_name]
    terms.extend(product_names or [])
    if "/" in item.competitor_name:
        terms.extend(part.strip() for part in item.competitor_name.split("/"))
    return [term for term in terms if len(term.strip()) >= 3]


def score_item(
    item: NewsItem,
    config: AgentConfig,
    priority: str,
    product_names: list[str] | None = None,
) -> NewsItem:
    haystack = normalize_text(" ".join([item.title, item.summary, item.source]))
    score = PRIORITY_SCORE.get(priority, 0)
    matched: list[str] = []

    relevant_terms = []
    for term in _relevance_terms(item, product_names):
        if normalize_text(term) in haystack:
            relevant_terms.append(term)

    if relevant_terms:
        score += 3
        matched.extend(f"brand:{term}" for term in relevant_terms[:3])
    else:
        score -= 3

    for term in config.product_keywords:
        if normalize_text(term) in haystack:
            score += 1
            matched.append(term)

    for term in config.update_keywords:
        if normalize_text(term) in haystack:
            score += 2
            matched.append(term)

    for term in config.exclude_keywords:
        if normalize_text(term) in haystack:
            score -= 8
            matched.append(f"exclude:{term}")

    if item.published is not None and item.published >= datetime.utcnow() - timedelta(days=2):
        score += 1

    item.score = score
    item.matched_terms = sorted(set(matched))
    return item


def within_lookback(item: NewsItem, lookback_days: int) -> bool:
    if item.published is None:
        return True
    return item.published >= datetime.utcnow() - timedelta(days=lookback_days)


def dedupe_items(items: list[NewsItem]) -> list[NewsItem]:
    deduped: OrderedDict[str, NewsItem] = OrderedDict()
    for item in items:
        title_key = normalize_text(item.title)
        key = f"{item.competitor_id}|{title_key}"
        existing = deduped.get(key)
        if existing is None or item.score > existing.score:
            deduped[key] = item
    return list(deduped.values())


def select_report_items(
    items: list[NewsItem],
    config: AgentConfig,
    state: SeenState,
    priority_by_competitor: dict[str, str],
    products_by_competitor: dict[str, list[str]] | None = None,
    lookback_days: int | None = None,
    limit: int | None = None,
    min_score: int | None = None,
    include_seen: bool = False,
) -> list[NewsItem]:
    lookback = lookback_days if lookback_days is not None else config.lookback_days
    threshold = min_score if min_score is not None else config.min_score
    max_items = limit if limit is not None else config.max_items

    scored = [
        score_item(
            item,
            config,
            priority_by_competitor.get(item.competitor_id, "watchlist"),
            (products_by_competitor or {}).get(item.competitor_id, []),
        )
        for item in items
        if within_lookback(item, lookback)
    ]
    candidates = [
        item
        for item in scored
        if item.score >= threshold and (include_seen or not state.is_seen(item))
    ]
    candidates = dedupe_items(candidates)
    return sorted(
        candidates,
        key=lambda item: (
            item.score,
            item.published or datetime.min,
            item.competitor_name,
        ),
        reverse=True,
    )[:max_items]

from __future__ import annotations

from datetime import datetime
from textwrap import shorten
from zoneinfo import ZoneInfo

from .config import AgentConfig
from .models import NewsItem


def _now_for_config(config: AgentConfig) -> datetime:
    try:
        return datetime.now(ZoneInfo(config.timezone))
    except Exception:  # noqa: BLE001 - fallback when timezone is invalid/missing.
        return datetime.utcnow()


def build_text_report(config: AgentConfig, items: list[NewsItem], errors: list[str]) -> str:
    generated_at = _now_for_config(config).strftime("%Y-%m-%d %H:%M")
    lines = [config.report_title, f"生成时间: {generated_at}"]
    if not items:
        lines.append("")
        lines.append("暂无新的高置信竞品产品动态。")
    else:
        for index, item in enumerate(items, start=1):
            lines.extend(
                [
                    "",
                    f"{index}. [{item.competitor_name}] {item.title}",
                    f"   来源: {item.source} | 日期: {item.display_date} | 分数: {item.score}",
                    f"   链接: {item.url}",
                ]
            )
            if item.summary:
                lines.append(f"   摘要: {shorten(item.summary, width=220, placeholder='...')}")
            if item.matched_terms:
                lines.append(f"   命中: {', '.join(item.matched_terms[:8])}")

    if errors:
        lines.append("")
        lines.append(f"抓取异常: {len(errors)} 个源失败，已跳过。")
        for error in errors[:5]:
            lines.append(f"- {error}")
    return "\n".join(lines)


def _escape_lark_md(value: str) -> str:
    return value.replace("\n", " ").strip()


def build_feishu_card(config: AgentConfig, items: list[NewsItem], errors: list[str]) -> dict:
    generated_at = _now_for_config(config).strftime("%Y-%m-%d %H:%M")
    elements: list[dict] = [
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**生成时间**: {generated_at}\n**新增动态**: {len(items)} 条",
            },
        }
    ]

    if not items:
        elements.append(
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "今日暂无新的高置信竞品产品动态。可在配置中降低 `min_score` 或扩大 `lookback_days`。",
                },
            }
        )
    else:
        for index, item in enumerate(items, start=1):
            summary = shorten(item.summary, width=180, placeholder="...") if item.summary else ""
            content = (
                f"**{index}. [{_escape_lark_md(item.competitor_name)}] "
                f"[{_escape_lark_md(item.title)}]({item.url})**\n"
                f"来源: {_escape_lark_md(item.source)} | 日期: {item.display_date} | 分数: {item.score}"
            )
            if summary:
                content += f"\n{_escape_lark_md(summary)}"
            if item.matched_terms:
                content += f"\n命中: {', '.join(item.matched_terms[:6])}"
            elements.append({"tag": "hr"})
            elements.append({"tag": "div", "text": {"tag": "lark_md", "content": content}})

    if errors:
        elements.append({"tag": "hr"})
        elements.append(
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"抓取异常: {len(errors)} 个源失败，已自动跳过。请查看运行日志。",
                },
            }
        )

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "template": "blue",
            "title": {"tag": "plain_text", "content": config.report_title},
        },
        "elements": elements,
    }

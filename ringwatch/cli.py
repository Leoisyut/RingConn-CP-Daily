from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path
import sys

from .config import AgentConfig, load_config
from .fetchers import FetchResult, fetch_competitor_news
from .feishu import FeishuClient
from .formatters import build_feishu_card, build_text_report
from .pipeline import select_report_items
from .state import SeenState


def load_dotenv(path: str | Path = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def default_config_path() -> str:
    return os.getenv("RINGWATCH_CONFIG", "config/competitors.json")


def default_state_path() -> str:
    return os.getenv("RINGWATCH_STATE", ".ringwatch/state.json")


def fetch_all(config: AgentConfig) -> FetchResult:
    merged = FetchResult()
    with ThreadPoolExecutor(max_workers=min(8, len(config.competitors))) as executor:
        futures = {
            executor.submit(fetch_competitor_news, competitor, config): competitor
            for competitor in config.competitors
        }
        for future in as_completed(futures):
            result = future.result()
            merged.items.extend(result.items)
            merged.errors.extend(result.errors)
    return merged


def build_priority_map(config: AgentConfig) -> dict[str, str]:
    return {competitor.id: competitor.priority for competitor in config.competitors}


def build_products_map(config: AgentConfig) -> dict[str, list[str]]:
    return {competitor.id: competitor.products for competitor in config.competitors}


def feishu_send_succeeded(response: dict) -> bool:
    if "error" in response:
        return False
    if "code" in response:
        return response.get("code") == 0
    if "StatusCode" in response:
        return response.get("StatusCode") == 0
    return "raw" not in response


def run_command(args: argparse.Namespace) -> int:
    load_dotenv(args.env_file)
    config = load_config(args.config)
    state = SeenState.load(args.state)

    fetch_result = fetch_all(config)
    selected = select_report_items(
        fetch_result.items,
        config,
        state,
        build_priority_map(config),
        products_by_competitor=build_products_map(config),
        lookback_days=args.lookback_days,
        limit=args.limit,
        min_score=args.min_score,
        include_seen=args.include_seen,
    )

    report = build_text_report(config, selected, fetch_result.errors)
    print(report)

    should_send = not args.dry_run and (selected or args.send_empty or config.send_empty_report)
    if should_send:
        webhook_url = os.getenv("FEISHU_WEBHOOK_URL", "").strip()
        if not webhook_url:
            print("FEISHU_WEBHOOK_URL is required unless --dry-run is used.", file=sys.stderr)
            return 2
        client = FeishuClient(
            webhook_url=webhook_url,
            secret=os.getenv("FEISHU_WEBHOOK_SECRET") or None,
        )
        response = client.send_card(build_feishu_card(config, selected, fetch_result.errors))
        print(f"Feishu response: {response}")
        if not feishu_send_succeeded(response):
            print("Feishu delivery failed; seen-state was not updated.", file=sys.stderr)
            return 3
        state.mark(selected)
        state.save()
    elif args.mark_seen:
        state.mark(selected)
        state.save()
        print(f"Marked {len(selected)} items as seen in {state.path}.")

    return 0


def list_competitors_command(args: argparse.Namespace) -> int:
    load_dotenv(args.env_file)
    config = load_config(args.config)
    for competitor in config.competitors:
        products = ", ".join(competitor.products)
        print(f"{competitor.priority:9} {competitor.name:28} {products}")
    return 0


def send_test_command(args: argparse.Namespace) -> int:
    load_dotenv(args.env_file)
    config = load_config(args.config)
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL", "").strip()
    if not webhook_url:
        print("FEISHU_WEBHOOK_URL is required.", file=sys.stderr)
        return 2
    client = FeishuClient(webhook_url=webhook_url, secret=os.getenv("FEISHU_WEBHOOK_SECRET") or None)
    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "template": "green",
            "title": {"tag": "plain_text", "content": "RingWatch 测试消息"},
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"{config.report_title} 已连通。下一步可运行 `python3 -m ringwatch run`。",
                },
            }
        ],
    }
    response = client.send_card(card)
    print(response)
    if not feishu_send_succeeded(response):
        return 3
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ringwatch")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--config", default=default_config_path())
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Fetch, dedupe, rank, and optionally send to Feishu.")
    run_parser.add_argument("--state", default=default_state_path())
    run_parser.add_argument("--dry-run", action="store_true")
    run_parser.add_argument("--mark-seen", action="store_true")
    run_parser.add_argument("--include-seen", action="store_true")
    run_parser.add_argument("--send-empty", action="store_true")
    run_parser.add_argument("--lookback-days", type=int)
    run_parser.add_argument("--limit", type=int)
    run_parser.add_argument("--min-score", type=int)
    run_parser.set_defaults(func=run_command)

    list_parser = subparsers.add_parser("list-competitors", help="Show configured competitors.")
    list_parser.set_defaults(func=list_competitors_command)

    test_parser = subparsers.add_parser("send-test", help="Send a Feishu webhook test card.")
    test_parser.set_defaults(func=send_test_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)

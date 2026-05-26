import unittest

from ringwatch.config import AgentConfig
from ringwatch.models import Competitor, NewsItem
from ringwatch.pipeline import select_report_items
from ringwatch.state import SeenState


class PipelineTests(unittest.TestCase):
    def test_selects_relevant_product_update(self):
        competitor = Competitor(
            id="oura",
            name="Oura",
            company="Oura Health",
            priority="core",
            products=["Oura Ring"],
            rationale="",
            queries=[],
        )
        config = AgentConfig(
            report_title="test",
            lookback_days=7,
            max_items=5,
            min_score=3,
            timezone="Asia/Shanghai",
            send_empty_report=True,
            google_news_locale="",
            product_keywords=["ring", "sleep"],
            update_keywords=["launch", "update"],
            exclude_keywords=["coupon"],
            competitors=[competitor],
        )
        items = [
            NewsItem(
                competitor_id="oura",
                competitor_name="Oura",
                query="",
                title="Oura Ring launches new sleep update",
                url="https://example.com/1",
                source="Example",
            ),
            NewsItem(
                competitor_id="oura",
                competitor_name="Oura",
                query="",
                title="Oura Ring coupon roundup",
                url="https://example.com/2",
                source="Example",
            ),
        ]
        selected = select_report_items(
            items,
            config,
            SeenState(path="/tmp/ringwatch-test-state.json"),
            {"oura": "core"},
        )

        self.assertEqual(len(selected), 1)
        self.assertIn("sleep update", selected[0].title)


if __name__ == "__main__":
    unittest.main()

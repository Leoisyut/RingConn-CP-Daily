import unittest

from ringwatch.fetchers import parse_rss
from ringwatch.models import Competitor


RSS = """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <item>
      <title>Oura Ring app adds new sleep feature</title>
      <link>https://example.com/oura-sleep</link>
      <pubDate>Tue, 12 May 2026 01:00:00 GMT</pubDate>
      <source url="https://example.com">Example News</source>
      <description><![CDATA[<p>The update improves readiness and sleep tracking.</p>]]></description>
    </item>
  </channel>
</rss>
"""


class RssTests(unittest.TestCase):
    def test_parse_rss_item(self):
        competitor = Competitor(
            id="oura",
            name="Oura",
            company="Oura Health",
            priority="core",
            products=["Oura Ring"],
            rationale="",
            queries=["Oura Ring update"],
        )
        items = parse_rss(RSS, competitor, "Oura Ring update")

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].source, "Example News")
        self.assertIn("readiness", items[0].summary)


if __name__ == "__main__":
    unittest.main()

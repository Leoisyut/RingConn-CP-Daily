import unittest

from ringwatch.feishu import FeishuClient, gen_feishu_sign


class FeishuTests(unittest.TestCase):
    def test_signature_is_stable(self):
        self.assertEqual(
            gen_feishu_sign("test-secret", 1700000000),
            "mbm4Y4oluIPQ00qlBIhX8vAZ0EKv3nw0LuTb91jPL84=",
        )

    def test_signed_payload_contains_signature_fields(self):
        client = FeishuClient("https://example.invalid/hook", secret="secret")
        payload = client.build_payload({"elements": []})

        self.assertEqual(payload["msg_type"], "interactive")
        self.assertIn("timestamp", payload)
        self.assertIn("sign", payload)


if __name__ == "__main__":
    unittest.main()

import base64
import importlib
import json
import os
import sys
import unittest


for key, value in {
    "BUCKET_NAME": "bucket",
    "DEPOT_KEY": "depo.xlsx",
    "TRANSPORT_KEY": "tasima.xlsx",
    "COGNITO_ISSUER": "https://issuer.example",
    "COGNITO_CLIENT_ID": "client",
    "COGNITO_LOGIN_DOMAIN": "https://login.example",
    "QUERY_LIMIT_TABLE": "limits",
}.items():
    os.environ.setdefault(key, value)

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
app = importlib.import_module("app")


class DailyLimitTests(unittest.TestCase):
    def test_counts_only_query_data_tool_calls(self):
        query = {"method": "tools/call", "params": {"name": "query_data"}}

        self.assertEqual(app._query_call_name({"body": json.dumps(query)}), "query_data")
        self.assertEqual(
            app._query_call_name(
                {
                    "body": base64.b64encode(json.dumps(query).encode()).decode(),
                    "isBase64Encoded": True,
                }
            ),
            "query_data",
        )
        self.assertIsNone(app._query_call_name({"body": "not-json"}))
        self.assertIsNone(app._query_call_name({"body": "[]"}))

    def test_query_data_uses_configured_daily_limit(self):
        class FakeDynamoDB:
            def __init__(self):
                self.kwargs = None

            def update_item(self, **kwargs):
                self.kwargs = kwargs

        fake = FakeDynamoDB()
        app._ddb_client = fake
        event = {
            "requestContext": {
                "authorizer": {"jwt": {"claims": {"sub": "user-123"}}}
            },
            "body": json.dumps(
                {"method": "tools/call", "params": {"name": "query_data"}}
            ),
        }

        self.assertIsNone(app._enforce_daily_query_limit(event))
        self.assertEqual(fake.kwargs["ExpressionAttributeValues"][":limit"], {"N": "30"})
        self.assertRegex(fake.kwargs["Key"]["user_day"]["S"], r"^user-123#\d{4}-\d{2}-\d{2}$")

    def test_query_data_returns_429_when_limit_is_exhausted(self):
        class ConditionalCheckFailed(Exception):
            response = {"Error": {"Code": "ConditionalCheckFailedException"}}

        class FullDynamoDB:
            def update_item(self, **kwargs):
                raise ConditionalCheckFailed()

        app._ddb_client = FullDynamoDB()
        event = {
            "requestContext": {
                "authorizer": {"jwt": {"claims": {"sub": "user-123"}}}
            },
            "body": json.dumps(
                {"method": "tools/call", "params": {"name": "query_data"}}
            ),
        }

        response = app._enforce_daily_query_limit(event)
        self.assertEqual(response["statusCode"], 429)


if __name__ == "__main__":
    unittest.main()

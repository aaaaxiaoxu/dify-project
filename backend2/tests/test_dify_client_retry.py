import os
import sys
import unittest
from unittest.mock import Mock, patch

import requests


BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from utils.dify_client import DifyClient


class DifyClientRetryTest(unittest.TestCase):
    def test_post_workflow_retries_after_timeout(self):
        client = DifyClient()
        ok_response = Mock(status_code=200)

        with patch(
            "utils.dify_client.requests.post",
            side_effect=[requests.Timeout("timed out"), ok_response],
        ) as post:
            response, error = client._post_workflow_with_retries(
                "https://api.example.test/workflows/run",
                {"Authorization": "Bearer test"},
                {"inputs": {}},
                timeout=1,
                max_retries=1,
                retry_delay=0,
            )

        self.assertIs(response, ok_response)
        self.assertIsNone(error)
        self.assertEqual(post.call_count, 2)


if __name__ == "__main__":
    unittest.main()

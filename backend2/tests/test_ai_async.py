import os
import sys
import unittest
from unittest.mock import patch


BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from routes.ai import _merge_writing_feedback


class AIAsyncBehaviorTest(unittest.TestCase):
    def test_merge_writing_feedback_does_not_call_dify_by_default(self):
        with patch("routes.ai.dify_client.generate_writing_suggestion") as generate_writing:
            payload = _merge_writing_feedback({}, "今天非常开心。")

        generate_writing.assert_not_called()
        self.assertIn("writing_suggestion", payload)


if __name__ == "__main__":
    unittest.main()

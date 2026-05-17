import os
import sys
import unittest
from datetime import date
from unittest.mock import Mock, patch


BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from models import WorkflowJob
from routes.report import _call_report_workflow_with_retries


class ReportWorkflowRetryTest(unittest.TestCase):
    def test_retry_then_success_uses_dify_source(self):
        calls = [
            (None, "ReadTimeout: timed out"),
            ({"report_title": "测试报告"}, None),
        ]

        with patch("routes.report.dify_client.generate_travel_report_with_error", side_effect=calls):
            result = _call_report_workflow_with_retries(
                {"summary_stats": {}, "report_images": []},
                date(2026, 1, 1),
                date(2026, 1, 2),
                "warm",
                max_retries=2,
                sleep_fn=Mock(),
            )

        self.assertEqual(result["source"], "dify")
        self.assertEqual(result["workflow_status"], WorkflowJob.STATUS_SUCCEEDED)
        self.assertEqual(result["attempts"], 2)
        self.assertIsNone(result["error_message"])

    def test_exhausted_retries_falls_back_to_local(self):
        sleep_fn = Mock()
        with patch(
            "routes.report.dify_client.generate_travel_report_with_error",
            return_value=(None, "HTTP 504: gateway timeout"),
        ):
            result = _call_report_workflow_with_retries(
                {"summary_stats": {}, "report_images": []},
                date(2026, 1, 1),
                date(2026, 1, 2),
                "warm",
                max_retries=1,
                sleep_fn=sleep_fn,
            )

        self.assertEqual(result["source"], "local")
        self.assertEqual(result["workflow_status"], WorkflowJob.STATUS_FAILED)
        self.assertEqual(result["attempts"], 2)
        self.assertIn("504", result["error_message"])
        sleep_fn.assert_called_once()

    def test_missing_dify_config_is_not_retried(self):
        sleep_fn = Mock()
        with patch(
            "routes.report.dify_client.generate_travel_report_with_error",
            return_value=(None, "Dify 报告工作流未配置"),
        ):
            result = _call_report_workflow_with_retries(
                {"summary_stats": {}, "report_images": []},
                date(2026, 1, 1),
                date(2026, 1, 2),
                "warm",
                max_retries=3,
                sleep_fn=sleep_fn,
            )

        self.assertEqual(result["source"], "local")
        self.assertEqual(result["attempts"], 1)
        sleep_fn.assert_not_called()


if __name__ == "__main__":
    unittest.main()

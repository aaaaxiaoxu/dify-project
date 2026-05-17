import os
import sys
import unittest
from datetime import date

from flask import Flask


BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from extensions import db
from models import ReportJob, User, WorkflowJob
from routes.report import (
    _pending_report_job_count,
    _report_max_concurrent_jobs,
    _report_max_pending_jobs_per_user,
)


class ReportConcurrencyTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        self.app.config["REPORT_MAX_CONCURRENT_REPORT_JOBS"] = 2
        self.app.config["REPORT_MAX_PENDING_REPORT_JOBS_PER_USER"] = 3
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()
            db.session.add(
                User(
                    id=1,
                    username="owner",
                    password="pw",
                    nickname="Owner",
                    phone="13800000001",
                )
            )
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def _add_report_job(self, status):
        workflow_job = WorkflowJob(
            user_id=1,
            job_type="report",
            workflow_name="travel_report",
            status=status,
        )
        db.session.add(workflow_job)
        db.session.flush()
        report_job = ReportJob(
            user_id=1,
            workflow_job_id=workflow_job.id,
            status=status,
            range_type="custom",
            start_date=date(2026, 5, 1),
            end_date=date(2026, 5, 2),
            report_style="warm",
        )
        db.session.add(report_job)
        db.session.commit()

    def test_configured_concurrency_limits_are_loaded(self):
        with self.app.app_context():
            self.assertEqual(_report_max_concurrent_jobs(), 2)
            self.assertEqual(_report_max_pending_jobs_per_user(), 3)

    def test_pending_count_only_includes_queued_and_running_jobs(self):
        with self.app.app_context():
            self._add_report_job(ReportJob.STATUS_QUEUED)
            self._add_report_job(ReportJob.STATUS_RUNNING)
            self._add_report_job(ReportJob.STATUS_SUCCEEDED)
            self._add_report_job(ReportJob.STATUS_FAILED)

            self.assertEqual(_pending_report_job_count(1), 2)


if __name__ == "__main__":
    unittest.main()

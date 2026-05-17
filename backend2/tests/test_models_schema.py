import os
import sys
import unittest

from flask import Flask
from sqlalchemy import inspect


BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from extensions import db
from models import ImageAccessLog, ReportJob, SentimentEvalSample, WorkflowJob


class ModelSchemaTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def test_new_tables_are_created(self):
        with self.app.app_context():
            tables = set(inspect(db.engine).get_table_names())

        self.assertIn(WorkflowJob.__tablename__, tables)
        self.assertIn(ReportJob.__tablename__, tables)
        self.assertIn(SentimentEvalSample.__tablename__, tables)
        self.assertIn(ImageAccessLog.__tablename__, tables)

    def test_report_job_has_async_result_columns(self):
        with self.app.app_context():
            columns = {column["name"] for column in inspect(db.engine).get_columns("report_jobs")}

        self.assertIn("status", columns)
        self.assertIn("report_context", columns)
        self.assertIn("report_payload", columns)
        self.assertIn("workflow_job_id", columns)

    def test_image_access_log_has_authorization_columns(self):
        with self.app.app_context():
            columns = {column["name"] for column in inspect(db.engine).get_columns("image_access_logs")}

        self.assertIn("decision", columns)
        self.assertIn("reason", columns)
        self.assertIn("share_link_id", columns)


if __name__ == "__main__":
    unittest.main()

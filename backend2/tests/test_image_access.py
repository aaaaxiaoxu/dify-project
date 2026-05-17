import os
import sys
import unittest
from datetime import date

from flask import Flask


BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from extensions import db
from models import Diary, DiaryImage, ImageAccessLog, ShareLink, User
from utils.image_access import (
    can_access_diary_image,
    get_authorized_cos_url,
    validate_share_token,
)


class ImageAccessTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()
            db.session.add_all(
                [
                    User(id=1, username="owner", password="pw", nickname="Owner", phone="13800000001"),
                    User(id=2, username="other", password="pw", nickname="Other", phone="13800000002"),
                    Diary(
                        id=10,
                        user_id=1,
                        is_draft=False,
                        title="西湖",
                        location="杭州",
                        date=date(2026, 1, 1),
                        emotion="开心",
                        content="今天很开心",
                    ),
                    DiaryImage(
                        id=100,
                        diary_id=10,
                        image_url="https://example.com/media/image/a.jpg",
                        sort_order=0,
                    ),
                    ShareLink(
                        id=200,
                        token="share-token",
                        diary_id=10,
                        user_id=1,
                        view_password="1234",
                        is_active=True,
                    ),
                ]
            )
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def test_owner_can_access_diary_image(self):
        with self.app.app_context():
            allowed, reason, image = can_access_diary_image(1, diary_id=10, image_id=100)

        self.assertTrue(allowed)
        self.assertEqual(image.id, 100)
        self.assertIn("作者", reason)

    def test_other_user_is_denied(self):
        with self.app.app_context():
            allowed, reason, image = can_access_diary_image(2, diary_id=10, image_id=100)

        self.assertFalse(allowed)
        self.assertEqual(image.id, 100)
        self.assertIn("无权", reason)

    def test_share_token_requires_password(self):
        with self.app.app_context():
            allowed, reason, _link = validate_share_token("share-token", password="bad")

        self.assertFalse(allowed)
        self.assertIn("密码", reason)

    def test_authorized_url_records_audit_log(self):
        with self.app.app_context():
            url, reason = get_authorized_cos_url(
                user_id=1,
                diary_id=10,
                image_id=100,
                access_type="report_pdf",
            )
            logs = ImageAccessLog.query.all()

        self.assertEqual(url, "https://example.com/media/image/a.jpg")
        self.assertIn("作者", reason)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].decision, ImageAccessLog.DECISION_ALLOWED)

    def test_denied_access_records_audit_log(self):
        with self.app.app_context():
            url, reason = get_authorized_cos_url(
                user_id=2,
                diary_id=10,
                image_id=100,
                access_type="report_pdf",
            )
            logs = ImageAccessLog.query.all()

        self.assertIsNone(url)
        self.assertIn("无权", reason)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].decision, ImageAccessLog.DECISION_DENIED)


if __name__ == "__main__":
    unittest.main()

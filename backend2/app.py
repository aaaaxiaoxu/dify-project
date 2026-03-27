import os
import sys
import locale
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import inspect, text

# 设置默认编码为utf-8
if sys.version_info[0] == 3:
    import importlib
    importlib.reload(sys)
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import pymysql

# 解决中文编码问题
pymysql.install_as_MySQLdb()

# 显式读取 backend2/.env，避免不同启动目录导致变量加载失败
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from extensions import db, jwt, dify_client
from config import config


def _ensure_diary_is_draft_column():
    inspector = inspect(db.engine)
    if not inspector.has_table('diaries'):
        return

    columns = {column["name"] for column in inspector.get_columns('diaries')}
    if 'is_draft' in columns:
        return

    dialect = db.engine.dialect.name
    if dialect == 'mysql':
        ddl = (
            "ALTER TABLE diaries "
            "ADD COLUMN is_draft BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否草稿'"
        )
    else:
        ddl = "ALTER TABLE diaries ADD COLUMN is_draft BOOLEAN NOT NULL DEFAULT 0"

    try:
        with db.engine.begin() as conn:
            conn.execute(text(ddl))
    except Exception:
        inspector = inspect(db.engine)
        columns = {column["name"] for column in inspector.get_columns('diaries')}
        if 'is_draft' not in columns:
            raise


def _ensure_user_admin_columns():
    """自动补建 users 表的 is_admin 和 is_frozen 列"""
    inspector = inspect(db.engine)
    if not inspector.has_table('users'):
        return

    columns = {column["name"] for column in inspector.get_columns('users')}
    dialect = db.engine.dialect.name

    for col_name, comment in [('is_admin', '是否管理员'), ('is_frozen', '是否冻结')]:
        if col_name in columns:
            continue
        if dialect == 'mysql':
            ddl = (
                f"ALTER TABLE users "
                f"ADD COLUMN {col_name} BOOLEAN NOT NULL DEFAULT FALSE COMMENT '{comment}'"
            )
        else:
            ddl = f"ALTER TABLE users ADD COLUMN {col_name} BOOLEAN NOT NULL DEFAULT 0"
        try:
            with db.engine.begin() as conn:
                conn.execute(text(ddl))
        except Exception:
            inspector = inspect(db.engine)
            columns = {column["name"] for column in inspector.get_columns('users')}
            if col_name not in columns:
                raise


def _ensure_ai_analysis_columns():
    """自动补建 ai_analysis 表新增字段"""
    inspector = inspect(db.engine)
    if not inspector.has_table('ai_analysis'):
        return

    columns = {column["name"] for column in inspector.get_columns('ai_analysis')}
    dialect = db.engine.dialect.name

    column_specs = [
        ('emotion_label', 'VARCHAR(50)', '情感标签'),
        ('memory_point', 'TEXT', '记忆点'),
    ]

    for col_name, col_type, comment in column_specs:
        if col_name in columns:
            continue
        if dialect == 'mysql':
            ddl = (
                f"ALTER TABLE ai_analysis "
                f"ADD COLUMN {col_name} {col_type} NULL COMMENT '{comment}'"
            )
        else:
            ddl = f"ALTER TABLE ai_analysis ADD COLUMN {col_name} {col_type}"
        try:
            with db.engine.begin() as conn:
                conn.execute(text(ddl))
        except Exception:
            inspector = inspect(db.engine)
            columns = {column["name"] for column in inspector.get_columns('ai_analysis')}
            if col_name not in columns:
                raise

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # 初始化扩展
    db.init_app(app)
    jwt.init_app(app)
    dify_client.init_app(app)
    
    # 启用CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # 注册蓝图
    from routes.user import user_bp
    from routes.diary import diary_bp
    from routes.ai import ai_bp
    from routes.map import map_bp
    from routes.share import share_bp
    from routes.file import file_bp
    from routes.stats import stats_bp
    from routes.report import report_bp
    from routes.admin import admin_bp
    
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(diary_bp, url_prefix='/api/diary')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(map_bp, url_prefix='/api/map')
    app.register_blueprint(share_bp, url_prefix='/api/share')
    app.register_blueprint(file_bp, url_prefix='/api/file')
    app.register_blueprint(stats_bp, url_prefix='/api/stats')
    app.register_blueprint(report_bp, url_prefix='/api/report')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    # 启动时自动补建缺失数据表（不会删除已有表和数据）
    with app.app_context():
        db.create_all()
        _ensure_diary_is_draft_column()
        _ensure_user_admin_columns()
        _ensure_ai_analysis_columns()
    
    return app

import os
import sys
import locale
from datetime import datetime
from dotenv import load_dotenv

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

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
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
    
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(diary_bp, url_prefix='/api/diary')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(map_bp, url_prefix='/api/map')
    app.register_blueprint(share_bp, url_prefix='/api/share')
    app.register_blueprint(file_bp, url_prefix='/api/file')

    # 启动时自动补建缺失数据表（不会删除已有表和数据）
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    # 设置环境变量解决编码问题
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    app = create_app()
    # 使用localhost而不是0.0.0.0来避免DNS解析问题
    app.run(debug=True, host='localhost', port=5000)
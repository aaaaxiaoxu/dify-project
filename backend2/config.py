import os
import pytz
from datetime import datetime

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'travel-diary-secret-key'
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'travel-diary-jwt-secret'
    COS_SECRET_ID = os.environ.get('COS_SECRET_ID') or None
    COS_SECRET_KEY = os.environ.get('COS_SECRET_KEY') or None
    COS_REGION = os.environ.get('COS_REGION') or 'ap-guangzhou'
    COS_BUCKET = os.environ.get('COS_BUCKET') or 'diary-1387359490'
    COS_BASE_URL = (os.environ.get('COS_BASE_URL') or 'https://diary-1387359490.cos.ap-guangzhou.myqcloud.com').rstrip('/')
    COS_MEDIA_PREFIX = (os.environ.get('COS_MEDIA_PREFIX') or 'media').strip('/')
    
    # 数据库配置 - 请根据您的实际MySQL配置修改用户名、密码和数据库名
    # 本地
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:diary@python@localhost/travel_diary'
    # 服务器
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:diary%40python@47.110.157.154/travel_diary'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 设置时区为北京时间
    TIMEZONE = pytz.timezone('Asia/Shanghai')
    
    # Dify配置
    DIFY_API_KEY = os.environ.get('DIFY_API_KEY') or 'your-dify-api-key'
    DIFY_API_URL = os.environ.get('DIFY_API_URL') or 'https://api.dify.ai/v1'

    # 腾讯地图 WebService Key（用于经纬度反查地址）
    TENCENT_MAP_KEY = os.environ.get('TENCENT_MAP_KEY') or 'HTJBZ-PMGKN-2E5FT-SH6DO-ZEQYV-BSBWH'
    
    # 确保上传目录存在
    @staticmethod
    def init_app(app):
        if not os.path.exists(Config.UPLOAD_FOLDER):
            os.makedirs(Config.UPLOAD_FOLDER)

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

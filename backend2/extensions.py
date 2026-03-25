from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from utils.dify_client import DifyClient

# 初始化扩展
db = SQLAlchemy()
jwt = JWTManager()
dify_client = DifyClient()
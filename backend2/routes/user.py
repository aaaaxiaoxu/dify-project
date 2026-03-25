from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from sqlalchemy import or_
from models import User
from extensions import db

user_bp = Blueprint('user', __name__)

@user_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    phone = (data.get('phone') or '').strip()
    password = data.get('password') or ''
    # 昵称改为可选：前端不传时使用用户名兜底，满足数据库非空约束
    nickname = (data.get('nickname') or username).strip()
    
    if not username or not phone or not password:
        return jsonify({"msg": "用户名、手机号和密码不能为空"}), 400
    
    # 检查用户名是否已存在
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"msg": "用户名已存在"}), 400
    
    # 创建新用户
    new_user = User(
        username=username,
        phone=phone,
        password=password,  # 在实际应用中应该加密存储
        nickname=nickname
    )
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"msg": "注册成功"}), 201

@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    login_id = (data.get('username') or data.get('phone') or data.get('account') or '').strip()
    password = data.get('password') or ''
    
    if not login_id or not password:
        return jsonify({"msg": "请输入手机号/用户名和密码"}), 400
    
    # 支持“用户名”或“手机号”登录
    user = User.query.filter(
        User.password == password,
        or_(User.username == login_id, User.phone == login_id)
    ).first()
    
    if user is None:
        return jsonify({"msg": "用户名或密码错误"}), 401
    
    # 创建访问令牌
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        "access_token": access_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "phone": user.phone
        }
    }), 200

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    current_user_id = get_jwt_identity()
    
    # 查找用户
    user = User.query.get(current_user_id)
    
    if user is None:
        return jsonify({"msg": "用户不存在"}), 404
    
    return jsonify({
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "phone": user.phone
    }), 200
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from sqlalchemy import or_
from models import User
from extensions import db

user_bp = Blueprint('user', __name__)


def serialize_user(user):
    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "phone": user.phone,
        "avatar_url": user.avatar_url,
        "bio": user.bio,
        "is_admin": user.is_admin,
    }

@user_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    phone = (data.get('phone') or '').strip()
    password = data.get('password') or ''
    # 昵称改为可选：前端不传时使用用户名兜底，满足数据库非空约束
    nickname = (data.get('nickname') or username).strip()
    avatar_url = (data.get('avatar_url') or '').strip() or None
    bio = (data.get('bio') or '').strip() or None
    
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
        nickname=nickname,
        avatar_url=avatar_url,
        bio=bio
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
    
    # 检查用户是否被冻结
    if user.is_frozen:
        return jsonify({"msg": "您的账号已被冻结，请联系管理员"}), 403
    
    # 创建访问令牌
    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        "access_token": access_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "phone": user.phone,
            "avatar_url": user.avatar_url,
            "bio": user.bio,
            "is_admin": user.is_admin
        }
    }), 200


@user_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json() or {}
    account = (data.get('account') or data.get('username') or '').strip()
    phone = (data.get('phone') or '').strip()
    new_password = data.get('new_password') or data.get('password') or ''

    if not account or not phone or not new_password:
        return jsonify({"msg": "账号、手机号和新密码不能为空"}), 400

    user = User.query.filter(
        or_(User.username == account, User.phone == account)
    ).first()

    if user is None:
        return jsonify({"msg": "账号不存在"}), 404

    if user.phone != phone:
        return jsonify({"msg": "手机号校验失败"}), 400

    user.password = new_password

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"msg": "密码重置失败，请稍后重试"}), 500

    return jsonify({"msg": "密码重置成功，请使用新密码登录"}), 200

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    current_user_id = int(get_jwt_identity())
    
    # 查找用户
    user = User.query.get(current_user_id)
    
    if user is None:
        return jsonify({"msg": "用户不存在"}), 404
    
    return jsonify(serialize_user(user)), 200


@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)

    if user is None:
        return jsonify({"msg": "用户不存在"}), 404

    data = request.get_json() or {}
    nickname = data.get('nickname', user.nickname)
    phone = data.get('phone', user.phone)
    avatar_url = data.get('avatar_url', user.avatar_url)
    bio = data.get('bio', user.bio)

    nickname = '' if nickname is None else str(nickname).strip()
    phone = '' if phone is None else str(phone).strip()
    avatar_url = None if avatar_url is None else str(avatar_url).strip()
    bio = None if bio is None else str(bio).strip()

    if not nickname:
        return jsonify({"msg": "昵称不能为空"}), 400

    if not phone:
        return jsonify({"msg": "手机号不能为空"}), 400

    existing_user = User.query.filter(
        User.phone == phone,
        User.id != current_user_id
    ).first()
    if existing_user:
        return jsonify({"msg": "手机号已被其他用户使用"}), 400

    user.nickname = nickname
    user.phone = phone
    user.avatar_url = avatar_url or None
    user.bio = bio or None

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"msg": "个人资料更新失败，请稍后重试"}), 500

    return jsonify({
        "msg": "个人资料更新成功",
        "user": serialize_user(user)
    }), 200

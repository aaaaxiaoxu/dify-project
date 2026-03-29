from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from models import User, Diary, DiaryImage, DiaryVideo, AIAnalysis
from extensions import db
from utils.admin_auth import is_fixed_admin

admin_bp = Blueprint('admin', __name__)


def _require_admin():
    """校验当前用户是否是管理员，返回 (user, error_response)"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    if user is None:
        return None, (jsonify({"msg": "用户不存在"}), 404)
    if not is_fixed_admin(user):
        return None, (jsonify({"msg": "权限不足，需要管理员身份"}), 403)
    return user, None


# ──────────────────────────────── 升级为管理员 ────────────────────────────────
@admin_bp.route('/upgrade', methods=['POST'])
@jwt_required()
def upgrade_to_admin():
    """管理员权限仅保留给固定账号，不支持通过密钥升级"""
    return jsonify({"msg": "管理员权限仅限固定账号，不支持升级"}), 403


# ──────────────────────────────── 检查管理员状态 ────────────────────────────────
@admin_bp.route('/check', methods=['GET'])
@jwt_required()
def check_admin():
    """检查当前用户是否是管理员"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    if user is None:
        return jsonify({"msg": "用户不存在"}), 404
    return jsonify({"is_admin": is_fixed_admin(user)}), 200


# ──────────────────────────────── 用户管理 ────────────────────────────────
@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_all_users():
    """管理员获取所有用户列表"""
    admin, err = _require_admin()
    if err:
        return err

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '', type=str).strip()

    query = User.query
    if keyword:
        query = query.filter(
            db.or_(
                User.username.like(f'%{keyword}%'),
                User.nickname.like(f'%{keyword}%'),
                User.phone.like(f'%{keyword}%'),
            )
        )

    query = query.order_by(User.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    users = []
    for u in pagination.items:
        diary_count = Diary.query.filter_by(user_id=u.id).count()
        users.append({
            "id": u.id,
            "username": u.username,
            "nickname": u.nickname,
            "phone": u.phone,
            "avatar_url": u.avatar_url,
            "is_admin": is_fixed_admin(u),
            "is_frozen": u.is_frozen,
            "diary_count": diary_count,
            "created_at": u.created_at.strftime('%Y-%m-%d %H:%M:%S') if u.created_at else None,
        })

    return jsonify({
        "users": users,
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
    }), 200


@admin_bp.route('/users/<int:user_id>/freeze', methods=['POST'])
@jwt_required()
def freeze_user(user_id):
    """管理员冻结/解冻用户"""
    admin, err = _require_admin()
    if err:
        return err

    target_user = User.query.get(user_id)
    if target_user is None:
        return jsonify({"msg": "目标用户不存在"}), 404

    if is_fixed_admin(target_user):
        return jsonify({"msg": "不能冻结管理员"}), 400

    if target_user.id == admin.id:
        return jsonify({"msg": "不能冻结自己"}), 400

    # 切换冻结状态
    target_user.is_frozen = not target_user.is_frozen
    db.session.commit()

    status = "已冻结" if target_user.is_frozen else "已解冻"
    return jsonify({
        "msg": f"用户 {target_user.username} {status}",
        "is_frozen": target_user.is_frozen,
    }), 200


# ──────────────────────────────── 日记管理 ────────────────────────────────
@admin_bp.route('/diaries', methods=['GET'])
@jwt_required()
def get_all_diaries():
    """管理员获取所有日记列表"""
    admin, err = _require_admin()
    if err:
        return err

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '', type=str).strip()

    query = Diary.query
    if keyword:
        query = query.filter(
            db.or_(
                Diary.title.like(f'%{keyword}%'),
                Diary.location.like(f'%{keyword}%'),
                Diary.content.like(f'%{keyword}%'),
            )
        )

    query = query.order_by(Diary.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    diaries = []
    for d in pagination.items:
        author = User.query.get(d.user_id)
        diaries.append({
            "id": d.id,
            "title": d.title,
            "location": d.location,
            "date": d.date.strftime('%Y-%m-%d') if d.date else None,
            "emotion": d.emotion,
            "content": d.content[:100] + ('...' if len(d.content) > 100 else ''),
            "is_draft": d.is_draft,
            "user_id": d.user_id,
            "author_name": author.nickname if author else '未知用户',
            "author_username": author.username if author else '',
            "image_count": len(d.images) if d.images else 0,
            "created_at": d.created_at.strftime('%Y-%m-%d %H:%M:%S') if d.created_at else None,
        })

    return jsonify({
        "diaries": diaries,
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
    }), 200


@admin_bp.route('/diaries/<int:diary_id>', methods=['DELETE'])
@jwt_required()
def delete_diary(diary_id):
    """管理员删除日记"""
    admin, err = _require_admin()
    if err:
        return err

    diary = Diary.query.get(diary_id)
    if diary is None:
        return jsonify({"msg": "日记不存在"}), 404

    db.session.delete(diary)
    db.session.commit()
    return jsonify({"msg": "日记已删除"}), 200

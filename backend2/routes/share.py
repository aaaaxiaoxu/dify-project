from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import uuid
from sqlalchemy.orm import selectinload

from models import Diary

share_bp = Blueprint('share', __name__)

# 存储分享链接（实际项目中应使用数据库存储）
shares = []

@share_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_share():
    current_user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    diary_id = data.get('diary_id')
    if not diary_id:
        return jsonify({"msg": "diary_id 不能为空"}), 400
    
    # 查找日记
    diary = Diary.query.filter_by(id=diary_id, user_id=current_user_id).first()
    
    if diary is None:
        return jsonify({"msg": "日记不存在"}), 404
    
    # 生成分享链接
    share_token = str(uuid.uuid4())
    share_link = f"http://localhost:5000/api/share/{share_token}"
    
    # 保存分享信息
    share_info = {
        "token": share_token,
        "diary_id": diary_id,
        "user_id": current_user_id,
        "link": share_link,
        "created_at": "2023-05-20T10:00:00Z"  # 实际应用中应使用当前时间
    }
    shares.append(share_info)
    
    return jsonify({
        "share_link": share_link,
        "msg": "分享链接生成成功"
    }), 200

@share_bp.route('/<token>', methods=['GET'])
def get_share(token):
    # 查找分享信息
    share_info = None
    for s in shares:
        if s['token'] == token:
            share_info = s
            break
    
    if share_info is None:
        return jsonify({"msg": "分享链接不存在或已过期"}), 404
    
    # 查找日记
    diary = (
        Diary.query.options(
            selectinload(Diary.images),
            selectinload(Diary.videos),
        )
        .filter_by(id=share_info['diary_id'])
        .first()
    )
    
    if diary is None:
        return jsonify({"msg": "日记不存在"}), 404
    
    # 返回公开的日记信息（不包含敏感信息）
    public_diary = {
        "title": diary.title,
        "location": diary.location,
        "date": diary.date.isoformat() if diary.date else None,
        "emotion": diary.emotion,
        "content": diary.content,
        "images": [image.image_url for image in diary.images],
        "videos": [{"url": video.video_url, "thumbnail": video.thumbnail_url} for video in diary.videos],
        "created_at": diary.created_at.isoformat() if diary.created_at else None
    }
    
    return jsonify(public_diary), 200

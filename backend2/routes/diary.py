from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date, datetime
from sqlalchemy.orm import selectinload

from models import Diary, DiaryImage, DiaryVideo
from extensions import db
from utils.html_sanitize import (
    diary_html_is_effectively_empty,
    sanitize_diary_html,
)

diary_bp = Blueprint('diary', __name__)


def _parse_client_coords(lat_raw, lng_raw):
    """客户端提交的经纬度（须先通过「解析为经纬度」或定位获得）。"""
    if lat_raw is None or lng_raw is None:
        return None
    try:
        la = float(lat_raw)
        lo = float(lng_raw)
    except (TypeError, ValueError):
        return None
    if not (-90 <= la <= 90 and -180 <= lo <= 180):
        return None
    return la, lo


def _parse_date_value(value):
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        # 兼容 "YYYY-MM-DD" 与完整 ISO 时间字符串
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    raise ValueError("date 字段格式错误")


def _is_remote_url(value):
    return isinstance(value, str) and value.startswith(("http://", "https://"))


def _normalize_images(images):
    if images is None:
        return []
    if not isinstance(images, list):
        raise ValueError("images 字段格式错误，必须是 URL 数组")

    normalized = []
    for index, image_url in enumerate(images):
        if not isinstance(image_url, str) or not image_url.strip():
            raise ValueError(f"第 {index + 1} 张图片格式错误")
        image_url = image_url.strip()
        if not _is_remote_url(image_url):
            raise ValueError("图片尚未上传完成，请先上传图片再保存日记")
        normalized.append(image_url)
    return normalized


def _normalize_videos(videos):
    if videos is None:
        return []
    if not isinstance(videos, list):
        raise ValueError("videos 字段格式错误，必须是对象数组")

    normalized = []
    for index, video_data in enumerate(videos):
        if not isinstance(video_data, dict):
            raise ValueError(f"第 {index + 1} 个视频格式错误")

        video_url = video_data.get("url")
        thumbnail_url = video_data.get("thumbnail")
        video_url = video_url.strip() if isinstance(video_url, str) else ""
        thumbnail_url = thumbnail_url.strip() if isinstance(thumbnail_url, str) else None

        if not video_url or not _is_remote_url(video_url):
            raise ValueError("视频尚未上传完成，请先上传视频再保存日记")
        if thumbnail_url and not _is_remote_url(thumbnail_url):
            raise ValueError("视频缩略图地址无效")

        normalized.append({
            "url": video_url,
            "thumbnail": thumbnail_url or None,
        })
    return normalized


def _serialize_diary(diary):
    return {
        "id": diary.id,
        "user_id": diary.user_id,
        "title": diary.title,
        "location": diary.location,
        "latitude": float(diary.latitude) if diary.latitude else None,
        "longitude": float(diary.longitude) if diary.longitude else None,
        "date": diary.date.isoformat() if diary.date else None,
        "emotion": diary.emotion,
        "content": diary.content,
        "images": [image.image_url for image in diary.images],
        "videos": [{"url": video.video_url, "thumbnail": video.thumbnail_url} for video in diary.videos],
        "created_at": diary.created_at.isoformat() if diary.created_at else None,
    }

@diary_bp.route('/list', methods=['GET'])
@jwt_required()
def get_diary_list():
    current_user_id = int(get_jwt_identity())
    
    # 筛选出当前用户的日记
    user_diaries = (
        Diary.query.options(
            selectinload(Diary.images),
            selectinload(Diary.videos),
        )
        .filter_by(user_id=current_user_id)
        .order_by(Diary.created_at.desc())
        .all()
    )
    
    return jsonify([_serialize_diary(diary) for diary in user_diaries]), 200

@diary_bp.route('/detail/<int:diary_id>', methods=['GET'])
@jwt_required()
def get_diary_detail(diary_id):
    current_user_id = int(get_jwt_identity())
    
    # 查找日记
    diary = (
        Diary.query.options(
            selectinload(Diary.images),
            selectinload(Diary.videos),
        )
        .filter_by(id=diary_id, user_id=current_user_id)
        .first()
    )
    
    if diary is None:
        return jsonify({"msg": "日记不存在"}), 404

    return jsonify(_serialize_diary(diary)), 200

@diary_bp.route('/create', methods=['POST'])
@jwt_required()
def create_diary():
    current_user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    required_fields = ["title", "location", "date", "emotion", "content"]
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return jsonify({"msg": f"缺少必填字段: {', '.join(missing)}"}), 400

    try:
        parsed_date = _parse_date_value(data.get("date"))
    except Exception:
        return jsonify({"msg": "date 字段格式错误，需为 YYYY-MM-DD 或 ISO 时间"}), 400

    content_html = sanitize_diary_html(data.get("content"))
    if diary_html_is_effectively_empty(content_html):
        return jsonify({"msg": "内容不能为空"}), 400

    try:
        images = _normalize_images(data.get('images'))
        videos = _normalize_videos(data.get('videos'))
    except ValueError as exc:
        return jsonify({"msg": str(exc)}), 400

    parsed = _parse_client_coords(data.get("latitude"), data.get("longitude"))
    if not parsed:
        return jsonify(
            {
                "msg": "请先在前端点击「解析为经纬度」或使用「获取当前位置」，再保存日记",
            }
        ), 400
    la, lo = parsed

    # 创建新日记（经纬度仅接受客户端解析/定位结果，避免在保存接口内再调地图导致 macOS 下 worker 不稳定）
    new_diary = Diary(
        user_id=current_user_id,
        title=data.get('title'),
        location=data.get('location'),
        latitude=la,
        longitude=lo,
        date=parsed_date,
        emotion=data.get('emotion'),
        content=content_html
    )
    db.session.add(new_diary)
    db.session.flush()
    
    # 处理图片
    for i, image_url in enumerate(images):
        diary_image = DiaryImage(
            diary_id=new_diary.id,
            image_url=image_url,
            sort_order=i
        )
        db.session.add(diary_image)
    
    # 处理视频
    for i, video_data in enumerate(videos):
        diary_video = DiaryVideo(
            diary_id=new_diary.id,
            video_url=video_data.get('url'),
            thumbnail_url=video_data.get('thumbnail'),
            sort_order=i
        )
        db.session.add(diary_video)
    
    db.session.commit()
    
    return jsonify({"msg": "创建成功", "diary_id": new_diary.id}), 201

@diary_bp.route('/update/<int:diary_id>', methods=['PUT'])
@jwt_required()
def update_diary(diary_id):
    current_user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    
    # 查找日记
    diary = Diary.query.filter_by(id=diary_id, user_id=current_user_id).first()
    
    if diary is None:
        return jsonify({"msg": "日记不存在"}), 404

    try:
        images = _normalize_images(data.get('images')) if 'images' in data else None
        videos = _normalize_videos(data.get('videos')) if 'videos' in data else None
    except ValueError as exc:
        return jsonify({"msg": str(exc)}), 400
    
    # 更新日记
    diary.title = data.get('title', diary.title)
    diary.location = data.get("location", diary.location)
    parsed = _parse_client_coords(data.get("latitude"), data.get("longitude"))
    if not parsed:
        return jsonify(
            {
                "msg": "请先在前端点击「解析为经纬度」或使用「获取当前位置」，再保存日记",
            }
        ), 400
    diary.latitude, diary.longitude = parsed
    if 'date' in data:
        try:
            diary.date = _parse_date_value(data.get('date'))
        except Exception:
            return jsonify({"msg": "date 字段格式错误，需为 YYYY-MM-DD 或 ISO 时间"}), 400
    diary.emotion = data.get('emotion', diary.emotion)
    if "content" in data:
        content_html = sanitize_diary_html(data.get("content"))
        if diary_html_is_effectively_empty(content_html):
            return jsonify({"msg": "内容不能为空"}), 400
        diary.content = content_html
    
    if images is not None:
        # 更新图片（先删除再重新添加）
        DiaryImage.query.filter_by(diary_id=diary_id).delete()
        for i, image_url in enumerate(images):
            diary_image = DiaryImage(
                diary_id=diary.id,
                image_url=image_url,
                sort_order=i
            )
            db.session.add(diary_image)
    
    if videos is not None:
        # 更新视频（先删除再重新添加）
        DiaryVideo.query.filter_by(diary_id=diary_id).delete()
        for i, video_data in enumerate(videos):
            diary_video = DiaryVideo(
                diary_id=diary.id,
                video_url=video_data.get('url'),
                thumbnail_url=video_data.get('thumbnail'),
                sort_order=i
            )
            db.session.add(diary_video)
    
    db.session.commit()
    
    return jsonify({"msg": "更新成功"}), 200

@diary_bp.route('/delete/<int:diary_id>', methods=['DELETE'])
@jwt_required()
def delete_diary(diary_id):
    current_user_id = int(get_jwt_identity())
    
    # 查找日记
    diary = Diary.query.filter_by(id=diary_id, user_id=current_user_id).first()
    
    if diary is None:
        return jsonify({"msg": "日记不存在"}), 404
    
    # 删除相关图片和视频
    DiaryImage.query.filter_by(diary_id=diary_id).delete()
    DiaryVideo.query.filter_by(diary_id=diary_id).delete()
    
    # 删除日记
    db.session.delete(diary)
    db.session.commit()
    
    return jsonify({"msg": "删除成功"}), 200

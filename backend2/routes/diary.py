from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date, datetime
from sqlalchemy.orm import selectinload
import threading
import logging

from models import Diary, DiaryImage, DiaryVideo, AIAnalysis
from extensions import db, dify_client
from utils.html_sanitize import (
    diary_html_is_effectively_empty,
    sanitize_diary_html,
    html_to_plain_text,
)

diary_bp = Blueprint('diary', __name__)
logger = logging.getLogger(__name__)


def _trigger_ai_analysis(app, diary_id):
    """在后台线程中执行 AI 分析并将结果存库"""
    with app.app_context():
        try:
            diary = Diary.query.options(
                selectinload(Diary.images),
                selectinload(Diary.videos),
            ).filter_by(id=diary_id).first()

            if not diary:
                return

            diary_content = diary.content or ''
            plain_text = html_to_plain_text(diary_content)
            image_urls = [img.image_url for img in diary.images] if diary.images else []
            video_urls = [vid.video_url for vid in diary.videos] if diary.videos else []

            # 调用 Dify 分析
            dify_result = dify_client.analyze_diary_content(
                plain_text if plain_text.strip() else diary_content,
                image_urls=image_urls,
                video_urls=video_urls
            )

            if dify_result:
                analysis_result = dify_result
            else:
                # Dify 不可用时回退到本地分析
                from routes.ai import analyze_diary_content
                analysis_result = analyze_diary_content(diary_content)

            from routes.ai import _save_ai_analysis_record

            # 存库
            _save_ai_analysis_record(diary_id, analysis_result)
            logger.info("AI 分析完成并存库: diary_id=%s", diary_id)

        except Exception as e:
            logger.error("AI 分析后台任务失败: diary_id=%s, error=%s", diary_id, e)
            db.session.rollback()


def _start_ai_analysis(diary_id):
    """启动后台线程执行 AI 分析（不阻塞当前请求）"""
    app = current_app._get_current_object()
    thread = threading.Thread(target=_trigger_ai_analysis, args=(app, diary_id))
    thread.daemon = True
    thread.start()


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


def _parse_bool_value(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "y", "on"}:
            return True
        if text in {"0", "false", "no", "n", "off", ""}:
            return False
    raise ValueError("is_draft 字段格式错误")


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
        "is_draft": bool(diary.is_draft),
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
        "updated_at": diary.updated_at.isoformat() if diary.updated_at else None,
    }


def _normalize_diary_payload(data, existing=None):
    is_draft = _parse_bool_value(
        data.get("is_draft"),
        default=bool(existing.is_draft) if existing is not None else False,
    )

    payload = {
        "is_draft": is_draft,
        "title": existing.title if existing is not None else "",
        "location": existing.location if existing is not None else "",
        "emotion": existing.emotion if existing is not None else "",
        "content": existing.content if existing is not None else "",
        "date": existing.date if existing is not None else None,
        "latitude": float(existing.latitude) if existing is not None and existing.latitude is not None else None,
        "longitude": float(existing.longitude) if existing is not None and existing.longitude is not None else None,
        "images": None if existing is not None else [],
        "videos": None if existing is not None else [],
    }

    if "title" in data or existing is None:
        payload["title"] = (data.get("title") or "").strip()
    if "location" in data or existing is None:
        payload["location"] = (data.get("location") or "").strip()
    if "emotion" in data or existing is None:
        payload["emotion"] = (data.get("emotion") or "").strip()

    if "content" in data or existing is None:
        payload["content"] = sanitize_diary_html(data.get("content"))

    raw_date = data.get("date") if "date" in data else payload["date"]
    if raw_date is None or (isinstance(raw_date, str) and not raw_date.strip()):
        if is_draft:
            payload["date"] = payload["date"] or date.today()
        else:
            payload["date"] = payload["date"]
    else:
        payload["date"] = _parse_date_value(raw_date)

    if "latitude" in data or "longitude" in data or existing is None:
        parsed_coords = _parse_client_coords(data.get("latitude"), data.get("longitude"))
        if parsed_coords:
            payload["latitude"], payload["longitude"] = parsed_coords
        elif "latitude" in data or "longitude" in data:
            payload["latitude"], payload["longitude"] = None, None

    if "images" in data or existing is None:
        payload["images"] = _normalize_images(data.get("images"))
    if "videos" in data or existing is None:
        payload["videos"] = _normalize_videos(data.get("videos"))

    return payload


def _validate_publish_payload(payload):
    missing = []
    if not payload["title"]:
        missing.append("title")
    if not payload["location"]:
        missing.append("location")
    if not payload["date"]:
        missing.append("date")
    if not payload["emotion"]:
        missing.append("emotion")
    if missing:
        return jsonify({"msg": f"缺少必填字段: {', '.join(missing)}"}), 400

    if diary_html_is_effectively_empty(payload["content"]):
        return jsonify({"msg": "内容不能为空"}), 400

    if payload["latitude"] is None or payload["longitude"] is None:
        return jsonify(
            {
                "msg": "请先在前端点击「解析为经纬度」或使用「获取当前位置」，再保存日记",
            }
        ), 400

    return None

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
        .filter_by(user_id=current_user_id, is_draft=False)
        .order_by(Diary.created_at.desc())
        .all()
    )
    
    return jsonify([_serialize_diary(diary) for diary in user_diaries]), 200


@diary_bp.route('/drafts', methods=['GET'])
@jwt_required()
def get_diary_drafts():
    current_user_id = int(get_jwt_identity())

    draft_diaries = (
        Diary.query.options(
            selectinload(Diary.images),
            selectinload(Diary.videos),
        )
        .filter_by(user_id=current_user_id, is_draft=True)
        .order_by(Diary.updated_at.desc(), Diary.id.desc())
        .all()
    )

    return jsonify([_serialize_diary(diary) for diary in draft_diaries]), 200

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

    try:
        payload = _normalize_diary_payload(data)
    except ValueError as exc:
        msg = str(exc)
        if msg == "date 字段格式错误":
            return jsonify({"msg": "date 字段格式错误，需为 YYYY-MM-DD 或 ISO 时间"}), 400
        return jsonify({"msg": msg}), 400
    except Exception:
        return jsonify({"msg": "date 字段格式错误，需为 YYYY-MM-DD 或 ISO 时间"}), 400

    if not payload["is_draft"]:
        invalid = _validate_publish_payload(payload)
        if invalid:
            return invalid

    # 创建新日记（经纬度仅接受客户端解析/定位结果，避免在保存接口内再调地图导致 macOS 下 worker 不稳定）
    new_diary = Diary(
        user_id=current_user_id,
        is_draft=payload["is_draft"],
        title=payload["title"],
        location=payload["location"],
        latitude=payload["latitude"],
        longitude=payload["longitude"],
        date=payload["date"],
        emotion=payload["emotion"],
        content=payload["content"],
    )
    db.session.add(new_diary)
    db.session.flush()
    
    # 处理图片
    for i, image_url in enumerate(payload["images"]):
        diary_image = DiaryImage(
            diary_id=new_diary.id,
            image_url=image_url,
            sort_order=i
        )
        db.session.add(diary_image)
    
    # 处理视频
    for i, video_data in enumerate(payload["videos"]):
        diary_video = DiaryVideo(
            diary_id=new_diary.id,
            video_url=video_data.get('url'),
            thumbnail_url=video_data.get('thumbnail'),
            sort_order=i
        )
        db.session.add(diary_video)
    
    db.session.commit()

    # 非草稿日记落库后自动触发 AI 分析
    if not payload["is_draft"]:
        _start_ai_analysis(new_diary.id)
    
    return jsonify(
        {
            "msg": "草稿保存成功" if payload["is_draft"] else "创建成功",
            "diary_id": new_diary.id,
            "is_draft": payload["is_draft"],
        }
    ), 201

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
        payload = _normalize_diary_payload(data, existing=diary)
    except ValueError as exc:
        msg = str(exc)
        if msg == "date 字段格式错误":
            return jsonify({"msg": "date 字段格式错误，需为 YYYY-MM-DD 或 ISO 时间"}), 400
        return jsonify({"msg": msg}), 400
    except Exception:
        return jsonify({"msg": "date 字段格式错误，需为 YYYY-MM-DD 或 ISO 时间"}), 400

    if not payload["is_draft"]:
        invalid = _validate_publish_payload(payload)
        if invalid:
            return invalid

    # 更新日记
    diary.is_draft = payload["is_draft"]
    diary.title = payload["title"]
    diary.location = payload["location"]
    diary.latitude = payload["latitude"]
    diary.longitude = payload["longitude"]
    diary.date = payload["date"]
    diary.emotion = payload["emotion"]
    diary.content = payload["content"]
    
    if payload["images"] is not None:
        # 更新图片（先删除再重新添加）
        DiaryImage.query.filter_by(diary_id=diary_id).delete()
        for i, image_url in enumerate(payload["images"]):
            diary_image = DiaryImage(
                diary_id=diary.id,
                image_url=image_url,
                sort_order=i
            )
            db.session.add(diary_image)
    
    if payload["videos"] is not None:
        # 更新视频（先删除再重新添加）
        DiaryVideo.query.filter_by(diary_id=diary_id).delete()
        for i, video_data in enumerate(payload["videos"]):
            diary_video = DiaryVideo(
                diary_id=diary.id,
                video_url=video_data.get('url'),
                thumbnail_url=video_data.get('thumbnail'),
                sort_order=i
            )
            db.session.add(diary_video)
    
    db.session.commit()

    # 非草稿日记更新后，删除旧分析并重新触发 AI 分析
    if not payload["is_draft"]:
        AIAnalysis.query.filter_by(diary_id=diary_id).delete()
        db.session.commit()
        _start_ai_analysis(diary.id)
    
    return jsonify(
        {
            "msg": "草稿保存成功" if payload["is_draft"] else "更新成功",
            "diary_id": diary.id,
            "is_draft": payload["is_draft"],
        }
    ), 200

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

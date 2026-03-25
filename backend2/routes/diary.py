from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Diary, DiaryImage, DiaryVideo
from extensions import db

diary_bp = Blueprint('diary', __name__)

@diary_bp.route('/list', methods=['GET'])
@jwt_required()
def get_diary_list():
    current_user_id = get_jwt_identity()
    
    # 筛选出当前用户的日记
    user_diaries = Diary.query.filter_by(user_id=current_user_id).order_by(Diary.created_at.desc()).all()
    
    diaries_data = []
    for diary in user_diaries:
        diary_data = {
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
            "created_at": diary.created_at.isoformat() if diary.created_at else None
        }
        diaries_data.append(diary_data)
    
    return jsonify(diaries_data), 200

@diary_bp.route('/detail/<int:diary_id>', methods=['GET'])
@jwt_required()
def get_diary_detail(diary_id):
    current_user_id = get_jwt_identity()
    
    # 查找日记
    diary = Diary.query.filter_by(id=diary_id, user_id=current_user_id).first()
    
    if diary is None:
        return jsonify({"msg": "日记不存在"}), 404
    
    diary_data = {
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
        "created_at": diary.created_at.isoformat() if diary.created_at else None
    }
    
    return jsonify(diary_data), 200

@diary_bp.route('/create', methods=['POST'])
@jwt_required()
def create_diary():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    # 创建新日记
    new_diary = Diary(
        user_id=current_user_id,
        title=data.get('title'),
        location=data.get('location'),
        latitude=data.get('latitude'),
        longitude=data.get('longitude'),
        date=data.get('date'),
        emotion=data.get('emotion'),
        content=data.get('content')
    )
    db.session.add(new_diary)
    db.session.commit()
    
    # 处理图片
    images = data.get('images', [])
    for i, image_url in enumerate(images):
        diary_image = DiaryImage(
            diary_id=new_diary.id,
            image_url=image_url,
            sort_order=i
        )
        db.session.add(diary_image)
    
    # 处理视频
    videos = data.get('videos', [])
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
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    # 查找日记
    diary = Diary.query.filter_by(id=diary_id, user_id=current_user_id).first()
    
    if diary is None:
        return jsonify({"msg": "日记不存在"}), 404
    
    # 更新日记
    diary.title = data.get('title', diary.title)
    diary.location = data.get('location', diary.location)
    diary.latitude = data.get('latitude', diary.latitude)
    diary.longitude = data.get('longitude', diary.longitude)
    diary.date = data.get('date', diary.date)
    diary.emotion = data.get('emotion', diary.emotion)
    diary.content = data.get('content', diary.content)
    
    # 更新图片（先删除再重新添加）
    DiaryImage.query.filter_by(diary_id=diary_id).delete()
    images = data.get('images', [])
    for i, image_url in enumerate(images):
        diary_image = DiaryImage(
            diary_id=diary.id,
            image_url=image_url,
            sort_order=i
        )
        db.session.add(diary_image)
    
    # 更新视频（先删除再重新添加）
    DiaryVideo.query.filter_by(diary_id=diary_id).delete()
    videos = data.get('videos', [])
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
    current_user_id = get_jwt_identity()
    
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
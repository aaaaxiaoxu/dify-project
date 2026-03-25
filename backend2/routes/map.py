from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Diary, TravelTrajectory
from extensions import db

map_bp = Blueprint('map', __name__)

@map_bp.route('/trajectory', methods=['GET'])
@jwt_required()
def get_trajectory():
    current_user_id = int(get_jwt_identity())
    
    # 筛选出当前用户的旅行轨迹数据
    user_diaries = Diary.query.filter_by(user_id=current_user_id).all()
    
    # 提取轨迹信息
    trajectory_data = []
    for diary in user_diaries:
        trajectory_data.append({
            "location": diary.location,
            "date": diary.date.isoformat() if diary.date else None,
            "emotion": diary.emotion,
            "latitude": float(diary.latitude) if diary.latitude else None,
            "longitude": float(diary.longitude) if diary.longitude else None
        })
    
    return jsonify(trajectory_data), 200

@map_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_map_stats():
    current_user_id = int(get_jwt_identity())
    
    # 获取当前用户的所有日记
    user_diaries = Diary.query.filter_by(user_id=current_user_id).all()
    
    # 统计城市数量（根据地点去重）
    locations = [diary.location for diary in user_diaries]
    unique_locations = list(set(locations))
    city_count = len(unique_locations)
    
    # 简单模拟公里数（实际应该根据地理位置计算）
    # 这里我们假设每次旅行平均距离为200公里
    km_count = len(user_diaries) * 200
    
    stats_data = {
        "city_count": city_count,
        "km_count": km_count,
        "locations": unique_locations
    }
    
    return jsonify(stats_data), 200

@map_bp.route('/detail', methods=['GET'])
@jwt_required()
def get_map_detail():
    current_user_id = int(get_jwt_identity())
    
    # 获取当前用户的所有日记
    user_diaries = Diary.query.filter_by(user_id=current_user_id).order_by(Diary.date.desc()).all()
    
    # 构建详细数据
    detail_data = {
        "stats": {},
        "history": []
    }
    
    # 统计数据
    locations = [diary.location for diary in user_diaries]
    unique_locations = list(set(locations))
    city_count = len(unique_locations)
    km_count = len(user_diaries) * 200  # 简单模拟公里数
    total_days = len(user_diaries)
    
    detail_data["stats"] = {
        "total_cities": city_count,
        "total_distance": km_count,
        "total_days": total_days
    }
    
    # 历史记录
    for diary in user_diaries:
        detail_data["history"].append({
            "location": diary.location,
            "date": diary.date.isoformat() if diary.date else None,
            "emotion": diary.emotion,
            "latitude": float(diary.latitude) if diary.latitude else None,
            "longitude": float(diary.longitude) if diary.longitude else None
        })
    
    return jsonify(detail_data), 200
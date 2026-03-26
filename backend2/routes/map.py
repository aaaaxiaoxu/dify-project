from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Diary
from geo_utils import (
    route_distance_km_from_diaries,
    unique_location_strings,
    unique_travel_day_count,
)
import requests

from tencent_geocode import forward_geocode_address

map_bp = Blueprint('map', __name__)

@map_bp.route('/trajectory', methods=['GET'])
@jwt_required()
def get_trajectory():
    current_user_id = int(get_jwt_identity())
    
    # 按时间正序，便于前端直接连线成「旅程」
    user_diaries = (
        Diary.query.filter_by(user_id=current_user_id, is_draft=False)
        .order_by(Diary.date.asc(), Diary.id.asc())
        .all()
    )
    
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
    
    user_diaries = Diary.query.filter_by(user_id=current_user_id, is_draft=False).all()

    unique_locations = unique_location_strings(user_diaries)
    city_count = len(unique_locations)
    km_count = route_distance_km_from_diaries(user_diaries)

    stats_data = {
        "diary_count": len(user_diaries),
        "city_count": city_count,
        "km_count": km_count,
        "locations": unique_locations,
    }
    
    return jsonify(stats_data), 200

@map_bp.route('/detail', methods=['GET'])
@jwt_required()
def get_map_detail():
    current_user_id = int(get_jwt_identity())
    
    # 获取当前用户的所有日记
    user_diaries = Diary.query.filter_by(user_id=current_user_id, is_draft=False).order_by(Diary.date.desc()).all()
    
    # 构建详细数据
    detail_data = {
        "stats": {},
        "history": []
    }
    
    unique_locations = unique_location_strings(user_diaries)
    city_count = len(unique_locations)
    km_count = route_distance_km_from_diaries(user_diaries)
    total_days = unique_travel_day_count(user_diaries)

    detail_data["stats"] = {
        "total_cities": city_count,
        "total_distance": km_count,
        "total_days": total_days,
        "diary_count": len(user_diaries),
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


@map_bp.route('/reverse_geocode', methods=['POST'])
@jwt_required()
def reverse_geocode():
    data = request.get_json() or {}
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if latitude is None or longitude is None:
        return jsonify({"msg": "latitude 和 longitude 不能为空"}), 400

    try:
        lat = float(latitude)
        lng = float(longitude)
    except (TypeError, ValueError):
        return jsonify({"msg": "latitude 或 longitude 格式错误"}), 400

    map_key = current_app.config.get("TENCENT_MAP_KEY")
    if not map_key:
        return jsonify({"msg": "未配置腾讯地图 Key"}), 500

    try:
        resp = requests.get(
            "https://apis.map.qq.com/ws/geocoder/v1/",
            params={"location": f"{lat},{lng}", "key": map_key},
            timeout=8,
        )
        if resp.status_code != 200:
            return jsonify({"msg": "地址解析服务不可用"}), 502

        payload = resp.json()
        if payload.get("status") != 0:
            return jsonify({"msg": payload.get("message") or "地址解析失败"}), 502

        result = payload.get("result", {})
        address = result.get("address", "")
        ad_info = result.get("address_component", {})
        province = ad_info.get("province", "")
        city = ad_info.get("city", "")
        district = ad_info.get("district", "")

        return jsonify(
            {
                "address": address,
                "province": province,
                "city": city,
                "district": district,
            }
        ), 200
    except Exception:
        return jsonify({"msg": "地址解析请求异常"}), 502


@map_bp.route("/geocode", methods=["POST"])
@jwt_required()
def geocode_address():
    """正向地理编码：文本地址 → 经纬度（与写日记入库逻辑共用）。"""
    data = request.get_json() or {}
    address = (data.get("address") or "").strip()
    if not address:
        return jsonify({"msg": "address 不能为空"}), 400

    map_key = current_app.config.get("TENCENT_MAP_KEY")
    if not map_key:
        return jsonify({"msg": "未配置腾讯地图 Key"}), 500

    region = (data.get("region") or "").strip() or None
    res = forward_geocode_address(address, map_key, region=region)
    if not res:
        return jsonify({"msg": "未找到该地址对应的坐标或服务异常"}), 400

    return jsonify(
        {
            "latitude": res["latitude"],
            "longitude": res["longitude"],
            "address": res.get("formatted"),
        }
    ), 200

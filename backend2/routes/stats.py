"""统计分析接口 —— 情感分布 & 情绪趋势"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date, timedelta
from sqlalchemy import func
from collections import OrderedDict

from models import Diary, AIAnalysis
from extensions import db

stats_bp = Blueprint('stats', __name__)


# ---------- 1. 情感倾向分布（饼图数据） ----------
@stats_bp.route('/emotion-distribution', methods=['GET'])
@jwt_required()
def emotion_distribution():
    """
    返回当前用户所有非草稿日记的情绪标签分布。
    响应示例:
    {
      "items": [
        {"emotion": "开心", "count": 12},
        {"emotion": "感动", "count": 5},
        ...
      ],
      "total": 30
    }
    """
    current_user_id = int(get_jwt_identity())

    rows = (
        db.session.query(Diary.emotion, func.count(Diary.id).label('cnt'))
        .filter(Diary.user_id == current_user_id, Diary.is_draft == False)
        .group_by(Diary.emotion)
        .all()
    )

    items = [{'emotion': row.emotion, 'count': row.cnt} for row in rows]
    total = sum(r['count'] for r in items)

    return jsonify({'items': items, 'total': total}), 200


# ---------- 2. 情绪波动趋势（折线图数据） ----------
@stats_bp.route('/emotion-trend', methods=['GET'])
@jwt_required()
def emotion_trend():
    """
    按天聚合日记数量及平均情绪指数。
    Query params:
      - period: '7d' | '30d' | 'month'  （默认 '7d'）
    响应示例:
    {
      "period": "7d",
      "dates": ["2026-03-20", "2026-03-21", ...],
      "counts": [1, 0, 2, ...],
      "scores": [4.0, null, 3.5, ...]
    }
    """
    current_user_id = int(get_jwt_identity())
    period = request.args.get('period', '7d')

    today = date.today()
    if period == '30d' or period == 'month':
        start_date = today - timedelta(days=29)
        period_label = '30d'
    else:
        start_date = today - timedelta(days=6)
        period_label = '7d'

    # 查询该时间范围内的日记（非草稿），同时 join AI 分析结果取 emotion_score
    rows = (
        db.session.query(Diary.date, AIAnalysis.emotion_score)
        .outerjoin(AIAnalysis, AIAnalysis.diary_id == Diary.id)
        .filter(
            Diary.user_id == current_user_id,
            Diary.is_draft == False,
            Diary.date >= start_date,
            Diary.date <= today,
        )
        .all()
    )

    # 按天聚合
    day_map = OrderedDict()
    d = start_date
    while d <= today:
        day_map[d.isoformat()] = {'count': 0, 'score_sum': 0.0, 'score_cnt': 0}
        d += timedelta(days=1)

    for diary_date, emotion_score in rows:
        key = diary_date.isoformat() if diary_date else None
        if key and key in day_map:
            day_map[key]['count'] += 1
            if emotion_score is not None:
                day_map[key]['score_sum'] += emotion_score
                day_map[key]['score_cnt'] += 1

    dates = list(day_map.keys())
    counts = [v['count'] for v in day_map.values()]
    scores = [
        round(v['score_sum'] / v['score_cnt'], 2) if v['score_cnt'] > 0 else None
        for v in day_map.values()
    ]

    return jsonify({
        'period': period_label,
        'dates': dates,
        'counts': counts,
        'scores': scores,
    }), 200

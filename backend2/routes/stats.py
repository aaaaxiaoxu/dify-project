"""统计分析接口 —— 情感分布 & 情绪趋势"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date, timedelta
from collections import OrderedDict
from sqlalchemy import func

from models import Diary, AIAnalysis
from extensions import db

stats_bp = Blueprint('stats', __name__)


SCORE_BUCKETS = (
    {"emotion": "强烈积极", "range": "0.6 ~ 1.0"},
    {"emotion": "偏积极", "range": "0.2 ~ 0.6"},
    {"emotion": "中性", "range": "-0.2 ~ 0.2"},
    {"emotion": "偏消极", "range": "-0.6 ~ -0.2"},
    {"emotion": "强烈消极", "range": "-1.0 ~ -0.6"},
    {"emotion": "待分析", "range": "暂无评分"},
)


def _month_start(value):
    return date(value.year, value.month, 1)


def _next_month(value):
    if value.month == 12:
        return date(value.year + 1, 1, 1)
    return date(value.year, value.month + 1, 1)


def _normalize_emotion_score(raw_score):
    if raw_score is None:
        return None

    try:
        return max(-1.0, min(1.0, float(raw_score)))
    except (TypeError, ValueError):
        return None


def _score_to_bucket(score):
    if score is None:
        return "待分析"
    if score >= 0.6:
        return "强烈积极"
    if score >= 0.2:
        return "偏积极"
    if score >= -0.2:
        return "中性"
    if score >= -0.6:
        return "偏消极"
    return "强烈消极"


# ---------- 1. 情感倾向分布（饼图数据） ----------
@stats_bp.route('/emotion-distribution', methods=['GET'])
@jwt_required()
def emotion_distribution():
    """
    返回当前用户所有非草稿日记的情绪评分分布。
    响应示例:
    {
      "items": [
        {"emotion": "强烈积极", "count": 12, "range": "0.6 ~ 1.0"},
        {"emotion": "中性", "count": 5, "range": "-0.2 ~ 0.2"},
        ...
      ],
      "total": 30,
      "scored_total": 28,
      "avg_score": 0.37
    }
    """
    current_user_id = int(get_jwt_identity())

    rows = (
        db.session.query(AIAnalysis.emotion_score)
        .select_from(Diary)
        .outerjoin(AIAnalysis, AIAnalysis.diary_id == Diary.id)
        .filter(Diary.user_id == current_user_id, Diary.is_draft == False)
        .all()
    )

    bucket_counts = OrderedDict((bucket['emotion'], 0) for bucket in SCORE_BUCKETS)
    valid_scores = []

    for (raw_score,) in rows:
        score = _normalize_emotion_score(raw_score)
        bucket_counts[_score_to_bucket(score)] += 1
        if score is not None:
            valid_scores.append(score)

    items = [
        {
            'emotion': bucket['emotion'],
            'count': bucket_counts[bucket['emotion']],
            'range': bucket['range'],
        }
        for bucket in SCORE_BUCKETS
        if bucket_counts[bucket['emotion']] > 0
    ]
    total = sum(bucket_counts.values())
    avg_score = round(sum(valid_scores) / len(valid_scores), 2) if valid_scores else None

    return jsonify({
        'items': items,
        'total': total,
        'scored_total': len(valid_scores),
        'avg_score': avg_score,
    }), 200


# ---------- 2. 情绪波动趋势（折线图数据） ----------
@stats_bp.route('/emotion-trend', methods=['GET'])
@jwt_required()
def emotion_trend():
    """
    按天聚合日记数量及平均情绪评分。
    Query params:
      - period: '7d' | '30d' | 'month' | 'all'  （默认 '7d'）
    响应示例:
    {
      "period": "7d",
      "granularity": "day",
      "dates": ["2026-03-20", "2026-03-21", ...],
      "counts": [1, 0, 2, ...],
      "scores": [0.7, null, -0.1, ...]
    }
    """
    current_user_id = int(get_jwt_identity())
    period = request.args.get('period', '7d')

    today = date.today()
    if period == 'all':
        start_date, end_date = (
            db.session.query(func.min(Diary.date), func.max(Diary.date))
            .filter(Diary.user_id == current_user_id, Diary.is_draft == False)
            .first()
        )

        if not start_date or not end_date:
            return jsonify({
                'period': 'all',
                'granularity': 'day',
                'dates': [],
                'counts': [],
                'scores': [],
            }), 200

        period_label = 'all'
        granularity = 'month' if (end_date - start_date).days > 90 else 'day'
    elif period == '30d' or period == 'month':
        start_date = today - timedelta(days=29)
        end_date = today
        period_label = '30d'
        granularity = 'day'
    else:
        start_date = today - timedelta(days=6)
        end_date = today
        period_label = '7d'
        granularity = 'day'

    # 查询该时间范围内的日记（非草稿），同时 join AI 分析结果取 emotion_score
    rows = (
        db.session.query(Diary.date, AIAnalysis.emotion_score)
        .outerjoin(AIAnalysis, AIAnalysis.diary_id == Diary.id)
        .filter(
            Diary.user_id == current_user_id,
            Diary.is_draft == False,
            Diary.date >= start_date,
            Diary.date <= end_date,
        )
        .all()
    )

    if granularity == 'month':
        bucket_map = OrderedDict()
        current_month = _month_start(start_date)
        end_month = _month_start(end_date)
        while current_month <= end_month:
            bucket_map[current_month.strftime('%Y-%m')] = {
                'count': 0,
                'score_sum': 0.0,
                'score_cnt': 0,
            }
            current_month = _next_month(current_month)
    else:
        bucket_map = OrderedDict()
        d = start_date
        while d <= end_date:
            bucket_map[d.isoformat()] = {'count': 0, 'score_sum': 0.0, 'score_cnt': 0}
            d += timedelta(days=1)

    for diary_date, emotion_score in rows:
        if not diary_date:
            continue
        key = (
            diary_date.strftime('%Y-%m')
            if granularity == 'month'
            else diary_date.isoformat()
        )
        if key in bucket_map:
            bucket_map[key]['count'] += 1
            score = _normalize_emotion_score(emotion_score)
            if score is not None:
                bucket_map[key]['score_sum'] += score
                bucket_map[key]['score_cnt'] += 1

    dates = list(bucket_map.keys())
    counts = [v['count'] for v in bucket_map.values()]
    scores = [
        round(v['score_sum'] / v['score_cnt'], 2) if v['score_cnt'] > 0 else None
        for v in bucket_map.values()
    ]

    return jsonify({
        'period': period_label,
        'granularity': granularity,
        'dates': dates,
        'counts': counts,
        'scores': scores,
    }), 200

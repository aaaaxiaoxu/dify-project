import json
import os
import uuid
from collections import Counter, OrderedDict
from datetime import date, datetime, timedelta

from flask import Blueprint, current_app, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import func

from extensions import db, dify_client
from geo_utils import (
    route_distance_km_from_diaries,
    unique_location_strings,
    unique_travel_day_count,
)
from models import AIAnalysis, Diary
from utils.html_sanitize import html_to_plain_text
from utils.report_pdf import build_travel_report_pdf

report_bp = Blueprint('report', __name__)


def _parse_date_value(raw_value, field_name):
    text = (raw_value or '').strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f'{field_name} 格式错误，应为 YYYY-MM-DD') from exc


def _resolve_report_range(user_id, payload):
    preset = ((payload.get('preset') or payload.get('range_type') or '30d').strip().lower())
    start_date = _parse_date_value(payload.get('start_date'), 'start_date')
    end_date = _parse_date_value(payload.get('end_date'), 'end_date')
    today = date.today()

    if start_date or end_date:
        if not start_date or not end_date:
            raise ValueError('start_date 和 end_date 需要同时传入')
        if start_date > end_date:
            raise ValueError('start_date 不能晚于 end_date')
        return start_date, end_date, 'custom'

    if preset in {'7d', '7'}:
        return today - timedelta(days=6), today, '7d'

    if preset in {'30d', '30', 'month'}:
        return today - timedelta(days=29), today, '30d'

    if preset == 'all':
        start_date, end_date = (
            db.session.query(func.min(Diary.date), func.max(Diary.date))
            .filter(Diary.user_id == user_id, Diary.is_draft == False)
            .first()
        )
        return start_date, end_date, 'all'

    raise ValueError('preset 参数无效，仅支持 7d / 30d / all / custom')


def _clip_text(text, limit=110):
    text = (text or '').strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + '…'


def _normalize_score(raw_score):
    if raw_score is None or raw_score == '':
        return None
    try:
        return round(max(-1.0, min(1.0, float(raw_score))), 2)
    except (TypeError, ValueError):
        return None


def _parse_keywords(raw_keywords):
    if isinstance(raw_keywords, list):
        return [str(item).strip() for item in raw_keywords if str(item).strip()]
    if isinstance(raw_keywords, str):
        text = raw_keywords.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except (json.JSONDecodeError, TypeError):
            return [item.strip() for item in text.split(',') if item.strip()]
    return []


def _emotion_group(score):
    if score is None:
        return '待分析'
    if score >= 0.2:
        return '积极'
    if score <= -0.2:
        return '消极'
    return '中性'


def _score_label(score):
    if score is None:
        return '待分析'
    if score >= 0.6:
        return '明显积极'
    if score >= 0.2:
        return '偏积极'
    if score <= -0.6:
        return '明显低落'
    if score <= -0.2:
        return '略有波动'
    return '平稳中性'


def _format_score(score):
    if score is None:
        return '--'
    return f"+{score:.1f}" if score > 0 else f"{score:.1f}"


def _load_analysis_snapshot(diary, analysis_record):
    plain_text = html_to_plain_text(diary.content or '').strip()

    needs_fallback = (
        analysis_record is None or
        (
            analysis_record.emotion_score is None and
            not (analysis_record.emotion_label or '').strip() and
            not (analysis_record.memory_point or '').strip() and
            not _parse_keywords(analysis_record.keywords)
        )
    )

    if needs_fallback:
        from routes.ai import analyze_diary_content

        fallback = analyze_diary_content(diary.content or '')
        return {
            'emotion_score': _normalize_score(fallback.get('emotion_score')),
            'emotion_label': (fallback.get('emotion_label') or '').strip(),
            'memory_point': (fallback.get('memory_point') or '').strip(),
            'keywords': _parse_keywords(fallback.get('keywords', [])),
            'travel_advice': (fallback.get('travel_advice') or '').strip(),
            'emotion_analysis': (fallback.get('emotion_analysis') or '').strip(),
            'excerpt': _clip_text(plain_text),
        }

    return {
        'emotion_score': _normalize_score(analysis_record.emotion_score),
        'emotion_label': (analysis_record.emotion_label or '').strip(),
        'memory_point': (analysis_record.memory_point or '').strip(),
        'keywords': _parse_keywords(analysis_record.keywords),
        'travel_advice': (analysis_record.travel_advice or '').strip(),
        'emotion_analysis': (analysis_record.emotion_analysis or '').strip(),
        'excerpt': _clip_text(plain_text),
    }


def _select_highlights(items, limit=6):
    ranked = sorted(
        items,
        key=lambda item: (
            1 if item['memory_point'] else 0,
            abs(item['emotion_score']) if item['emotion_score'] is not None else -1,
            len(item['keywords']),
            item['date'],
        ),
        reverse=True,
    )

    selected = []
    seen_ids = set()
    for item in ranked:
        if item['id'] in seen_ids:
            continue
        selected.append(
            {
                'date': item['date'],
                'title': item['title'],
                'location': item['location'],
                'emotion_score': item['emotion_score'],
                'emotion_label': item['emotion_label'],
                'memory_point': item['memory_point'],
                'keywords': item['keywords'][:5],
                'excerpt': item['excerpt'],
            }
        )
        seen_ids.add(item['id'])
        if len(selected) >= limit:
            break

    if not selected:
        return [
            {
                'date': item['date'],
                'title': item['title'],
                'location': item['location'],
                'emotion_score': item['emotion_score'],
                'emotion_label': item['emotion_label'],
                'memory_point': item['memory_point'],
                'keywords': item['keywords'][:5],
                'excerpt': item['excerpt'],
            }
            for item in items[:limit]
        ]
    return selected


def _select_sample_entries(items, limit=10):
    if len(items) <= limit:
        return [
            {
                'date': item['date'],
                'title': item['title'],
                'location': item['location'],
                'emotion_score': item['emotion_score'],
                'emotion_label': item['emotion_label'],
                'keywords': item['keywords'][:4],
                'memory_point': item['memory_point'],
                'excerpt': item['excerpt'],
            }
            for item in items
        ]

    sample = []
    used_ids = set()

    def _append_entry(item):
        if item['id'] in used_ids or len(sample) >= limit:
            return
        sample.append(
            {
                'date': item['date'],
                'title': item['title'],
                'location': item['location'],
                'emotion_score': item['emotion_score'],
                'emotion_label': item['emotion_label'],
                'keywords': item['keywords'][:4],
                'memory_point': item['memory_point'],
                'excerpt': item['excerpt'],
            }
        )
        used_ids.add(item['id'])

    for item in items[:3]:
        _append_entry(item)
    for item in items[-3:]:
        _append_entry(item)
    for item in _select_highlights(items, limit=limit):
        matched = next(
            (
                source_item
                for source_item in items
                if source_item['date'] == item['date'] and source_item['title'] == item['title']
            ),
            None,
        )
        if matched:
            _append_entry(matched)
        if len(sample) >= limit:
            break

    return sample[:limit]


def _select_report_cover_image(rows):
    for diary, _analysis_record in reversed(rows):
        for image in diary.images or []:
            image_url = (image.image_url or '').strip()
            if not image_url:
                continue
            if not image_url.startswith(('http://', 'https://')):
                continue
            return {
                'image_url': image_url,
                'diary_id': diary.id,
                'diary_title': (diary.title or '').strip() or '未命名日记',
                'diary_date': diary.date.isoformat() if diary.date else '',
                'location': (diary.location or '').strip(),
            }
    return None


def _build_report_context(rows, start_date, end_date):
    diaries = []
    items = []
    location_counter = Counter()
    keyword_counter = Counter()
    emotion_counter = Counter()
    travel_advice_pool = []
    score_values = []

    for diary, analysis_record in rows:
        diaries.append(diary)
        snapshot = _load_analysis_snapshot(diary, analysis_record)
        score = snapshot['emotion_score']
        if score is not None:
            score_values.append(score)
        emotion_counter[_emotion_group(score)] += 1

        location = (diary.location or '').strip()
        if location:
            location_counter[location] += 1

        for keyword in snapshot['keywords'][:5]:
            keyword_counter[keyword] += 1

        if snapshot['travel_advice']:
            travel_advice_pool.append(snapshot['travel_advice'])

        items.append(
            {
                'id': diary.id,
                'date': diary.date.isoformat() if diary.date else '',
                'title': (diary.title or '').strip() or '未命名日记',
                'location': location,
                'emotion_score': score,
                'emotion_label': snapshot['emotion_label'],
                'memory_point': snapshot['memory_point'],
                'keywords': snapshot['keywords'],
                'travel_advice': snapshot['travel_advice'],
                'emotion_analysis': snapshot['emotion_analysis'],
                'excerpt': snapshot['excerpt'],
            }
        )

    unique_locations = unique_location_strings(diaries)
    highlights = _select_highlights(items)
    sample_entries = _select_sample_entries(items)
    cover_image = _select_report_cover_image(rows)
    avg_emotion_score = round(sum(score_values) / len(score_values), 2) if score_values else None

    dedup_advice = list(OrderedDict((item, None) for item in travel_advice_pool).keys())

    return {
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_days': (end_date - start_date).days + 1,
            'travel_day_count': unique_travel_day_count(diaries),
        },
        'summary_stats': {
            'diary_count': len(diaries),
            'city_count': len(unique_locations),
            'total_distance_km': route_distance_km_from_diaries(diaries),
            'avg_emotion_score': avg_emotion_score,
            'scored_diary_count': len(score_values),
        },
        'locations': [
            {'name': name, 'count': count}
            for name, count in location_counter.most_common(8)
        ],
        'emotion_distribution': [
            {'label': label, 'count': emotion_counter.get(label, 0)}
            for label in ['积极', '中性', '消极', '待分析']
            if emotion_counter.get(label, 0) > 0
        ],
        'top_keywords': [
            {'keyword': keyword, 'count': count}
            for keyword, count in keyword_counter.most_common(10)
        ],
        'highlights': highlights,
        'entries': sample_entries,
        'cover_image': cover_image,
        'travel_advice_pool': dedup_advice[:5],
    }


def _range_title_text(start_date, end_date):
    if start_date.year == end_date.year and start_date.month == end_date.month:
        return f'{start_date.year}年{start_date.month}月'
    if start_date.year == end_date.year:
        return f'{start_date.year}年{start_date.month}月-{end_date.month}月'
    return f'{start_date.year}年{start_date.month}月-{end_date.year}年{end_date.month}月'


def _build_highlight_lines(highlights):
    lines = []
    for item in highlights[:5]:
        intro = f"{item['date']} 在 {item['location'] or '旅途中'}"
        title = f"《{item['title']}》"
        score_text = _format_score(item['emotion_score'])
        detail = item['memory_point'] or item['excerpt'] or '留下了一次值得记住的旅行片段。'
        lines.append(f"{intro} 的 {title} 情绪评分 {score_text}，{detail}")
    return lines


def _build_travel_preferences(context):
    stats = context['summary_stats']
    locations = context['locations']
    keywords = context['top_keywords']
    highlights = context['highlights']
    preferences = []

    if locations:
        top_location = locations[0]
        if top_location['count'] > 1:
            preferences.append(f"你会反复记录 {top_location['name']} 这类地点，说明这类场景对你有稳定吸引力。")
        else:
            preferences.append(f"这段时间的行程覆盖 {stats['city_count']} 个地点，说明你更偏好持续探索不同目的地。")

    if keywords:
        top_terms = '、'.join(item['keyword'] for item in keywords[:3])
        preferences.append(f"关键词多次出现 {top_terms}，这些元素更容易触发你的旅行记忆。")

    if stats['avg_emotion_score'] is not None:
        score = stats['avg_emotion_score']
        if score >= 0.3:
            preferences.append('你的记录明显偏向捕捉让自己放松、满足和被打动的时刻。')
        elif score <= -0.2:
            preferences.append('你会如实记录旅途中的疲惫与落差，不只保留“好看”的片段。')
        else:
            preferences.append('你的记录方式比较平衡，既会写风景，也会记下真实状态和细节变化。')

    if any(item['memory_point'] for item in highlights):
        preferences.append('相比走马观花，你更看重能留下明确记忆点的瞬间。')

    return preferences[:4] or ['你更关注旅途里的具体体验，而不是只打卡地点本身。']


def _build_next_trip_suggestions(context):
    suggestions = []
    for advice in context['travel_advice_pool'][:3]:
        text = _clip_text(advice, limit=56)
        if text:
            suggestions.append(text)

    locations = context['locations']
    stats = context['summary_stats']
    if not suggestions and locations:
        suggestions.append(f"可以围绕 {locations[0]['name']} 相似气质的目的地，安排一次更完整的深度旅行。")
    if len(suggestions) < 2:
        if stats['total_distance_km'] and stats['total_distance_km'] >= 500:
            suggestions.append('下次可以减少同一行程中的转场次数，给每个地点留出更多停留时间。')
        else:
            suggestions.append('下次可以尝试加入一段清晨散步或傍晚停留，让旅程的节奏更完整。')
    if len(suggestions) < 3:
        suggestions.append('建议继续保留情绪评分和记忆点，这会让下一次总结更准确、更有个性。')

    deduped = []
    seen = set()
    for item in suggestions:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped[:4]


def _build_emotion_review(context):
    distribution = {item['label']: item['count'] for item in context['emotion_distribution']}
    avg_score = context['summary_stats']['avg_emotion_score']
    highlights = context['highlights']

    if avg_score is None:
        return '这段时间里可用的情绪评分还不够多，当前更适合从地点和记忆点角度回顾旅程。'

    tone = _score_label(avg_score)
    positive = distribution.get('积极', 0)
    neutral = distribution.get('中性', 0)
    negative = distribution.get('消极', 0)
    review = f"整体情绪表现为 {tone}。"

    if positive >= max(neutral, negative):
        review += f" 在 {positive} 篇偏积极记录的带动下，这段旅程整体基调更明亮。"
    elif negative > positive:
        review += f" 有 {negative} 篇记录呈现出明显波动，说明这段旅程里也夹杂着疲惫或失落。"
    else:
        review += ' 多数记录维持在平稳区间，情绪起伏存在但不剧烈。'

    best_highlight = next((item for item in highlights if item['emotion_score'] is not None), None)
    if best_highlight:
        review += f" 最突出的节点出现在 {best_highlight['date']} 的《{best_highlight['title']}》。"
    return review


def _build_memory_quote(context):
    for item in context['highlights']:
        if item['memory_point']:
            return item['memory_point']
        if item['excerpt']:
            return item['excerpt']
    return '旅程真正留下来的，通常不是路线本身，而是那些被认真记录下来的瞬间。'


def _build_local_report(context):
    period = context['period']
    stats = context['summary_stats']
    locations = context['locations']
    start_date = date.fromisoformat(period['start_date'])
    end_date = date.fromisoformat(period['end_date'])
    range_title = _range_title_text(start_date, end_date)
    top_location_name = locations[0]['name'] if locations else '旅程'
    avg_score = stats['avg_emotion_score']

    title = f'{range_title}{top_location_name}等地旅行总结' if locations else f'{range_title}旅行总结'
    subtitle = (
        f"共记录 {stats['diary_count']} 篇日记，走过 {stats['city_count']} 个地点，"
        f"整体情绪为 {_score_label(avg_score)}。"
        if avg_score is not None
        else f"共记录 {stats['diary_count']} 篇日记，走过 {stats['city_count']} 个地点。"
    )

    summary_parts = [
        f"本次时间范围覆盖 {period['total_days']} 天",
        f"实际有记录的旅行日为 {period['travel_day_count']} 天",
        f"共留下 {stats['diary_count']} 篇日记",
    ]
    if stats['total_distance_km']:
        summary_parts.append(f"轨迹累计约 {stats['total_distance_km']} 公里")
    if avg_score is not None:
        summary_parts.append(f"平均情绪评分为 {_format_score(avg_score)}")
    summary = '，'.join(summary_parts) + '。'

    return {
        'report_title': title,
        'report_subtitle': subtitle,
        'summary': summary,
        'highlights': _build_highlight_lines(context['highlights']),
        'emotion_review': _build_emotion_review(context),
        'travel_preferences': _build_travel_preferences(context),
        'next_trip_suggestions': _build_next_trip_suggestions(context),
        'memory_quote': _build_memory_quote(context),
    }


def _normalize_string_list(value, fallback):
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return items or fallback
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return fallback


def _normalize_cover_image(value):
    if isinstance(value, str):
        image_url = value.strip()
        image_meta = {}
    elif isinstance(value, dict):
        image_url = str(value.get('image_url') or value.get('url') or '').strip()
        image_meta = value
    else:
        return None

    if not image_url or not image_url.startswith(('http://', 'https://')):
        return None

    return {
        'image_url': image_url,
        'diary_id': image_meta.get('diary_id'),
        'diary_title': str(image_meta.get('diary_title') or '').strip(),
        'diary_date': str(image_meta.get('diary_date') or '').strip(),
        'location': str(image_meta.get('location') or '').strip(),
    }


def _merge_report_payload(payload, context):
    fallback = _build_local_report(context)
    if not isinstance(payload, dict):
        return fallback

    merged = dict(fallback)
    text_fields = [
        'report_title',
        'report_subtitle',
        'summary',
        'emotion_review',
        'memory_quote',
    ]
    list_fields = [
        'highlights',
        'travel_preferences',
        'next_trip_suggestions',
    ]

    for field in text_fields:
        value = payload.get(field)
        if isinstance(value, str) and value.strip():
            merged[field] = value.strip()

    for field in list_fields:
        merged[field] = _normalize_string_list(payload.get(field), fallback[field])

    return merged


def _normalize_export_bundle(payload):
    period = payload.get('period') if isinstance(payload.get('period'), dict) else {}
    summary_stats = payload.get('summary_stats') if isinstance(payload.get('summary_stats'), dict) else {}
    report = payload.get('report') if isinstance(payload.get('report'), dict) else {}
    cover_image = _normalize_cover_image(payload.get('cover_image'))
    if cover_image is None and isinstance(payload.get('gallery_images'), list) and payload.get('gallery_images'):
        cover_image = _normalize_cover_image(payload.get('gallery_images')[0])

    return {
        'period': {
            'start_date': str(period.get('start_date') or ''),
            'end_date': str(period.get('end_date') or ''),
            'range_type': str(period.get('range_type') or ''),
        },
        'source': str(payload.get('source') or 'local'),
        'summary_stats': {
            'diary_count': summary_stats.get('diary_count', 0),
            'city_count': summary_stats.get('city_count', 0),
            'total_distance_km': summary_stats.get('total_distance_km', 0),
            'avg_emotion_score': summary_stats.get('avg_emotion_score'),
        },
        'cover_image': cover_image,
        'report': {
            'report_title': str(report.get('report_title') or '').strip(),
            'report_subtitle': str(report.get('report_subtitle') or '').strip(),
            'summary': str(report.get('summary') or '').strip(),
            'highlights': _normalize_string_list(report.get('highlights'), []),
            'emotion_review': str(report.get('emotion_review') or '').strip(),
            'travel_preferences': _normalize_string_list(report.get('travel_preferences'), []),
            'next_trip_suggestions': _normalize_string_list(report.get('next_trip_suggestions'), []),
            'memory_quote': str(report.get('memory_quote') or '').strip(),
        },
    }


@report_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_report():
    current_user_id = int(get_jwt_identity())
    payload = request.get_json() or {}

    try:
        start_date, end_date, range_type = _resolve_report_range(current_user_id, payload)
    except ValueError as exc:
        return jsonify({'msg': str(exc)}), 400

    if not start_date or not end_date:
        return jsonify({'msg': '当前还没有可生成总结的旅行日记'}), 404

    rows = (
        db.session.query(Diary, AIAnalysis)
        .outerjoin(AIAnalysis, AIAnalysis.diary_id == Diary.id)
        .filter(
            Diary.user_id == current_user_id,
            Diary.is_draft == False,
            Diary.date >= start_date,
            Diary.date <= end_date,
        )
        .order_by(Diary.date.asc(), Diary.id.asc())
        .all()
    )

    if not rows:
        return jsonify({'msg': '该时间范围内暂无可生成报告的日记'}), 404

    report_context = _build_report_context(rows, start_date, end_date)
    report_style = (payload.get('report_style') or 'warm').strip() or 'warm'

    generated = dify_client.generate_travel_report(
        report_context,
        start_date.isoformat(),
        end_date.isoformat(),
        report_style=report_style,
    )
    source = 'dify' if generated else 'local'
    report_payload = _merge_report_payload(generated, report_context)

    return jsonify(
        {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'range_type': range_type,
            },
            'source': source,
            'report_style': report_style,
            'summary_stats': report_context['summary_stats'],
            'cover_image': report_context['cover_image'],
            'report': report_payload,
        }
    ), 200


@report_bp.route('/export-pdf', methods=['POST'])
@jwt_required()
def export_report_pdf():
    current_user_id = int(get_jwt_identity())
    payload = request.get_json() or {}
    export_bundle = _normalize_export_bundle(payload)

    if not export_bundle['period']['start_date'] or not export_bundle['period']['end_date']:
        return jsonify({'msg': '缺少报告时间范围，无法导出 PDF'}), 400
    if not export_bundle['report']['report_title'] or not export_bundle['report']['summary']:
        return jsonify({'msg': '缺少完整报告内容，无法导出 PDF'}), 400

    upload_root = current_app.config.get('UPLOAD_FOLDER') or 'uploads'
    export_dir = os.path.join(current_app.root_path, upload_root, 'report_exports')
    os.makedirs(export_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    file_name = f'travel_report_{current_user_id}_{timestamp}_{uuid.uuid4().hex[:8]}.pdf'
    file_path = os.path.join(export_dir, file_name)

    try:
        build_travel_report_pdf(export_bundle, file_path)
    except RuntimeError as exc:
        return jsonify({'msg': str(exc)}), 500
    except Exception:
        return jsonify({'msg': 'PDF 生成失败'}), 500

    return jsonify(
        {
            'file_name': file_name,
            'msg': 'PDF 已生成',
        }
    ), 200


@report_bp.route('/download/<path:file_name>', methods=['GET'])
@jwt_required()
def download_report_pdf(file_name):
    current_user_id = int(get_jwt_identity())
    safe_name = os.path.basename(file_name or '')

    if not safe_name.endswith('.pdf') or not safe_name.startswith(f'travel_report_{current_user_id}_'):
        return jsonify({'msg': '文件不存在或无权访问'}), 404

    upload_root = current_app.config.get('UPLOAD_FOLDER') or 'uploads'
    file_path = os.path.join(current_app.root_path, upload_root, 'report_exports', safe_name)
    if not os.path.exists(file_path):
        return jsonify({'msg': '文件不存在'}), 404

    return send_file(
        file_path,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=safe_name,
        max_age=0,
    )

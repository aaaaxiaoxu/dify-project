from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import jieba
import jieba.analyse
import re
import json
from collections import Counter
from sqlalchemy.exc import IntegrityError
from extensions import dify_client, db
from models import Diary, AIAnalysis
from utils.html_sanitize import html_to_plain_text

ai_bp = Blueprint('ai', __name__)

# 定义情感词典
emotion_lexicon = {
    "positive": ["开心", "快乐", "高兴", "愉快", "兴奋", "欢乐", "喜悦", "满足", "幸福", "愉悦", "激动", "惊喜", "欣慰", "畅快", "舒畅"],
    "negative": ["难过", "悲伤", "忧郁", "沮丧", "失望", "痛苦", "烦恼", "焦虑", "担忧", "愤怒", "生气", "郁闷", "烦躁"],
    "neutral": ["平静", "安宁", "放松", "悠闲", "舒适", "恬静", "淡然", "冷静"]
}

# 定义地点类型词典
location_types = {
    "自然风光": ["山", "水", "湖", "河", "海", "海滩", "森林", "草原", "沙漠", "瀑布", "峡谷", "自然"],
    "城市景观": ["城市", "都市", "街", "广场", "商业", "购物", "繁华", "摩天大楼", "CBD"],
    "历史文化": ["古镇", "古街", "历史", "文化", "传统", "老城", "古迹", "博物馆", "文物", "遗址"],
    "现代建筑": ["现代", "科技", "高楼", "建筑", "摩登", "时尚", "地标", "剧院", "中心"],
    "乡村田园": ["乡村", "田园", "农家乐", "田野", "农庄", "农村", "果园", "农场"]
}

# 定义活动类型词典
activity_types = {
    "观光游览": ["游览", "参观", "欣赏", "观看", "漫步", "走走", "逛"],
    "美食体验": ["吃", "喝", "品尝", "美食", "餐厅", "小吃", "特色菜"],
    "休闲娱乐": ["休息", "放松", "娱乐", "玩耍", "游戏", "休闲"],
    "户外运动": ["爬山", "徒步", "骑行", "游泳", "滑雪", "运动"],
    "文化体验": ["学习", "了解", "体验", "感受", "文化", "传统"]
}

def preprocess_text(text):
    """
    预处理文本
    """
    # 去除特殊字符，保留中文、英文和数字
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', ' ', text)
    # 去除多余空格
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_keywords_tfidf(content, topK=10):
    """
    使用TF-IDF算法提取关键词
    """
    # 使用jieba进行分词
    words = jieba.lcut(content)
    # 过滤掉长度小于2的词
    words = [word for word in words if len(word) >= 2]
    
    # 如果词汇量太少，直接返回分词结果
    if len(words) < 5:
        return list(set(words))
    
    # 使用TF-IDF提取关键词
    tfidf_keywords = jieba.analyse.extract_tags(content, topK=topK, withWeight=False)
    return tfidf_keywords

def analyze_emotion(content):
    """
    分析情感倾向
    """
    # 分词
    words = jieba.lcut(content.lower())
    
    # 统计各类情感词出现次数
    emotion_counts = {"positive": 0, "negative": 0, "neutral": 0}
    
    for word in words:
        for emotion_type, emotion_words in emotion_lexicon.items():
            if word in emotion_words:
                emotion_counts[emotion_type] += 1
    
    # 判断主要情感倾向
    total_emotions = sum(emotion_counts.values())
    
    if total_emotions == 0:
        return "中性", "这篇日记的情感表达较为含蓄，可以进一步描述当时的心情和感受。", 0.0
    
    # 计算情感比例
    positive_ratio = emotion_counts["positive"] / total_emotions
    negative_ratio = emotion_counts["negative"] / total_emotions
    neutral_ratio = emotion_counts["neutral"] / total_emotions
    emotion_score = round(max(-1.0, min(1.0, positive_ratio - negative_ratio)), 1)
    
    # 确定主要情感
    if positive_ratio >= 0.5:
        main_emotion = "积极"
        description = "这篇日记表达了作者积极向上的情感，整体氛围愉快轻松。"
    elif negative_ratio >= 0.5:
        main_emotion = "消极"
        description = "这篇日记表达了作者略带感伤的情感，可以适当调节心情。"
    elif neutral_ratio >= 0.5:
        main_emotion = "平和"
        description = "这篇日记表达了作者平和宁静的情感，整体氛围安详舒适。"
    else:
        # 混合情感
        main_emotion = "复杂"
        description = "这篇日记表达了作者复杂多变的情感，生活体验丰富多彩。"
    
    return main_emotion, description, emotion_score

def identify_location_type(content):
    """
    识别地点类型
    """
    # 分词
    words = jieba.lcut(content.lower())
    
    # 统计各类地点词出现次数
    location_counts = {}
    for loc_type, loc_words in location_types.items():
        count = sum(1 for word in words if word in loc_words)
        if count > 0:
            location_counts[loc_type] = count
    
    # 返回出现频率最高的地点类型
    if location_counts:
        primary_type = max(location_counts, key=location_counts.get)
        return primary_type, location_counts
    else:
        return "未识别", {}

def identify_activities(content):
    """
    识别活动类型
    """
    # 分词
    words = jieba.lcut(content.lower())
    
    # 统计各类活动词出现次数
    activity_counts = {}
    for act_type, act_words in activity_types.items():
        count = sum(1 for word in words if word in act_words)
        if count > 0:
            activity_counts[act_type] = count
    
    # 返回出现频率最高的活动类型
    if activity_counts:
        primary_activities = sorted(activity_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        return [act[0] for act in primary_activities]
    else:
        return ["未识别"]

def generate_travel_advice(location_type, activities):
    """
    根据地点类型和活动生成旅行建议
    """
    advice_templates = {
        "自然风光": [
            "根据您对自然风光的喜爱，推荐您下次可以去张家界、九寨沟等自然景区体验更壮丽的山水之美。",
            "如果您喜欢山水景色，不妨考虑去桂林漓江或黄山，感受'桂林山水甲天下'的美誉。",
            "喜爱自然风光的您可以去张家界的天门山或贵州的黄果树瀑布，体验大自然的鬼斧神工。"
        ],
        "城市景观": [
            "根据您对都市生活的兴趣，推荐您可以去上海、深圳等现代化大都市感受繁华与便利。",
            "如果您喜欢城市风光，可以考虑去北京或上海，体验大都市的繁华与文化底蕴。",
            "喜爱城市景观的您可以去广州或杭州，感受南方城市的现代魅力与历史韵味。"
        ],
        "历史文化": [
            "根据您对历史文化的兴趣，推荐您可以去平遥古城、乌镇等历史名镇深入体验传统文化。",
            "如果您对历史文化感兴趣，不妨去西安看看兵马俑，感受千年古都的文化底蕴。",
            "喜爱历史文化的您可以去南京或洛阳，探索中国古代文明的深厚底蕴。"
        ],
        "现代建筑": [
            "根据您对现代建筑的兴趣，推荐您可以去北京的国家大剧院、上海中心等地标建筑参观。",
            "如果您喜欢现代建筑，可以去深圳的平安大厦或广州的小蛮腰，感受现代建筑的魅力。",
            "对现代建筑感兴趣的您可以去天津或重庆，欣赏这些城市的现代建筑群。"
        ],
        "乡村田园": [
            "根据您对田园风光的喜爱，推荐您可以去婺源、桂林等乡村地区体验农家乐和田园生活。",
            "如果您喜欢乡村田园，不妨去云南的元阳梯田或江西的婺源，感受田园生活的宁静美好。",
            "喜爱田园风光的您可以去湖南的桃花源或四川的田园风光区，享受乡村的悠闲时光。"
        ]
    }
    
    activity_advice = {
        "观光游览": "您喜欢观光游览，建议可以选择一些风景名胜区，慢慢欣赏自然和人文景观。",
        "美食体验": "您注重美食体验，建议在旅行中多尝试当地特色美食，这也是了解当地文化的好方式。",
        "休闲娱乐": "您偏爱休闲娱乐，建议选择一些度假村或休闲场所，放松身心。",
        "户外运动": "您喜欢户外运动，可以选择一些有徒步、攀岩等项目的景区，享受运动的乐趣。",
        "文化体验": "您重视文化体验，建议多参观博物馆、历史遗迹等，深入了解当地的历史文化。"
    }
    
    # 获取地点类型建议
    location_advice = advice_templates.get(location_type, [
        "建议您可以尝试不同类型的旅行体验，丰富旅行经历。"
    ])
    
    # 随机选择一条地点建议
    import random
    selected_advice = random.choice(location_advice)
    
    # 添加活动建议
    if activities and activities[0] != "未识别":
        primary_activity = activities[0]
        activity_suggestion = activity_advice.get(primary_activity, "")
        if activity_suggestion:
            selected_advice += f" {activity_suggestion}"
    
    return selected_advice

def analyze_writing_style(content):
    """
    分析写作风格
    """
    # 计算文本长度
    char_count = len(content)
    
    # 分词并计算词数
    words = jieba.lcut(content)
    word_count = len(words)
    
    # 计算句子数（简单按句号、感叹号、问号分割）
    sentence_count = len(re.split(r'[。！？]', content)) - 1
    
    # 计算平均句长
    avg_sentence_length = word_count / max(sentence_count, 1)
    
    # 分析写作风格
    if char_count < 100:
        style = "简洁"
        suggestion = "您的日记内容较为简洁，可以尝试添加更多细节描述，让内容更加丰富。"
    elif avg_sentence_length > 20:
        style = "详细"
        suggestion = "您的日记描述较为详细，很好地记录了旅行的点点滴滴。"
    else:
        style = "适中"
        suggestion = "您的日记详略得当，既有重点描述又不过于冗长。"
    
    return style, suggestion

def analyze_diary_content(content):
    """
    综合分析日记内容
    """
    plain = html_to_plain_text(content or "")
    if not plain or not plain.strip():
        return {
            "emotion_label": "中性",
            "emotion_analysis": "未提供内容，无法进行情感分析。",
            "emotion_score": 0.0,
            "keywords": [],
            "travel_advice": "请提供详细的旅行日记内容以获取个性化建议。",
            "memory_point": "",
            "writing_style": "未知",
            "writing_suggestion": "请提供内容以获取写作风格分析。"
        }

    # 预处理文本（富文本已转为纯文本）
    processed_content = preprocess_text(plain)
    
    # 1. 情感分析
    main_emotion, emotion_description, emotion_score = analyze_emotion(processed_content)
    
    # 2. 关键词提取
    keywords = extract_keywords_tfidf(processed_content, topK=5)
    
    # 3. 地点类型识别
    location_type, location_details = identify_location_type(processed_content)
    
    # 4. 活动类型识别
    activities = identify_activities(processed_content)
    
    # 5. 生成旅行建议
    travel_advice = generate_travel_advice(location_type, activities)
    
    # 6. 写作风格分析
    writing_style, writing_suggestion = analyze_writing_style(plain)
    
    return {
        "emotion_label": main_emotion,
        "emotion_analysis": emotion_description,
        "emotion_score": emotion_score,
        "keywords": keywords,
        "travel_advice": travel_advice,
        "memory_point": "",
        "writing_style": writing_style,
        "writing_suggestion": writing_suggestion
    }


def _build_local_writing_feedback(content):
    plain = html_to_plain_text(content or "")
    if not plain or not plain.strip():
        return {
            "writing_style": "未知",
            "writing_suggestion": "请提供内容以获取写作风格分析。"
        }

    writing_style, writing_suggestion = analyze_writing_style(plain)
    return {
        "writing_style": writing_style,
        "writing_suggestion": writing_suggestion
    }


def _merge_writing_feedback(result_payload, content):
    payload = dict(result_payload or {})
    local_feedback = _build_local_writing_feedback(content)

    if not payload.get("writing_style"):
        payload["writing_style"] = local_feedback["writing_style"]
    if not payload.get("writing_suggestion"):
        payload["writing_suggestion"] = local_feedback["writing_suggestion"]

    plain = html_to_plain_text(content or "")
    writing_text = plain if plain.strip() else (content or "")
    dify_writing = dify_client.generate_writing_suggestion(writing_text)
    if dify_writing:
        payload["writing_suggestion"] = dify_writing

    return payload


def _serialize_keywords_for_storage(keywords_value):
    if isinstance(keywords_value, list):
        return json.dumps(keywords_value, ensure_ascii=False)
    if keywords_value is None:
        return "[]"
    return str(keywords_value)


def _parse_keywords_from_storage(keywords_value):
    if isinstance(keywords_value, list):
        return keywords_value
    if isinstance(keywords_value, str):
        text = keywords_value.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, TypeError):
            return [item.strip() for item in text.split(',') if item.strip()]
    return []


def _get_memory_point_value(analysis_result):
    return (analysis_result.get("memory_point") or "").strip()


def _serialize_ai_analysis_record(record):
    memory_point = record.memory_point or ""
    return {
        "emotion_analysis": record.emotion_analysis,
        "emotion_score": record.emotion_score,
        "emotion_label": record.emotion_label or "",
        "keywords": _parse_keywords_from_storage(record.keywords),
        "travel_advice": record.travel_advice,
        "memory_point": memory_point,
        "writing_style": "",
        "writing_suggestion": "",
    }


def _build_ai_analysis_record(diary_id, analysis_result):
    return AIAnalysis(
        diary_id=diary_id,
        emotion_analysis=analysis_result.get("emotion_analysis", ""),
        emotion_score=analysis_result.get("emotion_score"),
        emotion_label=(analysis_result.get("emotion_label") or "").strip() or None,
        keywords=_serialize_keywords_for_storage(analysis_result.get("keywords", [])),
        travel_advice=analysis_result.get("travel_advice", ""),
        memory_point=_get_memory_point_value(analysis_result) or None,
    )


def _assign_ai_analysis_record(record, analysis_result):
    record.emotion_analysis = analysis_result.get("emotion_analysis", "")
    record.emotion_score = analysis_result.get("emotion_score")
    record.emotion_label = (analysis_result.get("emotion_label") or "").strip() or None
    record.keywords = _serialize_keywords_for_storage(analysis_result.get("keywords", []))
    record.travel_advice = analysis_result.get("travel_advice", "")
    record.memory_point = _get_memory_point_value(analysis_result) or None
    return record


def _save_ai_analysis_record(diary_id, analysis_result):
    record = AIAnalysis.query.filter_by(diary_id=diary_id).first()
    if record:
        _assign_ai_analysis_record(record, analysis_result)
    else:
        record = _build_ai_analysis_record(diary_id, analysis_result)
        db.session.add(record)

    try:
        db.session.commit()
        return record
    except IntegrityError:
        db.session.rollback()
        record = AIAnalysis.query.filter_by(diary_id=diary_id).first()
        if not record:
            raise
        _assign_ai_analysis_record(record, analysis_result)
        db.session.commit()
        return record

@ai_bp.route('/analysis', methods=['POST'])
@jwt_required()
def ai_analysis():
    data = request.get_json() or {}
    diary_id = data.get('diary_id')

    # ---- 兼容模式：没有 diary_id 时用传入的 content 做本地分析（新建日记场景） ----
    if not diary_id:
        diary_content = data.get('content', '')
        if not diary_content:
            return jsonify({"error": "缺少 diary_id 或 content 参数"}), 400
        analysis_result = analyze_diary_content(diary_content)
        return jsonify(analysis_result), 200

    user_id = get_jwt_identity()
    diary = Diary.query.filter_by(id=diary_id, user_id=user_id).first()
    if not diary:
        return jsonify({"error": "日记不存在"}), 404

    diary_content = diary.content or ''
    plain_for_llm = html_to_plain_text(diary_content)
    writing_source = plain_for_llm if plain_for_llm.strip() else diary_content

    # ---- 1. 查库：已有分析结果则直接返回 ----
    existing = AIAnalysis.query.filter_by(diary_id=diary_id).first()
    needs_backfill = bool(
        existing and
        not (existing.emotion_label or '').strip() and
        not (existing.memory_point or '').strip()
    )
    if existing and not needs_backfill:
        existing_payload = _serialize_ai_analysis_record(existing)
        return jsonify(_merge_writing_feedback(existing_payload, writing_source)), 200

    # ---- 2. 获取文字、图片、视频 ----

    # 收集图片和视频 URL
    image_urls = [img.image_url for img in diary.images] if diary.images else []
    video_urls = [vid.video_url for vid in diary.videos] if diary.videos else []

    # ---- 3. 调用 Dify 分析（传文字 + 图片 + 视频） ----
    dify_result = dify_client.analyze_diary_content(
        plain_for_llm if plain_for_llm.strip() else diary_content,
        image_urls=image_urls,
        video_urls=video_urls
    )

    if dify_result:
        analysis_result = dify_result
    else:
        # Dify 不可用时回退到本地分析
        analysis_result = analyze_diary_content(diary_content)

    analysis_result = _merge_writing_feedback(analysis_result, writing_source)

    # ---- 4. 存库 ----
    _save_ai_analysis_record(diary_id, analysis_result)

    return jsonify(analysis_result), 200


@ai_bp.route('/analysis/refresh', methods=['POST'])
@jwt_required()
def ai_analysis_refresh():
    """强制重新分析（日记编辑后可调用）"""
    data = request.get_json() or {}
    diary_id = data.get('diary_id')

    if not diary_id:
        return jsonify({"error": "缺少 diary_id 参数"}), 400

    # 查询日记
    user_id = get_jwt_identity()
    diary = Diary.query.filter_by(id=diary_id, user_id=user_id).first()
    if not diary:
        return jsonify({"error": "日记不存在"}), 404

    diary_content = diary.content or ''
    plain_for_llm = html_to_plain_text(diary_content)
    writing_source = plain_for_llm if plain_for_llm.strip() else diary_content
    image_urls = [img.image_url for img in diary.images] if diary.images else []
    video_urls = [vid.video_url for vid in diary.videos] if diary.videos else []

    dify_result = dify_client.analyze_diary_content(
        plain_for_llm if plain_for_llm.strip() else diary_content,
        image_urls=image_urls,
        video_urls=video_urls
    )

    if dify_result:
        analysis_result = dify_result
    else:
        analysis_result = analyze_diary_content(diary_content)

    analysis_result = _merge_writing_feedback(analysis_result, writing_source)

    # 存入新记录
    _save_ai_analysis_record(diary_id, analysis_result)

    return jsonify(analysis_result), 200

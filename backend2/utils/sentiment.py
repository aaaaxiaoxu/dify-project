import json
import os
from collections import Counter, defaultdict

import jieba


LEXICON_SOURCE = (
    "基础词汇来自现有项目高频旅游情绪词，并参考大连理工大学中文情感词汇本体、"
    "BosonNLP 情感词典和知网情感词典的常见极性分类进行人工筛选。"
)

POSITIVE_WORD_WEIGHTS = {
    "开心": 1.0,
    "快乐": 1.0,
    "高兴": 1.0,
    "愉快": 1.0,
    "兴奋": 1.1,
    "欢乐": 1.0,
    "喜悦": 1.1,
    "满足": 0.9,
    "幸福": 1.1,
    "愉悦": 1.0,
    "激动": 1.0,
    "惊喜": 1.0,
    "欣慰": 0.9,
    "畅快": 1.0,
    "舒畅": 1.0,
    "喜欢": 0.9,
    "美好": 1.0,
    "漂亮": 0.8,
    "治愈": 1.0,
    "难忘": 0.8,
    "舒服": 0.8,
    "放松": 0.7,
    "安心": 0.8,
    "期待": 0.7,
    "好": 0.6,
}

NEGATIVE_WORD_WEIGHTS = {
    "难过": 1.0,
    "悲伤": 1.0,
    "忧郁": 1.0,
    "沮丧": 1.0,
    "失望": 1.0,
    "痛苦": 1.1,
    "烦恼": 0.9,
    "焦虑": 1.0,
    "担忧": 0.8,
    "愤怒": 1.1,
    "生气": 1.0,
    "郁闷": 1.0,
    "烦躁": 0.9,
    "疲惫": 0.8,
    "糟糕": 1.1,
    "拥挤": 0.7,
    "失落": 1.0,
    "遗憾": 0.8,
    "害怕": 1.0,
    "不安": 0.9,
    "失眠": 0.8,
    "落空": 0.9,
    "闷": 0.6,
}

NEUTRAL_WORDS = {
    "平静",
    "安宁",
    "悠闲",
    "舒适",
    "恬静",
    "淡然",
    "冷静",
    "安静",
    "宁静",
    "平和",
}

NEGATION_WORDS = {
    "不",
    "没",
    "没有",
    "未",
    "无",
    "不是",
    "别",
    "无法",
    "不能",
    "难以",
    "并不",
    "从不",
    "毫不",
    "一点也不",
    "不太",
}

DEGREE_ADVERBS = {
    "极其": 2.0,
    "无比": 2.0,
    "特别": 1.7,
    "非常": 1.8,
    "十分": 1.8,
    "格外": 1.6,
    "太": 1.5,
    "很": 1.4,
    "挺": 1.2,
    "比较": 1.2,
    "有点": 0.7,
    "稍微": 0.6,
    "略": 0.6,
    "不太": 0.7,
}

EVAL_SAMPLE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "sentiment_eval_samples.json",
)


for word in (
    list(POSITIVE_WORD_WEIGHTS)
    + list(NEGATIVE_WORD_WEIGHTS)
    + list(NEUTRAL_WORDS)
    + list(NEGATION_WORDS)
    + list(DEGREE_ADVERBS)
):
    jieba.add_word(word)


def _tokens(text):
    return [token.strip() for token in jieba.lcut(text or "") if token.strip()]


def _sentiment_match(token):
    if token in POSITIVE_WORD_WEIGHTS:
        return 1, POSITIVE_WORD_WEIGHTS[token], token, False
    if token in NEGATIVE_WORD_WEIGHTS:
        return -1, NEGATIVE_WORD_WEIGHTS[token], token, False

    for negation in sorted(NEGATION_WORDS, key=len, reverse=True):
        if not token.startswith(negation):
            continue
        base = token[len(negation):]
        if base in POSITIVE_WORD_WEIGHTS:
            return 1, POSITIVE_WORD_WEIGHTS[base], base, True
        if base in NEGATIVE_WORD_WEIGHTS:
            return -1, NEGATIVE_WORD_WEIGHTS[base], base, True
    return 0, 0.0, "", False


def _context_adjustment(tokens, index, window_size=3):
    start = max(0, index - window_size)
    window = tokens[start:index]
    degree = 1.0
    negation_count = 0

    for token in window:
        if token in DEGREE_ADVERBS:
            degree *= DEGREE_ADVERBS[token]
        if token in NEGATION_WORDS:
            negation_count += 1

    return degree, negation_count


def _label_from_score(score, counts):
    if counts["positive"] and counts["negative"] and abs(score) < 0.5:
        return "复杂"
    if score >= 0.2:
        return "积极"
    if score <= -0.2:
        return "消极"
    if counts["neutral"]:
        return "平和"
    return "中性"


def _description(label, score, counts):
    count_text = (
        f"正向词 {counts['positive']} 个、负向词 {counts['negative']} 个、"
        f"平和词 {counts['neutral']} 个"
    )
    rule_text = "已按否定词窗口和程度副词权重修正后计算情绪评分"

    if label == "积极":
        return f"这篇日记整体呈现积极情绪，{count_text}，{rule_text}，得分为 {score:.2f}。"
    if label == "消极":
        return f"这篇日记整体呈现消极情绪，{count_text}，{rule_text}，得分为 {score:.2f}。"
    if label == "复杂":
        return f"这篇日记同时包含正负向表达，{count_text}，{rule_text}，情绪较为复杂。"
    if label == "平和":
        return f"这篇日记以平和、安静的描述为主，{count_text}，情绪波动较小。"
    return "这篇日记的情感表达较为含蓄，未识别到足够明确的情感词。"


def analyze_emotion_rules(content):
    tokens = _tokens(content)
    counts = Counter({"positive": 0, "negative": 0, "neutral": 0})
    positive_strength = 0.0
    negative_strength = 0.0
    evidence = []

    for index, token in enumerate(tokens):
        polarity, base_weight, matched_word, prefix_negated = _sentiment_match(token)
        if polarity == 0:
            if token in NEUTRAL_WORDS:
                counts["neutral"] += 1
            continue

        degree, negation_count = _context_adjustment(tokens, index)
        is_negated = prefix_negated or bool(negation_count % 2)
        if is_negated:
            if polarity < 0:
                counts["neutral"] += 1
                evidence.append(
                    {
                        "word": matched_word,
                        "polarity": "neutralized",
                        "weight": 0.0,
                        "degree": round(degree, 3),
                        "negated": True,
                    }
                )
                continue
            polarity *= -1
        weighted = base_weight * degree

        if polarity > 0:
            counts["positive"] += 1
            positive_strength += weighted
        else:
            counts["negative"] += 1
            negative_strength += weighted

        evidence.append(
            {
                "word": matched_word,
                "polarity": "positive" if polarity > 0 else "negative",
                "weight": round(weighted, 3),
                "degree": round(degree, 3),
                "negated": is_negated,
            }
        )

    sentiment_strength = positive_strength + negative_strength
    if sentiment_strength == 0:
        score = 0.0
    else:
        score = (positive_strength - negative_strength) / sentiment_strength
    score = round(max(-1.0, min(1.0, score)), 2)
    label = _label_from_score(score, counts)

    return {
        "emotion_label": label,
        "emotion_analysis": _description(label, score, counts),
        "emotion_score": score,
        "lexicon_source": LEXICON_SOURCE,
        "formula": (
            "score = (sum(adjusted_positive_weight) - sum(adjusted_negative_weight)) "
            "/ sum(all_adjusted_sentiment_weight)，再截断到 [-1, 1]"
        ),
        "counts": dict(counts),
        "evidence": evidence,
    }


def load_sentiment_eval_samples(path=EVAL_SAMPLE_PATH):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def evaluate_sentiment_samples(samples=None):
    samples = samples if samples is not None else load_sentiment_eval_samples()
    labels = sorted({sample["expected_label"] for sample in samples})
    confusion = {label: Counter() for label in labels}
    support = Counter()
    correct = 0
    predictions = []

    for sample in samples:
        expected = sample["expected_label"]
        predicted = analyze_emotion_rules(sample["text"])["emotion_label"]
        support[expected] += 1
        confusion[expected][predicted] += 1
        correct += int(expected == predicted)
        predictions.append(
            {
                "id": sample.get("id"),
                "expected_label": expected,
                "predicted_label": predicted,
            }
        )

    per_label = {}
    for label in labels:
        true_positive = confusion[label][label]
        false_positive = sum(confusion[other][label] for other in labels if other != label)
        false_negative = sum(count for pred, count in confusion[label].items() if pred != label)
        precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
        recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_label[label] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": support[label],
        }

    macro_f1 = sum(item["f1"] for item in per_label.values()) / max(len(per_label), 1)
    return {
        "total": len(samples),
        "accuracy": round(correct / max(len(samples), 1), 4),
        "macro_f1": round(macro_f1, 4),
        "per_label": per_label,
        "confusion_matrix": {
            label: dict(confusion[label])
            for label in labels
        },
        "predictions": predictions,
    }

import re
import json
import requests
import logging

logger = logging.getLogger(__name__)


class DifyClient:
    def __init__(self):
        self.api_key = None
        self.api_url = None
        self.writing_api_key = None
        self.writing_api_url = None
        self.report_api_key = None
        self.report_api_url = None
        
    def init_app(self, app):
        self.api_key = app.config.get('DIFY_API_KEY')
        self.api_url = app.config.get('DIFY_API_URL')
        self.writing_api_key = app.config.get('DIFY_WRITING_API_KEY') or self.api_key
        self.writing_api_url = app.config.get('DIFY_WRITING_API_URL') or self.api_url
        self.report_api_key = app.config.get('DIFY_REPORT_API_KEY') or self.api_key
        self.report_api_url = app.config.get('DIFY_REPORT_API_URL') or self.api_url

    def _has_valid_workflow_config(self, api_key, api_url):
        return bool(
            api_key and
            api_url and
            str(api_key).strip() and
            str(api_url).strip() and
            str(api_key).strip() != 'your-dify-api-key'
        )

    def _run_workflow(self, api_key, api_url, inputs, timeout=60, user='travel_diary_user'):
        if not self._has_valid_workflow_config(api_key, api_url):
            return None, 'Dify 工作流未配置'

        url = f"{str(api_url).rstrip('/')}/workflows/run"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            'inputs': inputs,
            'response_mode': 'blocking',
            'user': user
        }

        try:
            resp = requests.post(url, headers=headers, json=data, timeout=timeout)
            if resp.status_code == 200:
                return resp, None
            err_body = resp.text
            logger.warning("Dify API 返回 %s: %s", resp.status_code, err_body)
            return None, f"HTTP {resp.status_code}: {err_body}"
        except Exception as e:
            last_error = f"{type(e).__name__}: {e}"
            logger.warning("Dify API 请求异常: %s", last_error)
            return None, last_error

    def _call_workflow(self, url, headers, content, image_urls=None, video_urls=None, timeout=60):
        """
        调用 Dify 工作流，返回 (response, error_msg)。
        输入变量名与 Dify 工作流"开始"节点保持一致
        """
        inputs = {
            'text': content,
            'diary_content': content,
        }

        # 传入图片文件列表（remote_url 方式）
        if image_urls:
            inputs['image_urls'] = [
                {"type": "image", "transfer_method": "remote_url", "url": u}
                for u in image_urls
            ]
        else:
            inputs['image_urls'] = []

        # 传入视频文件列表（remote_url 方式）
        if video_urls:
            inputs['video_file'] = [
                {"type": "video", "transfer_method": "remote_url", "url": u}
                for u in video_urls
            ]
        else:
            inputs['video_file'] = []

        data = {
            'inputs': inputs,
            'response_mode': 'blocking',
            'user': 'travel_diary_user'
        }
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=timeout)
            if resp.status_code == 200:
                return resp, None
            err_body = resp.text
            logger.warning("Dify API 返回 %s: %s", resp.status_code, err_body)
            return None, f"HTTP {resp.status_code}: {err_body}"
        except Exception as e:
            last_error = f"{type(e).__name__}: {e}"
            logger.warning("Dify API 请求异常: %s", last_error)
            return None, last_error

    def _extract_outputs(self, resp):
        try:
            result = resp.json()
            data = result.get('data', {})

            if data.get('status') != 'succeeded':
                logger.warning("Dify 工作流执行失败: %s", data.get('error', '未知错误'))
                return None

            outputs = data.get('outputs', {})
            if not outputs:
                logger.warning("Dify 返回成功但 outputs 为空: %s", result)
                return None
            return outputs
        except Exception as e:
            logger.error("Dify 返回解析失败: %s", e)
            return None

    def _parse_json_value(self, raw_value):
        if isinstance(raw_value, (dict, list)):
            return raw_value
        if not isinstance(raw_value, str):
            return None

        cleaned = re.sub(r'^```(?:json)?\s*', '', raw_value.strip())
        cleaned = re.sub(r'\s*```$', '', cleaned.strip())
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return None

    def _parse_json_output(self, raw_value):
        parsed = self._parse_json_value(raw_value)
        return parsed if isinstance(parsed, dict) else None

    def _normalize_suggestions_text(self, raw_value):
        parsed = self._parse_json_value(raw_value)
        suggestions = []

        if isinstance(parsed, list):
            suggestions = [str(item).strip() for item in parsed if str(item).strip()]
        elif isinstance(parsed, dict):
            nested = parsed.get('suggestions') or parsed.get('writing_suggestion') or parsed.get('result')
            if isinstance(nested, list):
                suggestions = [str(item).strip() for item in nested if str(item).strip()]
            elif isinstance(nested, str) and nested.strip():
                suggestions = [nested.strip()]
        elif isinstance(raw_value, list):
            suggestions = [str(item).strip() for item in raw_value if str(item).strip()]
        elif isinstance(raw_value, str) and raw_value.strip():
            suggestions = [raw_value.strip()]

        if not suggestions:
            return ''

        return '\n'.join(f'{idx + 1}. {item}' for idx, item in enumerate(suggestions))

    def analyze_diary_content(self, content, image_urls=None, video_urls=None):
        """
        使用Dify工作流分析日记内容
        :param content: 日记文本内容
        :param image_urls: 图片 URL 列表
        :param video_urls: 视频 URL 列表
        """
        if not self._has_valid_workflow_config(self.api_key, self.api_url):
            logger.warning("Dify 未配置 (api_key=%s, api_url=%s)，跳过", bool(self.api_key), bool(self.api_url))
            return None

        if not content or not content.strip():
            return None
            
        url = f"{self.api_url.rstrip('/')}/workflows/run"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        resp, error = self._call_workflow(url, headers, content,
                                          image_urls=image_urls,
                                          video_urls=video_urls)

        if resp is None:
            logger.error("Dify API 所有 inputs 组合均失败: %s", error)
            return None

        outputs = self._extract_outputs(resp)
        if not outputs:
            return None

        try:
            # Dify 工作流返回的是 analysis_result 字段，内容是 JSON 字符串（可能包裹在 markdown 代码块中）
            analysis_raw = outputs.get("analysis_result", "")
            if analysis_raw:
                parsed = self._parse_json_output(analysis_raw)
                if parsed is not None:
                    raw_score = parsed.get("emotion_score")
                    emotion_score = None
                    if raw_score is not None:
                        try:
                            emotion_score = round(max(-1.0, min(1.0, float(raw_score))), 1)
                        except (TypeError, ValueError):
                            emotion_score = None
                    return {
                        "emotion_label": parsed.get("emotion_label") or parsed.get("emotion", ""),
                        "emotion_analysis": parsed.get("emotion_analysis") or parsed.get("emotion", ""),
                        "emotion_score": emotion_score,
                        "keywords": parsed.get("keywords", []),
                        "travel_advice": parsed.get("travel_advice", ""),
                        "memory_point": parsed.get("memory_point", ""),
                        "writing_style": parsed.get("writing_style", ""),
                        "writing_suggestion": parsed.get("writing_suggestion", "")
                    }
                else:
                    logger.warning("Dify analysis_result JSON 解析失败，原始内容: %s", analysis_raw[:200])
                    return {
                        "emotion_label": "",
                        "emotion_analysis": analysis_raw,
                        "emotion_score": None,
                        "keywords": [],
                        "travel_advice": "",
                        "memory_point": "",
                        "writing_style": "",
                        "writing_suggestion": ""
                    }

            # 兼容旧格式：直接从 outputs 取字段
            return {
                "emotion_label": outputs.get("emotion_label", ""),
                "emotion_analysis": outputs.get("emotion_analysis", ""),
                "emotion_score": outputs.get("emotion_score"),
                "keywords": outputs.get("keywords", []),
                "travel_advice": outputs.get("travel_advice", ""),
                "memory_point": outputs.get("memory_point", ""),
                "writing_style": outputs.get("writing_style", ""),
                "writing_suggestion": outputs.get("writing_suggestion", "")
            }
        except Exception as e:
            logger.error("Dify 返回解析失败: %s", e)
            return None

    def generate_writing_suggestion(self, content):
        if not self._has_valid_workflow_config(self.writing_api_key, self.writing_api_url):
            logger.warning("Dify 写作建议工作流未配置，跳过")
            return None

        plain = (content or '').strip()
        if not plain:
            return None

        resp, error = self._run_workflow(
            self.writing_api_key,
            self.writing_api_url,
            {'diary_text': plain},
            timeout=60,
            user='travel_writing_user',
        )
        if resp is None:
            logger.warning("Dify 写作建议工作流失败: %s", error)
            return None

        outputs = self._extract_outputs(resp)
        if not outputs:
            return None

        suggestions_raw = (
            outputs.get('suggestions')
            or outputs.get('writing_suggestion')
            or outputs.get('result')
        )
        suggestion_text = self._normalize_suggestions_text(suggestions_raw)
        return suggestion_text or None

    def generate_travel_report(self, report_context, start_date, end_date, report_style='warm'):
        """
        使用 Dify 工作流生成旅行报告。
        :param report_context: 后端聚合后的 dict
        :param start_date: 开始日期字符串
        :param end_date: 结束日期字符串
        :param report_style: 报告风格
        """
        if not self._has_valid_workflow_config(self.report_api_key, self.report_api_url):
            logger.warning("Dify 报告工作流未配置，跳过")
            return None

        inputs = {
            'report_context_json': json.dumps(report_context, ensure_ascii=False),
            'start_date': start_date,
            'end_date': end_date,
            'report_style': report_style or 'warm',
        }

        resp, error = self._run_workflow(
            self.report_api_key,
            self.report_api_url,
            inputs,
            timeout=90,
            user='travel_report_user',
        )
        if resp is None:
            logger.error("Dify 报告工作流失败: %s", error)
            return None

        outputs = self._extract_outputs(resp)
        if not outputs:
            return None

        report_raw = (
            outputs.get('report_result') or
            outputs.get('report') or
            outputs.get('travel_report')
        )
        parsed = self._parse_json_output(report_raw)
        if parsed is not None:
            return parsed

        direct_fields = {
            "report_title": outputs.get("report_title", ""),
            "report_subtitle": outputs.get("report_subtitle", ""),
            "summary": outputs.get("summary", ""),
            "highlights": outputs.get("highlights", []),
            "emotion_review": outputs.get("emotion_review", ""),
            "travel_preferences": outputs.get("travel_preferences", []),
            "next_trip_suggestions": outputs.get("next_trip_suggestions", []),
            "memory_quote": outputs.get("memory_quote", ""),
        }
        if any(direct_fields.values()):
            return direct_fields

        logger.warning("Dify 报告工作流返回无法识别: %s", outputs)
        return None

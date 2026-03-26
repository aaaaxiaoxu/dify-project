import re
import json
import requests
import logging

logger = logging.getLogger(__name__)


class DifyClient:
    def __init__(self):
        self.api_key = None
        self.api_url = None
        
    def init_app(self, app):
        self.api_key = app.config.get('DIFY_API_KEY')
        self.api_url = app.config.get('DIFY_API_URL')

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

    def analyze_diary_content(self, content, image_urls=None, video_urls=None):
        """
        使用Dify工作流分析日记内容
        :param content: 日记文本内容
        :param image_urls: 图片 URL 列表
        :param video_urls: 视频 URL 列表
        """
        if not self.api_key or not self.api_url:
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

        try:
            result = resp.json()
            data = result.get('data', {})

            # 检查工作流是否执行成功
            if data.get('status') != 'succeeded':
                logger.warning("Dify 工作流执行失败: %s", data.get('error', '未知错误'))
                return None

            outputs = data.get('outputs', {})
            if not outputs:
                logger.warning("Dify 返回成功但 outputs 为空: %s", result)
                return None

            # Dify 工作流返回的是 analysis_result 字段，内容是 JSON 字符串（可能包裹在 markdown 代码块中）
            analysis_raw = outputs.get("analysis_result", "")
            if analysis_raw:
                # 去掉 markdown 代码块标记 ```json ... ```
                cleaned = re.sub(r'^```(?:json)?\s*', '', analysis_raw.strip())
                cleaned = re.sub(r'\s*```$', '', cleaned.strip())
                try:
                    parsed = json.loads(cleaned)
                    return {
                        "emotion_analysis": parsed.get("emotion", ""),
                        "keywords": parsed.get("keywords", []),
                        "travel_advice": parsed.get("travel_advice", ""),
                        "writing_style": parsed.get("writing_style", ""),
                        "writing_suggestion": parsed.get("memory_point", "")
                    }
                except json.JSONDecodeError:
                    logger.warning("Dify analysis_result JSON 解析失败，原始内容: %s", analysis_raw[:200])
                    # 解析失败时直接将原始文本作为情感分析结果返回
                    return {
                        "emotion_analysis": analysis_raw,
                        "keywords": [],
                        "travel_advice": "",
                        "writing_style": "",
                        "writing_suggestion": ""
                    }

            # 兼容旧格式：直接从 outputs 取字段
            return {
                "emotion_analysis": outputs.get("emotion_analysis", ""),
                "keywords": outputs.get("keywords", []),
                "travel_advice": outputs.get("travel_advice", ""),
                "writing_style": outputs.get("writing_style", ""),
                "writing_suggestion": outputs.get("writing_suggestion", "")
            }
        except Exception as e:
            logger.error("Dify 返回解析失败: %s", e)
            return None
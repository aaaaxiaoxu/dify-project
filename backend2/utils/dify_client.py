import requests
import json
from flask import current_app

class DifyClient:
    def __init__(self):
        self.api_key = None
        self.api_url = None
        self.workflow_id = None
        
    def init_app(self, app):
        self.api_key = app.config.get('DIFY_API_KEY')
        self.api_url = app.config.get('DIFY_API_URL')
        self.workflow_id = app.config.get('DIFY_WORKFLOW_ID')
        
    def analyze_diary_content(self, content):
        """
        使用Dify工作流分析日记内容
        """
        if not self.api_key or not self.api_url or not self.workflow_id:
            return None
            
        # Dify工作流API端点
        url = f"{self.api_url}/workflows/{self.workflow_id}/run"
        
        # 请求头
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # 请求数据
        data = {
            'inputs': {
                'diary_content': content
            },
            'response_mode': 'blocking',
            'user': 'travel_diary_user'
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                # 提取输出数据
                outputs = result.get('data', {}).get('outputs', {})
                return {
                    "emotion_analysis": outputs.get("emotion_analysis", ""),
                    "keywords": outputs.get("keywords", []),
                    "travel_advice": outputs.get("travel_advice", ""),
                    "writing_style": outputs.get("writing_style", ""),
                    "writing_suggestion": outputs.get("writing_suggestion", "")
                }
            else:
                print(f"Dify API调用失败: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Dify API调用异常: {str(e)}")
            return None
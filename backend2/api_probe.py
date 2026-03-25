#!/usr/bin/env python3
"""
接口巡检脚本：
1) 自动调用 backend2 已有 API
2) 输出逐项通过/失败结果
3) 保存完整 JSON 报告，便于回归对比
"""

import argparse
import json
import os
import tempfile
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests


class APITestRunner:
    def __init__(self, base_url: str, timeout: int = 15):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.results: List[Dict[str, Any]] = []
        self.token: Optional[str] = None
        self.diary_id: Optional[int] = None
        self.share_link: Optional[str] = None

        ts = int(time.time())
        self.username = f"api_probe_{ts}"
        self.phone = f"139{ts % 100000000:08d}"
        self.password = "123456"

    def _record(
        self,
        name: str,
        passed: bool,
        status_code: Optional[int],
        expected: str,
        response_data: Any = None,
        error: Optional[str] = None,
    ) -> None:
        self.results.append(
            {
                "name": name,
                "passed": passed,
                "status_code": status_code,
                "expected": expected,
                "response": response_data,
                "error": error,
            }
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        expected_status: Optional[List[int]] = None,
        json_data: Any = None,
        files: Any = None,
        need_auth: bool = False,
        name: str = "",
    ) -> Optional[requests.Response]:
        url = f"{self.base_url}{path}"
        headers: Dict[str, str] = {}
        if need_auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        expected_text = f"HTTP in {expected_status}" if expected_status else "请求成功"
        try:
            resp = self.session.request(
                method=method,
                url=url,
                json=json_data,
                files=files,
                headers=headers,
                timeout=self.timeout,
            )
            try:
                payload = resp.json()
            except Exception:
                payload = resp.text[:500]

            passed = True
            if expected_status is not None:
                passed = resp.status_code in expected_status

            self._record(
                name=name or f"{method} {path}",
                passed=passed,
                status_code=resp.status_code,
                expected=expected_text,
                response_data=payload,
                error=None if passed else "状态码不符合预期",
            )
            return resp
        except Exception as ex:
            self._record(
                name=name or f"{method} {path}",
                passed=False,
                status_code=None,
                expected=expected_text,
                response_data=None,
                error=str(ex),
            )
            return None

    def run(self) -> Dict[str, Any]:
        # 1) 未登录访问 profile，期望被拦截
        self._request(
            "GET",
            "/api/user/profile",
            expected_status=[401, 422],
            name="未登录访问 profile 应被拒绝",
        )

        # 2) 注册
        self._request(
            "POST",
            "/api/user/register",
            expected_status=[201],
            json_data={
                "username": self.username,
                "phone": self.phone,
                "password": self.password,
                "nickname": "接口巡检用户",
            },
            name="用户注册",
        )

        # 3) 重复注册应失败
        self._request(
            "POST",
            "/api/user/register",
            expected_status=[400],
            json_data={
                "username": self.username,
                "phone": self.phone,
                "password": self.password,
            },
            name="重复注册应失败",
        )

        # 4) 用户名登录
        login_resp = self._request(
            "POST",
            "/api/user/login",
            expected_status=[200],
            json_data={"username": self.username, "password": self.password},
            name="用户名登录",
        )
        if login_resp is not None:
            try:
                login_json = login_resp.json()
                self.token = login_json.get("access_token")
            except Exception:
                self.token = None

        # 5) 手机号登录
        self._request(
            "POST",
            "/api/user/login",
            expected_status=[200],
            json_data={"phone": self.phone, "password": self.password},
            name="手机号登录",
        )

        # 6) 获取个人资料
        self._request(
            "GET",
            "/api/user/profile",
            expected_status=[200],
            need_auth=True,
            name="获取个人资料",
        )

        # 7) 创建日记
        create_resp = self._request(
            "POST",
            "/api/diary/create",
            expected_status=[201],
            need_auth=True,
            json_data={
                "title": "接口巡检日记",
                "location": "杭州西湖",
                "latitude": 30.242865,
                "longitude": 120.149445,
                "date": "2026-03-25",
                "emotion": "开心",
                "content": "今天接口巡检顺利进行，记录一次完整流程。",
                "images": ["https://example.com/a.jpg"],
                "videos": [
                    {
                        "url": "https://example.com/a.mp4",
                        "thumbnail": "https://example.com/a.png",
                    }
                ],
            },
            name="创建日记",
        )
        if create_resp is not None:
            try:
                self.diary_id = create_resp.json().get("diary_id")
            except Exception:
                self.diary_id = None

        # 8) 日记列表
        self._request(
            "GET",
            "/api/diary/list",
            expected_status=[200],
            need_auth=True,
            name="获取日记列表",
        )

        # 9) 日记详情
        if self.diary_id:
            self._request(
                "GET",
                f"/api/diary/detail/{self.diary_id}",
                expected_status=[200],
                need_auth=True,
                name="获取日记详情",
            )

            # 10) 更新日记
            self._request(
                "PUT",
                f"/api/diary/update/{self.diary_id}",
                expected_status=[200],
                need_auth=True,
                json_data={
                    "title": "接口巡检日记（更新）",
                    "location": "上海外滩",
                    "latitude": 31.2400,
                    "longitude": 121.4900,
                    "date": "2026-03-26",
                    "emotion": "兴奋",
                    "content": "更新后的内容，用于验证 update 接口。",
                    "images": ["https://example.com/b.jpg"],
                    "videos": [],
                },
                name="更新日记",
            )

            # 11) 生成分享链接
            share_resp = self._request(
                "POST",
                "/api/share/generate",
                expected_status=[200],
                need_auth=True,
                json_data={"diary_id": self.diary_id},
                name="生成分享链接",
            )
            if share_resp is not None:
                try:
                    self.share_link = share_resp.json().get("share_link")
                except Exception:
                    self.share_link = None

        # 12) 地图相关
        self._request(
            "GET",
            "/api/map/trajectory",
            expected_status=[200],
            need_auth=True,
            name="地图轨迹",
        )
        self._request(
            "GET",
            "/api/map/stats",
            expected_status=[200],
            need_auth=True,
            name="地图统计",
        )
        self._request(
            "GET",
            "/api/map/detail",
            expected_status=[200],
            need_auth=True,
            name="地图详情",
        )

        # 13) 分享访问
        if self.share_link:
            token = self.share_link.rstrip("/").split("/")[-1]
            self._request(
                "GET",
                f"/api/share/{token}",
                expected_status=[200],
                name="访问分享页",
            )

        # 14) AI 分析
        self._request(
            "POST",
            "/api/ai/analysis",
            expected_status=[200],
            need_auth=True,
            json_data={"content": "今天在西湖散步，心情非常开心，也吃了很多美食。"},
            name="AI 日记分析",
        )

        # 15) 文件上传
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
            tmp.write("api probe upload test")
            tmp_path = tmp.name

        try:
            with open(tmp_path, "rb") as f:
                self._request(
                    "POST",
                    "/api/file/upload",
                    expected_status=[200],
                    need_auth=True,
                    files={"file": ("probe.txt", f, "text/plain")},
                    name="文件上传",
                )
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        # 16) 删除日记
        if self.diary_id:
            self._request(
                "DELETE",
                f"/api/diary/delete/{self.diary_id}",
                expected_status=[200],
                need_auth=True,
                name="删除日记",
            )

        passed = sum(1 for r in self.results if r["passed"])
        total = len(self.results)
        failed = total - passed

        return {
            "base_url": self.base_url,
            "generated_at": datetime.now().isoformat(),
            "summary": {"total": total, "passed": passed, "failed": failed},
            "results": self.results,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Backend API 巡检脚本")
    parser.add_argument("--base-url", default="http://127.0.0.1:5000", help="后端服务地址")
    parser.add_argument("--timeout", type=int, default=15, help="请求超时（秒）")
    parser.add_argument(
        "--report",
        default="api_probe_report.json",
        help="报告输出路径（JSON）",
    )
    args = parser.parse_args()

    runner = APITestRunner(base_url=args.base_url, timeout=args.timeout)
    report = runner.run()

    with open(args.report, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("=" * 72)
    print(f"API 巡检完成: {report['summary']}")
    print(f"报告文件: {args.report}")
    print("=" * 72)

    for item in report["results"]:
        mark = "PASS" if item["passed"] else "FAIL"
        status = item["status_code"] if item["status_code"] is not None else "-"
        print(f"[{mark}] {item['name']} | status={status} | expected={item['expected']}")
        if not item["passed"]:
            if item["error"]:
                print(f"  error: {item['error']}")
            if item["response"] is not None:
                print(f"  response: {item['response']}")

    if report["summary"]["failed"] > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

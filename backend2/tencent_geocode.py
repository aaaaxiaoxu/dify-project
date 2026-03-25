"""腾讯地图 WebService：正向地理编码（地址 → 经纬度）。"""
from __future__ import annotations

import requests


def forward_geocode_address(
    address: str,
    api_key: str,
    region: str | None = None,
    timeout: float = 8,
) -> dict | None:
    """
    返回 {"latitude": float, "longitude": float, "formatted": str|None}，失败返回 None。
    """
    text = (address or "").strip()
    if not text or not api_key:
        return None

    params = {"address": text, "key": api_key}
    r = (region or "").strip()
    if r:
        params["region"] = r

    try:
        resp = requests.get(
            "https://apis.map.qq.com/ws/geocoder/v1/",
            params=params,
            timeout=timeout,
        )
        if resp.status_code != 200:
            return None
        payload = resp.json()
        if payload.get("status") != 0:
            return None
        result = payload.get("result") or {}
        loc = result.get("location") or {}
        try:
            lat = float(loc.get("lat"))
            lng = float(loc.get("lng"))
        except (TypeError, ValueError):
            return None
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            return None
        formatted = (result.get("title") or result.get("address") or "").strip()
        return {
            "latitude": lat,
            "longitude": lng,
            "formatted": formatted or None,
        }
    except Exception:
        return None

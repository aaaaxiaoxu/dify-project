"""地理距离：Haversine 大圆距离与基于日记点的路线里程。"""
from __future__ import annotations

import math
from datetime import date


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """两点间球面大圆距离（千米）。"""
    r_km = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return r_km * c


def route_distance_km_from_diaries(diaries) -> float:
    """
    按日记日期升序（同日按 id），仅使用同时有有效经纬度的点，累加相邻点大圆距离。
    无坐标或单点时返回 0。
    """
    rows: list[tuple] = []
    for d in diaries:
        if d.latitude is None or d.longitude is None:
            continue
        try:
            lat = float(d.latitude)
            lon = float(d.longitude)
        except (TypeError, ValueError):
            continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            continue
        did = getattr(d, "id", 0) or 0
        rows.append((d.date, did, lat, lon))

    rows.sort(key=lambda x: (x[0] or date.min, x[1]))

    total = 0.0
    for i in range(1, len(rows)):
        _, _, lat0, lon0 = rows[i - 1]
        _, _, lat1, lon1 = rows[i]
        total += haversine_km(lat0, lon0, lat1, lon1)

    return round(total, 1)


def unique_location_strings(diaries) -> list[str]:
    """去重后的地点名称列表（strip，保序）。"""
    seen: set[str] = set()
    out: list[str] = []
    for d in diaries:
        if not d.location:
            continue
        s = str(d.location).strip()
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def unique_travel_day_count(diaries) -> int:
    """有日记的不同旅行日期数。"""
    return len({d.date for d in diaries if getattr(d, "date", None) is not None})

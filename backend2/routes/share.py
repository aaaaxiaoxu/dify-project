from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.orm import selectinload
import uuid
from datetime import datetime, timedelta
from markupsafe import escape

import pytz

from extensions import db
from models import Diary, ShareLink, ShareLog

share_bp = Blueprint('share', __name__)

TZ = pytz.timezone('Asia/Shanghai')


def _now():
    return datetime.now(TZ).replace(tzinfo=None)


# ---------- 生成分享链接 ----------
@share_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_share():
    current_user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    diary_id = data.get('diary_id')
    if not diary_id:
        return jsonify({"msg": "diary_id 不能为空"}), 400

    diary = Diary.query.filter_by(id=diary_id, user_id=current_user_id).first()
    if diary is None:
        return jsonify({"msg": "日记不存在"}), 404
    if diary.is_draft:
        return jsonify({"msg": "草稿暂不支持分享，请先发布"}), 400

    # 解析前端传入的可选参数
    expire_days = data.get('expire_days')          # 7 / 30 / None(永久)
    view_password = data.get('view_password')       # 字符串或空
    view_limit = data.get('view_limit')             # 整数或空

    expire_time = None
    if expire_days:
        expire_time = _now() + timedelta(days=int(expire_days))

    share_token = str(uuid.uuid4())

    link = ShareLink(
        token=share_token,
        diary_id=diary_id,
        user_id=current_user_id,
        view_password=view_password or None,
        expire_time=expire_time,
        view_limit=int(view_limit) if view_limit else None,
    )
    db.session.add(link)
    db.session.commit()

    return jsonify({
        "share_token": share_token,
        "expire_time": expire_time.isoformat() if expire_time else None,
        "has_password": bool(view_password),
        "view_limit": link.view_limit,
        "msg": "分享链接生成成功"
    }), 200


# ---------- 访问分享链接 ----------
@share_bp.route('/<token>', methods=['GET', 'POST'])
def get_share(token):
    link = ShareLink.query.filter_by(token=token).first()
    if link is None:
        return jsonify({"msg": "分享链接不存在"}), 404

    # 1) 是否被撤销
    if not link.is_active:
        return jsonify({"msg": "该分享链接已被撤销"}), 403

    # 2) 是否已过期
    if link.expire_time and _now() > link.expire_time:
        return jsonify({"msg": "分享链接已过期"}), 403

    # 3) 访问次数是否超限
    if link.view_limit is not None and link.view_count >= link.view_limit:
        return jsonify({"msg": "该分享链接的访问次数已达上限"}), 403

    # 4) 密码校验（POST 方式传入 password）
    if link.view_password:
        pwd = None
        if request.method == 'POST':
            body = request.get_json() or {}
            pwd = body.get('password')
        else:
            pwd = request.args.get('password')

        if not pwd:
            return jsonify({"msg": "该分享需要密码", "need_password": True}), 401
        if pwd != link.view_password:
            return jsonify({"msg": "密码错误", "need_password": True}), 401

    # 校验通过 —— 记录访问日志 & 计数
    link.view_count += 1
    log = ShareLog(
        share_link_id=link.id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')[:500],
    )
    db.session.add(log)
    db.session.commit()

    # 查询日记
    diary = (
        Diary.query.options(
            selectinload(Diary.images),
            selectinload(Diary.videos),
        )
        .filter_by(id=link.diary_id)
        .first()
    )
    if diary is None or diary.is_draft:
        return jsonify({"msg": "分享内容不存在"}), 404

    return jsonify({
        "title": diary.title,
        "location": diary.location,
        "date": diary.date.isoformat() if diary.date else None,
        "emotion": diary.emotion,
        "content": diary.content,
        "images": [img.image_url for img in diary.images],
        "videos": [{"url": v.video_url, "thumbnail": v.thumbnail_url} for v in diary.videos],
        "created_at": diary.created_at.isoformat() if diary.created_at else None,
    }), 200


# ---------- 我的分享列表 ----------
@share_bp.route('/list', methods=['GET'])
@jwt_required()
def share_list():
    current_user_id = int(get_jwt_identity())
    links = (
        ShareLink.query
        .filter_by(user_id=current_user_id)
        .order_by(ShareLink.created_at.desc())
        .all()
    )

    result = []
    for lk in links:
        diary = Diary.query.filter_by(id=lk.diary_id).first()
        now = _now()
        expired = bool(lk.expire_time and now > lk.expire_time)
        limit_reached = bool(lk.view_limit is not None and lk.view_count >= lk.view_limit)

        if not lk.is_active:
            status = 'revoked'
        elif expired:
            status = 'expired'
        elif limit_reached:
            status = 'limit_reached'
        else:
            status = 'active'

        result.append({
            "id": lk.id,
            "token": lk.token,
            "diary_id": lk.diary_id,
            "diary_title": diary.title if diary else "已删除的日记",
            "has_password": bool(lk.view_password),
            "expire_time": lk.expire_time.isoformat() if lk.expire_time else None,
            "view_limit": lk.view_limit,
            "view_count": lk.view_count,
            "status": status,
            "created_at": lk.created_at.isoformat() if lk.created_at else None,
        })

    return jsonify(result), 200


# ---------- 某篇日记的分享链接 ----------
@share_bp.route('/diary/<int:diary_id>', methods=['GET'])
@jwt_required()
def share_by_diary(diary_id):
    current_user_id = int(get_jwt_identity())
    links = (
        ShareLink.query
        .filter_by(diary_id=diary_id, user_id=current_user_id)
        .order_by(ShareLink.created_at.desc())
        .all()
    )

    now = _now()
    result = []
    for lk in links:
        expired = bool(lk.expire_time and now > lk.expire_time)
        limit_reached = bool(lk.view_limit is not None and lk.view_count >= lk.view_limit)

        if not lk.is_active:
            status = 'revoked'
        elif expired:
            status = 'expired'
        elif limit_reached:
            status = 'limit_reached'
        else:
            status = 'active'

        result.append({
            "id": lk.id,
            "token": lk.token,
            "has_password": bool(lk.view_password),
            "expire_time": lk.expire_time.isoformat() if lk.expire_time else None,
            "view_limit": lk.view_limit,
            "view_count": lk.view_count,
            "status": status,
            "created_at": lk.created_at.isoformat() if lk.created_at else None,
        })

    return jsonify(result), 200
@share_bp.route('/revoke/<int:share_id>', methods=['POST'])
@jwt_required()
def revoke_share(share_id):
    current_user_id = int(get_jwt_identity())
    link = ShareLink.query.filter_by(id=share_id, user_id=current_user_id).first()
    if link is None:
        return jsonify({"msg": "分享链接不存在"}), 404

    link.is_active = False
    db.session.commit()
    return jsonify({"msg": "已撤销分享"}), 200


# ---------- 删除分享链接 ----------
@share_bp.route('/delete/<int:share_id>', methods=['POST'])
@jwt_required()
def delete_share(share_id):
    current_user_id = int(get_jwt_identity())
    link = ShareLink.query.filter_by(id=share_id, user_id=current_user_id).first()
    if link is None:
        return jsonify({"msg": "分享链接不存在"}), 404

    db.session.delete(link)
    db.session.commit()
    return jsonify({"msg": "已删除分享链接"}), 200


# ---------- 单条分享的访问统计 ----------
@share_bp.route('/stats/<int:share_id>', methods=['GET'])
@jwt_required()
def share_stats(share_id):
    current_user_id = int(get_jwt_identity())
    link = ShareLink.query.filter_by(id=share_id, user_id=current_user_id).first()
    if link is None:
        return jsonify({"msg": "分享链接不存在"}), 404

    logs = (
        ShareLog.query
        .filter_by(share_link_id=link.id)
        .order_by(ShareLog.accessed_at.desc())
        .limit(100)
        .all()
    )

    # 按天聚合访问量（最近 7 天）
    from collections import defaultdict
    daily = defaultdict(int)
    for lg in logs:
        day_key = lg.accessed_at.strftime('%m-%d') if lg.accessed_at else 'unknown'
        daily[day_key] += 1

    return jsonify({
        "total_views": link.view_count,
        "daily_views": [{"date": k, "count": v} for k, v in sorted(daily.items())],
        "recent_logs": [
            {
                "ip": lg.ip_address,
                "ua": lg.user_agent,
                "time": lg.accessed_at.isoformat() if lg.accessed_at else None,
            }
            for lg in logs[:20]
        ],
    }), 200


# ============================================================
#  H5 分享页 —— 浏览器直接打开即可看到日记
# ============================================================

_EMOTION_EMOJI = {
    '开心': '😊', '感动': '😢', '兴奋': '🤩',
    '平静': '😌', '忧郁': '😔', '思念': '🥺',
}

_EMOTION_COLOR = {
    '开心': '#FF8C00', '感动': '#9370DB', '兴奋': '#FF69B4',
    '平静': '#20B2AA', '忧郁': '#696969', '思念': '#8B008B',
}


def _error_page(msg):
    html = _PAGE_SHELL.replace('{{BODY}}', f'''
        <div class="error-card">
            <div class="error-icon">😕</div>
            <div class="error-msg">{escape(msg)}</div>
        </div>
    ''')
    return make_response(html, 200)


def _password_page(token, error_msg=''):
    err_html = f'<div class="pwd-error">{escape(error_msg)}</div>' if error_msg else ''
    body = f'''
        <div class="pwd-card">
            <div class="pwd-icon">🔒</div>
            <div class="pwd-title">该分享内容需要密码访问</div>
            {err_html}
            <form method="POST" action="/api/share/page/{escape(token)}">
                <input class="pwd-input" type="password" name="password"
                       placeholder="请输入访问密码" autofocus required />
                <button class="pwd-btn" type="submit">确认访问</button>
            </form>
        </div>
    '''
    html = _PAGE_SHELL.replace('{{BODY}}', body)
    return make_response(html, 200)


def _diary_page(diary):
    emotion = diary.emotion or ''
    emoji = _EMOTION_EMOJI.get(emotion, emotion)
    color = _EMOTION_COLOR.get(emotion, '#007AFF')
    date_str = diary.date.strftime('%Y年%m月%d日') if diary.date else ''

    # 图片 HTML
    images_html = ''
    if diary.images:
        imgs = ''.join(
            f'<img class="gallery-img" src="{escape(img.image_url)}" />'
            for img in diary.images
        )
        images_html = f'<div class="gallery">{imgs}</div>'

    # 视频 HTML
    videos_html = ''
    if diary.videos:
        vids = ''.join(
            f'<video class="diary-video" controls poster="{escape(v.thumbnail_url or "")}">'
            f'<source src="{escape(v.video_url)}" /></video>'
            for v in diary.videos
        )
        videos_html = f'<div class="videos">{vids}</div>'

    body = f'''
        <div class="diary-card">
            <h1 class="diary-title">{escape(diary.title)}</h1>
            <div class="diary-meta">
                <span class="meta-date">📅 {escape(date_str)}</span>
                <span class="meta-loc">📍 {escape(diary.location or '')}</span>
                <span class="meta-emotion" style="color:{color}">{emoji} {escape(emotion)}</span>
            </div>
            {images_html}
            {videos_html}
            <div class="diary-content">{diary.content or ''}</div>
            <div class="diary-footer">来自「智能旅行日记」的分享</div>
        </div>
    '''
    html = _PAGE_SHELL.replace('{{BODY}}', body)
    return make_response(html, 200)


@share_bp.route('/page/<token>', methods=['GET', 'POST'])
def share_page(token):
    """浏览器可直接访问的 H5 分享页"""
    link = ShareLink.query.filter_by(token=token).first()
    if link is None:
        return _error_page('分享链接不存在')

    if not link.is_active:
        return _error_page('该分享链接已被撤销')

    if link.expire_time and _now() > link.expire_time:
        return _error_page('分享链接已过期')

    if link.view_limit is not None and link.view_count >= link.view_limit:
        return _error_page('该分享链接的访问次数已达上限')

    # 密码校验
    if link.view_password:
        if request.method == 'GET':
            return _password_page(token)
        # POST —— 表单提交密码
        pwd = request.form.get('password', '')
        if pwd != link.view_password:
            return _password_page(token, '密码错误，请重新输入')

    # 校验通过 —— 记录日志
    link.view_count += 1
    log = ShareLog(
        share_link_id=link.id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')[:500],
    )
    db.session.add(log)
    db.session.commit()

    diary = (
        Diary.query.options(
            selectinload(Diary.images),
            selectinload(Diary.videos),
        )
        .filter_by(id=link.diary_id)
        .first()
    )
    if diary is None or diary.is_draft:
        return _error_page('分享内容不存在')

    return _diary_page(diary)


# ---------- HTML 页面外壳 ----------
_PAGE_SHELL = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"/>
<title>旅行日记分享</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB",
              "Microsoft YaHei",sans-serif;
  background:linear-gradient(135deg,#f5f7fa 0%,#e4edf9 100%);
  min-height:100vh;
  padding:24px 16px 40px;
  color:#333;
}

/* 日记卡片 */
.diary-card{
  max-width:640px;margin:0 auto;
  background:#fff;border-radius:16px;
  padding:32px 24px;
  box-shadow:0 8px 30px rgba(0,0,0,.08);
}
.diary-title{
  font-size:24px;font-weight:700;margin-bottom:12px;line-height:1.4;
}
.diary-meta{
  display:flex;flex-wrap:wrap;gap:12px;
  font-size:14px;color:#888;margin-bottom:20px;
}
.meta-emotion{font-weight:600}

/* 图片画廊 */
.gallery{
  display:flex;flex-direction:column;gap:12px;margin-bottom:20px;
}
.gallery-img{
  width:100%;height:auto;
  border-radius:10px;cursor:pointer;
  transition:transform .2s;
}
.gallery-img:hover{transform:scale(1.02)}

/* 视频 */
.videos{margin-bottom:20px}
.diary-video{
  width:100%;border-radius:10px;margin-bottom:8px;
  background:#000;
}

/* 正文 */
.diary-content{
  font-size:16px;line-height:1.8;color:#444;
  word-break:break-word;
}
.diary-content img{max-width:100%;border-radius:8px;margin:8px 0}

.diary-footer{
  margin-top:32px;padding-top:16px;
  border-top:1px solid #f0f0f0;
  font-size:12px;color:#bbb;text-align:center;
}

/* 密码页 */
.pwd-card{
  max-width:400px;margin:80px auto 0;
  background:#fff;border-radius:16px;
  padding:40px 28px;text-align:center;
  box-shadow:0 8px 30px rgba(0,0,0,.08);
}
.pwd-icon{font-size:48px;margin-bottom:16px}
.pwd-title{font-size:18px;font-weight:600;margin-bottom:24px;color:#333}
.pwd-input{
  width:100%;height:44px;border:2px solid #e5e5e5;border-radius:10px;
  padding:0 14px;font-size:16px;text-align:center;
  outline:none;transition:border .2s;
}
.pwd-input:focus{border-color:#007AFF}
.pwd-btn{
  width:100%;height:44px;margin-top:16px;
  background:linear-gradient(135deg,#007AFF,#00d4ff);
  color:#fff;border:none;border-radius:10px;
  font-size:16px;font-weight:600;cursor:pointer;
  transition:opacity .2s;
}
.pwd-btn:hover{opacity:.9}
.pwd-error{
  color:#e53935;font-size:14px;margin-bottom:16px;
}

/* 错误页 */
.error-card{
  max-width:400px;margin:80px auto 0;
  background:#fff;border-radius:16px;
  padding:40px 28px;text-align:center;
  box-shadow:0 8px 30px rgba(0,0,0,.08);
}
.error-icon{font-size:48px;margin-bottom:16px}
.error-msg{font-size:16px;color:#999;line-height:1.6}
</style>
</head>
<body>
{{BODY}}
</body>
</html>'''

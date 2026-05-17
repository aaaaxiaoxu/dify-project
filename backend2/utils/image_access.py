from datetime import datetime

import pytz

from extensions import db
from models import Diary, DiaryImage, ImageAccessLog, ShareLink
from services.cos_storage import cos_storage_service


TZ = pytz.timezone('Asia/Shanghai')


def _now():
    return datetime.now(TZ).replace(tzinfo=None)


def _client_ip(request_obj):
    if request_obj is None:
        return None
    forwarded = request_obj.headers.get('X-Forwarded-For', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request_obj.remote_addr


def _user_agent(request_obj):
    if request_obj is None:
        return None
    return (request_obj.headers.get('User-Agent') or '')[:500]


def _coerce_int(value):
    if value in (None, ''):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _find_image(diary_id=None, image_id=None, image_url=None):
    query = DiaryImage.query
    image_id = _coerce_int(image_id)
    diary_id = _coerce_int(diary_id)

    if image_id is not None:
        query = query.filter(DiaryImage.id == image_id)
    if diary_id is not None:
        query = query.filter(DiaryImage.diary_id == diary_id)
    if image_url:
        query = query.filter(DiaryImage.image_url == image_url)
    return query.first()


def can_access_diary_image(user_id, diary_id=None, image_id=None, image_url=None):
    user_id = _coerce_int(user_id)
    if user_id is None:
        return False, '缺少用户身份', None

    image = _find_image(diary_id=diary_id, image_id=image_id, image_url=image_url)
    if image is None:
        return False, '图片不存在', None

    diary = Diary.query.filter_by(id=image.diary_id).first()
    if diary is None:
        return False, '日记不存在', image
    if int(diary.user_id) != user_id:
        return False, '无权访问该图片', image

    return True, '用户为日记作者', image


def validate_share_token(share_token, password=None):
    token = str(share_token or '').strip()
    if not token:
        return False, '缺少分享令牌', None

    link = ShareLink.query.filter_by(token=token).first()
    if link is None:
        return False, '分享链接不存在', None
    if not link.is_active:
        return False, '分享链接已撤销', link
    if link.expire_time and _now() > link.expire_time:
        return False, '分享链接已过期', link
    if link.view_limit is not None and link.view_count >= link.view_limit:
        return False, '分享访问次数已达上限', link
    if link.view_password and password != link.view_password:
        return False, '分享密码错误', link
    return True, '分享链接有效', link


def _record_image_access(
    user_id,
    diary_id,
    image_id,
    share_link_id,
    image_url,
    access_type,
    decision,
    reason,
    request_obj=None,
    commit=True,
):
    log = ImageAccessLog(
        user_id=_coerce_int(user_id),
        diary_id=_coerce_int(diary_id),
        image_id=_coerce_int(image_id),
        share_link_id=_coerce_int(share_link_id),
        image_url=str(image_url or ''),
        access_type=access_type,
        decision=decision,
        reason=reason,
        ip_address=_client_ip(request_obj),
        user_agent=_user_agent(request_obj),
    )
    db.session.add(log)
    if commit:
        db.session.commit()
    return log


def get_authorized_cos_url(
    user_id=None,
    diary_id=None,
    image_id=None,
    image_url=None,
    access_type='report_pdf',
    share_token=None,
    share_password=None,
    request_obj=None,
    expires=300,
):
    share_link = None
    if share_token:
        share_ok, share_reason, share_link = validate_share_token(share_token, share_password)
        if not share_ok:
            _record_image_access(
                user_id,
                diary_id,
                image_id,
                share_link.id if share_link else None,
                image_url,
                access_type,
                ImageAccessLog.DECISION_DENIED,
                share_reason,
                request_obj=request_obj,
            )
            return None, share_reason

        image = _find_image(diary_id=share_link.diary_id, image_id=image_id, image_url=image_url)
        if image is None:
            reason = '分享图片不存在'
            _record_image_access(
                user_id,
                share_link.diary_id,
                image_id,
                share_link.id,
                image_url,
                access_type,
                ImageAccessLog.DECISION_DENIED,
                reason,
                request_obj=request_obj,
            )
            return None, reason
        allowed = True
        reason = '分享链接授权访问'
    else:
        allowed, reason, image = can_access_diary_image(
            user_id,
            diary_id=diary_id,
            image_id=image_id,
            image_url=image_url,
        )

    resolved_url = image.image_url if image is not None else image_url
    resolved_diary_id = image.diary_id if image is not None else diary_id
    resolved_image_id = image.id if image is not None else image_id

    if not allowed:
        _record_image_access(
            user_id,
            resolved_diary_id,
            resolved_image_id,
            share_link.id if share_link else None,
            resolved_url,
            access_type,
            ImageAccessLog.DECISION_DENIED,
            reason,
            request_obj=request_obj,
        )
        return None, reason

    try:
        authorized_url = cos_storage_service.get_presigned_download_url(resolved_url, expires=expires)
    except Exception:
        authorized_url = resolved_url

    _record_image_access(
        user_id,
        resolved_diary_id,
        resolved_image_id,
        share_link.id if share_link else None,
        resolved_url,
        access_type,
        ImageAccessLog.DECISION_ALLOWED,
        reason,
        request_obj=request_obj,
    )
    return authorized_url, reason

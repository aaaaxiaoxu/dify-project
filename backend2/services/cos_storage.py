import mimetypes
import os
import uuid

from werkzeug.utils import secure_filename

from config import Config

try:
    from qcloud_cos import CosConfig, CosS3Client
except ImportError:  # pragma: no cover - 依赖未安装时在运行期给出清晰提示
    CosConfig = None
    CosS3Client = None


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".bmp",
    ".heic",
    ".heif",
}
VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".m4v",
    ".avi",
    ".mkv",
    ".webm",
    ".3gp",
}
DEFAULT_EXTENSION_BY_TYPE = {
    "image": ".jpg",
    "video": ".mp4",
}
ALIASED_EXTENSIONS = {
    ".jpe": ".jpg",
}


def normalize_media_type(media_type):
    if not media_type:
        return None
    value = str(media_type).strip().lower()
    if value in {"image", "img", "photo", "picture"}:
        return "image"
    if value in {"video", "vid"}:
        return "video"
    return None


def infer_media_type(filename, mimetype, media_type_hint=None):
    normalized_hint = normalize_media_type(media_type_hint)
    if normalized_hint:
        return normalized_hint

    raw_mimetype = (mimetype or "").strip().lower()
    if raw_mimetype.startswith("image/"):
        return "image"
    if raw_mimetype.startswith("video/"):
        return "video"

    ext = os.path.splitext(secure_filename(filename or "") or "")[1].lower()
    ext = ALIASED_EXTENSIONS.get(ext, ext)
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    raise ValueError("仅支持图片或视频上传")


def _resolve_extension(filename, mimetype, media_type):
    ext = os.path.splitext(secure_filename(filename or "") or "")[1].lower()
    ext = ALIASED_EXTENSIONS.get(ext, ext)
    allowed_extensions = IMAGE_EXTENSIONS if media_type == "image" else VIDEO_EXTENSIONS
    if ext in allowed_extensions:
        return ext

    guessed_ext = mimetypes.guess_extension(mimetype or "") or ""
    guessed_ext = ALIASED_EXTENSIONS.get(guessed_ext.lower(), guessed_ext.lower())
    if guessed_ext in allowed_extensions:
        return guessed_ext

    return DEFAULT_EXTENSION_BY_TYPE[media_type]


def _resolve_content_type(mimetype, extension):
    if mimetype:
        return mimetype
    guessed_mimetype, _ = mimetypes.guess_type(f"file{extension}")
    return guessed_mimetype or "application/octet-stream"


class CosStorageService:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client

        if CosConfig is None or CosS3Client is None:
            raise RuntimeError("缺少 COS SDK，请先安装依赖：pip install -U cos-python-sdk-v5")

        if not Config.COS_SECRET_ID or not Config.COS_SECRET_KEY:
            raise RuntimeError("未配置 COS_SECRET_ID / COS_SECRET_KEY，无法上传到腾讯云 COS")

        cos_config = CosConfig(
            Region=Config.COS_REGION,
            SecretId=Config.COS_SECRET_ID,
            SecretKey=Config.COS_SECRET_KEY,
            Scheme="https",
        )
        self._client = CosS3Client(cos_config)
        return self._client

    def upload_file(self, file_storage, media_type):
        media_type = normalize_media_type(media_type)
        if media_type not in {"image", "video"}:
            raise ValueError("media_type 仅支持 image 或 video")

        client = self._get_client()
        extension = _resolve_extension(file_storage.filename, file_storage.mimetype, media_type)
        key = f"{Config.COS_MEDIA_PREFIX}/{media_type}/{uuid.uuid4().hex}{extension}"
        file_storage.stream.seek(0)
        content_type = _resolve_content_type(file_storage.mimetype, extension)

        client.put_object(
            Bucket=Config.COS_BUCKET,
            Body=file_storage.stream,
            Key=key,
            ContentType=content_type,
        )

        return {
            "url": f"{Config.COS_BASE_URL}/{key}",
            "key": key,
            "media_type": media_type,
        }


cos_storage_service = CosStorageService()

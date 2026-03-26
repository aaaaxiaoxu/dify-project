from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from services.cos_storage import cos_storage_service, infer_media_type

file_bp = Blueprint('file', __name__)

@file_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    if 'file' not in request.files:
        return jsonify({"msg": "没有文件"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"msg": "没有选择文件"}), 400
    
    media_type_hint = (
        request.form.get('media_type')
        or request.form.get('mediaType')
        or request.form.get('type')
    )

    try:
        media_type = infer_media_type(file.filename, file.mimetype, media_type_hint)
        upload_result = cos_storage_service.upload_file(file, media_type)
    except ValueError as exc:
        return jsonify({"msg": str(exc)}), 400
    except RuntimeError as exc:
        return jsonify({"msg": str(exc)}), 500
    except Exception as exc:
        return jsonify({"msg": f"上传到 COS 失败: {exc}"}), 500

    return jsonify(upload_result), 200

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import os
import uuid
from werkzeug.utils import secure_filename
from config import Config

file_bp = Blueprint('file', __name__)

@file_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    if 'file' not in request.files:
        return jsonify({"msg": "没有文件"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"msg": "没有选择文件"}), 400
    
    if file:
        # 保存文件（避免重名覆盖，保留安全扩展名）
        orig = secure_filename(file.filename) or "upload"
        _, ext = os.path.splitext(orig)
        ext = ext.lower() if ext else ""
        if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"):
            ext = ".jpg"
        filename = f"{uuid.uuid4().hex}{ext}"
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # 返回文件URL
        file_url = f"http://localhost:5000/{Config.UPLOAD_FOLDER}/{filename}"
        return jsonify({"url": file_url}), 200
    return jsonify({"msg": "文件上传失败"}), 400
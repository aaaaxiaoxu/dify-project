from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import os
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
        # 保存文件
        filename = file.filename
        file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # 返回文件URL
        file_url = f"http://localhost:5000/{Config.UPLOAD_FOLDER}/{filename}"
        return jsonify({"url": file_url}), 200
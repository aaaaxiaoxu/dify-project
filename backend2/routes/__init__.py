def register_blueprints(app):
    from .user import user_bp
    from .diary import diary_bp
    from .map import map_bp
    from .ai import ai_bp
    from .file import file_bp
    from .share import share_bp
    from .stats import stats_bp
    from .admin import admin_bp
    
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(diary_bp, url_prefix='/api/diary')
    app.register_blueprint(map_bp, url_prefix='/api/map')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(file_bp, url_prefix='/api/file')
    app.register_blueprint(share_bp, url_prefix='/api/share')
    app.register_blueprint(stats_bp, url_prefix='/api/stats')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
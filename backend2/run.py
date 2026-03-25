import os
import sys
# 设置默认编码为utf-8
if sys.version_info[0] == 3:
    import importlib
    importlib.reload(sys)

from app import create_app

# 从环境变量获取配置名称，如果没有则默认为development
config_name = os.environ.get('FLASK_CONFIG', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    # 使用localhost而不是0.0.0.0来避免DNS解析问题
    app.run(debug=True, host='localhost', port=5000)
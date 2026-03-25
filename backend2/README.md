# 智能旅行日记APP后端

## 项目结构

```
backend/
├── app.py              # 应用工厂
├── wsgi.py             # Gunicorn 入口
├── start_gunicorn_dev.sh # Gunicorn 启动脚本
├── config.py           # 配置文件
├── extensions.py       # 扩展初始化
├── init_db.py          # 数据库初始化脚本
├── requirements.txt    # 依赖包
├── models.py           # 数据模型
├── routes/             # 路由蓝图
│   ├── __init__.py     # 蓝图注册
│   ├── user.py         # 用户相关路由
│   ├── diary.py        # 日记相关路由
│   ├── map.py          # 地图相关路由
│   ├── ai.py           # AI分析相关路由
│   ├── file.py         # 文件上传相关路由
│   └── share.py        # 分享相关路由
└── uploads/            # 文件上传目录
```

## 架构说明

### 分层架构
1. **应用层** (`app.py`, `wsgi.py`) - 应用工厂和入口点
2. **配置层** (`config.py`) - 应用配置管理
3. **扩展层** (`extensions.py`) - Flask扩展初始化
4. **路由层** (`routes/`) - API路由和业务逻辑处理
5. **模型层** (`models.py`) - 数据模型定义
6. **数据层** (MySQL数据库) - 数据持久化

### 路由模块
- `user.py` - 用户注册、登录、个人信息管理
- `diary.py` - 日记的增删改查操作
- `map.py` - 地图轨迹相关功能
- `ai.py` - AI分析接口
- `file.py` - 文件上传功能
- `share.py` - 日记分享功能

## 安装和运行

1. 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```

2. 初始化数据库:
   ```bash
   python init_db.py
   ```

3. 启动服务（仅 Gunicorn）:
   ```bash
   ./start_gunicorn_dev.sh
   ```
   默认监听 `8080`，等价于：
   ```bash
   PORT=8080 ./start_gunicorn_dev.sh
   ```
   手动启动命令：
   ```bash
   python3 -m gunicorn --bind 127.0.0.1:8080 --workers 1 --threads 4 --reload wsgi:app
   ```

## API接口

### 用户相关
- `POST /api/user/register` - 用户注册
- `POST /api/user/login` - 用户登录
- `GET /api/user/profile` - 获取用户信息

### 日记相关
- `GET /api/diary/list` - 获取日记列表
- `GET /api/diary/detail/<id>` - 获取日记详情
- `POST /api/diary/create` - 创建日记
- `PUT /api/diary/update/<id>` - 更新日记
- `DELETE /api/diary/delete/<id>` - 删除日记

### 地图相关
- `GET /api/map/trajectory` - 获取旅行轨迹

### AI分析相关
- `POST /api/ai/analysis` - AI分析日记内容

### 文件上传相关
- `POST /api/file/upload` - 上传文件

### 分享相关
- `POST /api/share/generate` - 生成分享链接
- `GET /api/share/<token>` - 访问分享内容
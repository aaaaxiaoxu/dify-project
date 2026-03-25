# 数据库模型定义
# 由于项目要求使用MySQL 8.0数据库，但在当前简化版本中使用内存数据结构模拟

from extensions import db
from datetime import datetime
import pytz

# 定义获取当前北京时间的函数
def get_current_time():
    tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(tz)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='用户ID')
    username = db.Column(db.String(50), nullable=False, unique=True, comment='用户名')
    password = db.Column(db.String(255), nullable=False, comment='密码')
    nickname = db.Column(db.String(100), nullable=False, comment='昵称')
    phone = db.Column(db.String(20), nullable=False, unique=True, comment='手机号')
    created_at = db.Column(db.DateTime, default=get_current_time, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=get_current_time, onupdate=get_current_time, comment='更新时间')
    
    # 关系
    diaries = db.relationship('Diary', backref='user', lazy=True)

class Diary(db.Model):
    __tablename__ = 'diaries'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='日记ID')
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='用户ID')
    title = db.Column(db.String(200), nullable=False, comment='日记标题')
    location = db.Column(db.String(200), nullable=False, comment='地点')
    latitude = db.Column(db.DECIMAL(10, 8), nullable=True, comment='纬度')
    longitude = db.Column(db.DECIMAL(11, 8), nullable=True, comment='经度')
    date = db.Column(db.Date, nullable=False, comment='旅行日期')
    emotion = db.Column(db.String(20), nullable=False, comment='情绪标签')
    content = db.Column(db.Text, nullable=False, comment='日记内容')
    created_at = db.Column(db.DateTime, default=get_current_time, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=get_current_time, onupdate=get_current_time, comment='更新时间')
    
    # 关系
    images = db.relationship('DiaryImage', backref='diary', lazy=True, cascade='all, delete-orphan')
    videos = db.relationship('DiaryVideo', backref='diary', lazy=True, cascade='all, delete-orphan')
    ai_analysis = db.relationship('AIAnalysis', backref='diary', lazy=True, uselist=False, cascade='all, delete-orphan')

class DiaryImage(db.Model):
    __tablename__ = 'diary_images'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='图片ID')
    diary_id = db.Column(db.BigInteger, db.ForeignKey('diaries.id', ondelete='CASCADE'), nullable=False, comment='日记ID')
    image_url = db.Column(db.String(500), nullable=False, comment='图片URL')
    sort_order = db.Column(db.Integer, default=0, nullable=False, comment='排序序号')
    created_at = db.Column(db.DateTime, default=get_current_time, comment='创建时间')

class DiaryVideo(db.Model):
    __tablename__ = 'diary_videos'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='视频ID')
    diary_id = db.Column(db.BigInteger, db.ForeignKey('diaries.id', ondelete='CASCADE'), nullable=False, comment='日记ID')
    video_url = db.Column(db.String(500), nullable=False, comment='视频URL')
    thumbnail_url = db.Column(db.String(500), nullable=True, comment='视频缩略图URL')
    sort_order = db.Column(db.Integer, default=0, nullable=False, comment='排序序号')
    created_at = db.Column(db.DateTime, default=get_current_time, comment='创建时间')

class AIAnalysis(db.Model):
    __tablename__ = 'ai_analysis'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='分析ID')
    diary_id = db.Column(db.BigInteger, db.ForeignKey('diaries.id', ondelete='CASCADE'), nullable=False, unique=True, comment='日记ID')
    emotion_analysis = db.Column(db.Text, nullable=False, comment='情感分析结果')
    keywords = db.Column(db.Text, nullable=False, comment='关键词')
    travel_advice = db.Column(db.Text, nullable=False, comment='旅行建议')
    created_at = db.Column(db.DateTime, default=get_current_time, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=get_current_time, onupdate=get_current_time, comment='更新时间')

class TravelTrajectory(db.Model):
    __tablename__ = 'travel_trajectories'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='轨迹ID')
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='用户ID')
    location = db.Column(db.String(200), nullable=False, comment='地点')
    latitude = db.Column(db.DECIMAL(10, 8), nullable=True, comment='纬度')
    longitude = db.Column(db.DECIMAL(11, 8), nullable=True, comment='经度')
    visit_time = db.Column(db.DateTime, default=get_current_time, comment='访问时间')
    created_at = db.Column(db.DateTime, default=get_current_time, comment='创建时间')

# 数据库操作类
class Database:
    def __init__(self):
        # 在实际应用中，这里应该连接到MySQL数据库
        # 当前使用内存数据结构模拟数据库
        self.users = []
        self.diaries = []
        self.diary_images = []
        self.diary_videos = []
        self.ai_analysis = []
        self.travel_trajectories = []
        self.init_data()
    
    def init_data(self):
      # 初始化示例数据
      user = User(1, "traveler", "123456", "旅行者", "13800138000")
      self.users.append(user)
      
      # 创建日记但暂时不添加图片和视频
      diary1 = Diary(
          1, 1, "西湖一日游", "杭州西湖", 30.24286500, 120.14944500, "2023-05-15", "开心",
          "今天游览了美丽的西湖，看到了断桥残雪。湖水波光粼粼，柳絮飞舞，仿佛置身于诗画之中。在这里感受到了江南水乡的独特韵味，心情格外舒畅。\n\n西湖十景之一的断桥残雪果然名不虚传，站在桥上远眺，整个湖面尽收眼底。远处雷峰塔巍峨耸立，近处游船穿梭其间，构成了一幅生动的画面。\n\n傍晚时分，夕阳西下，湖面泛起金色的涟漪，美得让人窒息。这一刻，所有的烦恼都被抛到了九霄云外，只剩下内心的宁静与满足。",
          [], [], "2023-05-15T20:30:00Z"
      )
      
      diary2 = Diary(
          2, 1, "古城探秘之旅", "丽江古城", 26.87239500, 100.23559700, "2023-04-22", "感动",
          "走在石板路上，仿佛穿越了时空。古城的韵味让人陶醉，每一处风景都值得细细品味。",
          [], [], "2023-04-22T19:15:00Z"
      )
      
      diary3 = Diary(
          3, 1, "海边度假", "三亚亚龙湾", 18.19528500, 109.65798500, "2023-03-10", "兴奋",
          "阳光、沙滩、海浪，一切都那么美好。在这里彻底放松了身心，享受了难得的悠闲时光。",
          [], [], "2023-03-10T18:45:00Z"
      )
      
      self.diaries.append(diary1)
      self.diaries.append(diary2)
      self.diaries.append(diary3)
      
      # 添加示例图片
      image1 = DiaryImage(1, 1, "https://example.com/images/西湖1.jpg", 1, "2023-05-15T20:30:00Z")
      image2 = DiaryImage(2, 1, "https://example.com/images/西湖2.jpg", 2, "2023-05-15T20:30:00Z")
      image3 = DiaryImage(3, 1, "https://example.com/images/西湖3.jpg", 3, "2023-05-15T20:30:00Z")
      self.diary_images.append(image1)
      self.diary_images.append(image2)
      self.diary_images.append(image3)
      
      # 将图片关联到对应的日记
      diary1.images = [image1, image2, image3]
      
      # 添加示例视频
      video1 = DiaryVideo(1, 1, "https://example.com/videos/西湖游记.mp4", "https://example.com/videos/西湖游记_thumb.jpg", 1, "2023-05-15T20:30:00Z")
      video2 = DiaryVideo(2, 3, "https://example.com/videos/海边度假.mp4", "https://example.com/videos/海边度假_thumb.jpg", 1, "2023-03-10T18:45:00Z")
      self.diary_videos.append(video1)
      self.diary_videos.append(video2)
      
      # 将视频关联到对应的日记
      diary1.videos = [video1]
      diary3.videos = [video2]
      
      # 添加示例AI分析
      ai_analysis1 = AIAnalysis(1, 1, "这篇日记表达了作者对西湖美景的喜爱之情，整体情绪非常积极向上。", '["西湖", "断桥残雪", "江南水乡", "诗画", "心情舒畅"]', "根据您对江南水乡的喜爱，推荐您下次可以去苏州园林或乌镇古镇体验类似的江南风情。", "2023-05-15T20:30:00Z", "2023-05-15T20:30:00Z")
      self.ai_analysis.append(ai_analysis1)
      
      # 添加示例轨迹数据
      trajectory1 = TravelTrajectory(1, 1, "杭州西湖", 30.24286500, 120.14944500, "2023-05-15T10:00:00Z", "2023-05-15T10:00:00Z")
      trajectory2 = TravelTrajectory(2, 1, "丽江古城", 26.87239500, 100.23559700, "2023-04-22T14:30:00Z", "2023-04-22T14:30:00Z")
      trajectory3 = TravelTrajectory(3, 1, "三亚亚龙湾", 18.19528500, 109.65798500, "2023-03-10T09:15:00Z", "2023-03-10T09:15:00Z")
      self.travel_trajectories.append(trajectory1)
      self.travel_trajectories.append(trajectory2)
      self.travel_trajectories.append(trajectory3)
    
    # 用户相关操作
    def get_user_by_username(self, username):
        for user in self.users:
            if user.username == username:
                return user
        return None
    
    def get_user_by_id(self, user_id):
        for user in self.users:
            if user.id == user_id:
                return user
        return None
    
    def create_user(self, username, password, nickname, phone):
        user_id = len(self.users) + 1
        user = User(user_id, username, password, nickname, phone)
        self.users.append(user)
        return user
    
    # 日记相关操作
    def get_diaries_by_user_id(self, user_id):
        return [diary for diary in self.diaries if diary.user_id == user_id]
    
    def get_diary_by_id(self, diary_id):
        for diary in self.diaries:
            if diary.id == diary_id:
                return diary
        return None
    
    def create_diary(self, user_id, title, location, latitude, longitude, date, emotion, content, images, videos):
        diary_id = len(self.diaries) + 1
        # 在实际应用中应该使用当前时间
        diary = Diary(diary_id, user_id, title, location, latitude, longitude, date, emotion, content, images, videos, "2023-05-20T10:00:00Z")
        self.diaries.append(diary)
        return diary
    
    def update_diary(self, diary_id, title, location, latitude, longitude, date, emotion, content, images, videos):
        diary = self.get_diary_by_id(diary_id)
        if diary:
            diary.title = title
            diary.location = location
            diary.latitude = latitude
            diary.longitude = longitude
            diary.date = date
            diary.emotion = emotion
            diary.content = content
            if images is not None:
                diary.images = images
            if videos is not None:
                diary.videos = videos
        return diary
    
    def delete_diary(self, diary_id):
        diary = self.get_diary_by_id(diary_id)
        if diary:
            self.diaries.remove(diary)
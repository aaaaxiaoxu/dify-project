import pymysql
from app import create_app
from extensions import db
from models import User, Diary, DiaryImage, DiaryVideo, AIAnalysis, TravelTrajectory

def init_database():
    app = create_app()
    
    with app.app_context():
        # 删除所有表
        db.drop_all()
        
        # 创建所有表
        db.create_all()
        
        # 创建示例用户
        user = User(
            username="admin",
            password="123456",
            nickname="旅行者",
            phone="13800138000"
        )
        db.session.add(user)
        db.session.commit()
        
        # 创建示例日记
        diary1 = Diary(
            user_id=user.id,
            title="西湖一日游",
            location="杭州西湖",
            latitude=30.24286500,
            longitude=120.14944500,
            date="2023-05-15",
            emotion="开心",
            content="今天游览了美丽的西湖，看到了断桥残雪。湖水波光粼粼，柳絮飞舞，仿佛置身于诗画之中。在这里感受到了江南水乡的独特韵味，心情格外舒畅。"
        )
        
        diary2 = Diary(
            user_id=user.id,
            title="古城探秘之旅",
            location="丽江古城",
            latitude=26.87239500,
            longitude=100.23559700,
            date="2023-04-22",
            emotion="感动",
            content="走在石板路上，仿佛穿越了时空。古城的韵味让人陶醉，每一处风景都值得细细品味。"
        )
        
        diary3 = Diary(
            user_id=user.id,
            title="海边度假",
            location="三亚亚龙湾",
            latitude=18.19528500,
            longitude=109.65798500,
            date="2023-03-10",
            emotion="兴奋",
            content="阳光、沙滩、海浪，一切都那么美好。在这里彻底放松了身心，享受了难得的悠闲时光。"
        )
        
        db.session.add(diary1)
        db.session.add(diary2)
        db.session.add(diary3)
        db.session.commit()
        
        print("数据库初始化完成，示例数据已创建")

if __name__ == '__main__':
    init_database()
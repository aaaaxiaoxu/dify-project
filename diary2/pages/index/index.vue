<template>
  <view class="container">
    <view class="header">
      <text class="title">智能旅行日记</text>
      <text class="subtitle">记录每一次美好旅程</text>
    </view>
    
    <view class="stats-card">
      <view class="stat-item" @click="goToDiaryList">
        <text class="stat-number">{{ diaryCount }}</text>
        <text class="stat-label">篇日记</text>
      </view>
      <view class="stat-item" @click="goToMap">
        <text class="stat-number">{{ cityCount }}</text>
        <text class="stat-label">个城市</text>
      </view>
      <view class="stat-item" @click="goToMap">
        <text class="stat-number">{{ kmCount }}</text>
        <text class="stat-label">公里</text>
      </view>
    </view>
    
    <view class="action-buttons">
      <button class="primary-btn" @click="goToWriteDiary">
        <text class="btn-icon">📝</text>
        <text>写日记</text>
      </button>
      <button class="secondary-btn" @click="goToMap">
        <text class="btn-icon">🗺️</text>
        <text>查看足迹</text>
      </button>
    </view>
    
    <view class="recent-diaries">
      <view class="section-title">
        <text>最近日记</text>
        <text class="more" @click="goToDiaryList">更多 ></text>
      </view>
      
      <view v-if="recentDiaries.length === 0" class="empty-state">
        <text class="empty-icon">📖</text>
        <text>暂无日记，快来记录你的第一次旅行吧！</text>
      </view>
      
      <view v-else class="diary-list">
        <view 
          v-for="diary in recentDiaries" 
          :key="diary.id" 
          class="diary-item"
          @click="goToDiaryDetail(diary.id)"
        >
          <view class="diary-image" v-if="diary.coverImage">
            <image :src="diary.coverImage" mode="aspectFill" class="diary-image-content"></image>
          </view>
          <view class="diary-image-placeholder" v-else>
            <text class="image-icon">🌄</text>
          </view>
          <view class="diary-content">
            <text class="diary-title">{{ diary.title }}</text>
            <text class="diary-location">📍 {{ diary.location }}</text>
            <text class="diary-date">{{ formatDate(diary.date) }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import request from '../../utils/request.js'
import config from '../../api/config.js'

export default {
  data() {
    return {
      diaryCount: 0,
      cityCount: 0,
      kmCount: 0,
      recentDiaries: []
    }
  },
  
  onLoad() {
    console.log('Index page loaded')
    // 页面加载时获取真实数据
    this.loadData()
  },
  
  onShow() {
    // 页面每次显示时重新加载数据
    this.loadData()
  },
  
  methods: {
    loadData() {
      // 获取日记统计数据
      this.loadDiaryStats()
      // 获取地图统计数据
      this.loadMapStats()
      // 获取最近日记
      this.loadRecentDiaries()
    },
    
    loadDiaryStats() {
      const token = this.$store.state.token
      if (!token) {
        console.log('用户未登录')
        return
      }
      
      // 调用后端获取日记列表接口来统计日记数量
      request({
        url: config.DIARY_LIST,
        method: 'GET',
        header: {
          'Authorization': 'Bearer ' + token
        }
      }).then(res => {
        this.diaryCount = res.length
      }).catch(err => {
        console.error('获取日记统计数据失败:', err)
      })
    },
    
    loadMapStats() {
      const token = this.$store.state.token
      if (!token) {
        console.log('用户未登录')
        // 使用默认值
        this.cityCount = 8
        this.kmCount = 2450
        return
      }
      
      // 调用后端获取地图统计数据
      request({
        url: config.MAP_STATS,
        method: 'GET',
        header: {
          'Authorization': 'Bearer ' + token
        }
      }).then(res => {
        this.cityCount = res.city_count
        this.kmCount = res.km_count
      }).catch(err => {
        console.error('获取地图统计数据失败:', err)
        // 出错时使用默认值
        this.cityCount = 8
        this.kmCount = 2450
      })
    },
    
    loadRecentDiaries() {
      const token = this.$store.state.token
      if (!token) {
        console.log('用户未登录')
        // 使用模拟数据
        this.recentDiaries = [
          {
            id: 1,
            title: '西湖一日游',
            location: '杭州西湖',
            date: '2023-05-15',
            coverImage: ''
          },
          {
            id: 2,
            title: '古城探秘之旅',
            location: '丽江古城',
            date: '2023-04-22',
            coverImage: ''
          },
          {
            id: 3,
            title: '海边度假',
            location: '三亚亚龙湾',
            date: '2023-03-10',
            coverImage: ''
          }
        ]
        return
      }
      
      // 调用后端获取日记列表接口
      request({
        url: config.DIARY_LIST,
        method: 'GET',
        header: {
          'Authorization': 'Bearer ' + token
        }
      }).then(res => {
        // 取最近3篇日记
        this.recentDiaries = res.slice(0, 3).map(diary => ({
          id: diary.id,
          title: diary.title,
          location: diary.location,
          date: diary.date,
          coverImage: diary.images && diary.images.length > 0 ? diary.images[0] : ''
        }))
      }).catch(err => {
        console.error('获取最近日记失败:', err)
        // 出错时使用模拟数据
        this.recentDiaries = [
          {
            id: 1,
            title: '西湖一日游',
            location: '杭州西湖',
            date: '2023-05-15',
            coverImage: ''
          },
          {
            id: 2,
            title: '古城探秘之旅',
            location: '丽江古城',
            date: '2023-04-22',
            coverImage: ''
          },
          {
            id: 3,
            title: '海边度假',
            location: '三亚亚龙湾',
            date: '2023-03-10',
            coverImage: ''
          }
        ]
      })
    },
    
    goToWriteDiary() {
      uni.navigateTo({
        url: '/pages/diary/edit'
      })
    },
    
    goToMap() {
      uni.switchTab({
        url: '/pages/map/map'
      })
    },
    
    goToDiaryList() {
      uni.switchTab({
        url: '/pages/diary/list'
      })
    },
    
    goToDiaryDetail(id) {
      uni.navigateTo({
        url: `/pages/diary/detail?id=${id}`
      })
    },
    
    formatDate(dateString) {
      const date = new Date(dateString)
      return `${date.getMonth() + 1}月${date.getDate()}日`
    }
  }
}
</script>

<style scoped>
.container {
  padding: 30rpx;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4edf9 100%);
  min-height: 100vh;
}

.header {
  text-align: center;
  margin-bottom: 50rpx;
  padding-top: 30rpx;
}

.title {
  font-size: 48rpx;
  font-weight: bold;
  color: #333;
  display: block;
  margin-bottom: 10rpx;
  text-shadow: 1rpx 1rpx 2rpx rgba(0,0,0,0.1);
}

.subtitle {
  font-size: 28rpx;
  color: #666;
  font-weight: 300;
}

.stats-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 20rpx;
  padding: 40rpx 0;
  display: flex;
  justify-content: space-around;
  margin-bottom: 50rpx;
  box-shadow: 0 10rpx 30rpx rgba(0,0,0,0.15);
  animation: fadeInUp 0.6s ease-out;
}

.stat-item {
  text-align: center;
}

.stat-item:active {
  opacity: 0.8;
}

.stat-number {
  display: block;
  font-size: 48rpx;
  font-weight: bold;
  color: #fff;
  margin-bottom: 10rpx;
}

.stat-label {
  font-size: 24rpx;
  color: rgba(255,255,255,0.8);
}

.action-buttons {
  display: flex;
  justify-content: space-between;
  margin-bottom: 50rpx;
  gap: 30rpx;
}

.primary-btn, .secondary-btn {
  flex: 1;
  border: none;
  border-radius: 15rpx;
  padding: 30rpx;
  font-size: 32rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.1);
  transition: all 0.3s ease;
}

.primary-btn {
  background: linear-gradient(135deg, #007AFF 0%, #00d4ff 100%);
  color: white;
}

.secondary-btn {
  background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
  color: white;
}

.primary-btn:hover, .secondary-btn:hover {
  transform: translateY(-5rpx);
  box-shadow: 0 8rpx 25rpx rgba(0,0,0,0.2);
}

.btn-icon {
  font-size: 50rpx;
  margin-bottom: 10rpx;
}

.section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30rpx;
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
}

.more {
  font-size: 28rpx;
  color: #007AFF;
  font-weight: normal;
}

.empty-state {
  text-align: center;
  padding: 100rpx 0;
  color: #999;
}

.empty-icon {
  font-size: 100rpx;
  margin-bottom: 30rpx;
  display: block;
}

.diary-list {
  display: flex;
  flex-direction: column;
  gap: 30rpx;
}

.diary-item {
  background: #fff;
  border-radius: 20rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.05);
  display: flex;
  transition: all 0.3s ease;
  animation: fadeInUp 0.6s ease-out;
}

.diary-item:hover {
  transform: translateY(-5rpx);
  box-shadow: 0 8rpx 25rpx rgba(0,0,0,0.1);
}

.diary-image {
  width: 200rpx;
  height: 200rpx;
}

.diary-image-content {
  width: 100%;
  height: 100%;
}

.diary-image-placeholder {
  width: 200rpx;
  height: 200rpx;
  background: linear-gradient(135deg, #c9d6ff 0%, #e2e2e2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-icon {
  font-size: 60rpx;
}

.diary-content {
  flex: 1;
  padding: 20rpx;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.diary-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
}

.diary-location {
  font-size: 26rpx;
  color: #666;
}

.diary-date {
  font-size: 24rpx;
  color: #999;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
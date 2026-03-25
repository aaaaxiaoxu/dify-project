<template>
  <view class="container">
    <view class="header">
      <text class="title">我的日记</text>
    </view>
    
    <view class="filter-bar">
      <view class="search-box">
        <input 
          class="search-input" 
          placeholder="搜索日记..." 
          v-model="searchKeyword"
          @input="handleSearch"
        />
      </view>
      
      <view class="filter-options">
        <picker mode="selector" :range="emotionOptions" @change="handleEmotionChange">
          <view class="filter-option">
            {{ selectedEmotion || '情绪筛选' }}
          </view>
        </picker>
        
        <picker mode="date" @change="handleDateChange">
          <view class="filter-option">
            时间筛选
          </view>
        </picker>
      </view>
    </view>
    
    <view class="diary-list">
      <view 
        v-for="diary in filteredDiaries" 
        :key="diary.id" 
        class="diary-item"
        @click="goToDiaryDetail(diary.id)"
      >
        <view class="diary-image" v-if="diary.coverImage && diary.coverImage.length > 0">
          <image :src="diary.coverImage" mode="aspectFill" class="diary-image-content" @error="onImageError(diary)"></image>
        </view>
        <view class="diary-image" v-else>
          <image src="/static/images/placeholder.svg" mode="aspectFill" class="diary-image-content"></image>
        </view>
        <view class="diary-content">
          <view class="diary-header">
            <text class="diary-title">{{ diary.title }}</text>
            <view class="emotion-tag" :class="'emotion-' + diary.emotion">
              {{ getEmotionLabel(diary.emotion) }}
            </view>
          </view>
          <text class="diary-location">📍 {{ diary.location }}</text>
          <text class="diary-excerpt">{{ diary.content.substring(0, 80) }}...</text>
          <view class="diary-footer">
            <text class="diary-date">{{ formatDate(diary.date) }}</text>
            <view class="diary-actions">
              <text class="action-item" @click.stop="handleEdit(diary.id)">编辑</text>
              <text class="action-item" @click.stop="handleDelete(diary.id)">删除</text>
            </view>
          </view>
        </view>
      </view>
      
      <view v-if="filteredDiaries.length === 0" class="empty-state">
        <text class="empty-icon">📖</text>
        <text>暂无相关日记</text>
        <view v-if="!token">
          <text>请先登录</text>
          <button @click="goToLogin">前往登录</button>
        </view>
      </view>
    </view>
    
    <view class="fab" @click="goToWriteDiary">
      <text class="plus-icon">+</text>
    </view>
  </view>
</template>

<script>
import request from '../../utils/request.js'
import config from '../../api/config.js'

export default {
  data() {
    return {
      searchKeyword: '',
      selectedEmotion: '',
      selectedDate: '',
      emotionOptions: ['全部', '开心', '感动', '兴奋', '平静', '忧郁', '思念'],
      diaries: []
    }
  },
  
  computed: {
    token() {
      return this.$store.state.token
    },
    filteredDiaries() {
      let result = [...this.diaries].sort((a, b) => {
        // 按时间倒序排列
        return new Date(b.date) - new Date(a.date)
      })
      
      // 搜索过滤
      if (this.searchKeyword) {
        result = result.filter(diary => 
          diary.title.includes(this.searchKeyword) || 
          diary.content.includes(this.searchKeyword)
        )
      }
      
      // 情绪过滤
      if (this.selectedEmotion && this.selectedEmotion !== '全部') {
        result = result.filter(diary => diary.emotion === this.selectedEmotion)
      }
      
      // 时间过滤
      if (this.selectedDate) {
        result = result.filter(diary => diary.date === this.selectedDate)
      }
      
      return result
    }
  },
  
  onLoad() {
    this.loadDiaryList()
  },
  
  onShow() {
    // 页面每次显示时重新加载数据
    this.loadDiaryList()
  },
  
  methods: {
    loadDiaryList() {
      // 检查是否有token
      if (!this.token) {
        uni.showToast({
          title: '请先登录',
          icon: 'none'
        })
        return
      }

      // 调用后端获取日记列表接口
      request({
        url: config.DIARY_LIST,
        method: 'GET',
        header: {
          'Authorization': 'Bearer ' + this.token
        }
      }).then(res => {
        console.log('日记列表数据:', res); // 添加日志以便调试
        this.diaries = res.map(diary => ({
          id: diary.id,
          title: diary.title,
          location: diary.location,
          date: diary.date,
          emotion: diary.emotion,
          content: diary.content,
          coverImage: this.getCoverImage(diary.images),
          images: diary.images || [] // 保留完整图片数组
        }))
        console.log('处理后的日记数据:', this.diaries); // 添加日志以便调试
      }).catch(err => {
        console.error('获取日记列表失败:', err)
        uni.showToast({
          title: '获取日记列表失败',
          icon: 'none'
        })
      })
    },
    
    getCoverImage(images) {
      // 检查是否有图片
      if (!images || !Array.isArray(images) || images.length === 0) {
        return '/static/images/placeholder.svg';
      }
      
      // 返回第一张图片
      const firstImage = images[0];
      if (!firstImage) {
        return '/static/images/placeholder.svg';
      }
      
      return firstImage;
    },
    
    handleSearch() {
      // 搜索处理已在computed中完成
    },
    
    handleEmotionChange(e) {
      this.selectedEmotion = this.emotionOptions[e.detail.value]
    },
    
    handleDateChange(e) {
      this.selectedDate = e.detail.value
    },
    
    getEmotionLabel(emotion) {
      const labels = {
        '开心': '😊',
        '感动': '😢',
        '兴奋': '🤩',
        '平静': '😌',
        '忧郁': '😔',
        '思念': '🥺'
      }
      return labels[emotion] || emotion
    },
    
    formatDate(dateString) {
      const date = new Date(dateString)
      return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`
    },
    
    goToWriteDiary() {
      uni.navigateTo({
        url: '/pages/diary/edit'
      })
    },
    
    goToDiaryDetail(id) {
      uni.navigateTo({
        url: `/pages/diary/detail?id=${id}`
      })
    },
    
    handleEdit(id) {
      uni.navigateTo({
        url: `/pages/diary/edit?id=${id}`
      })
    },
    
    handleDelete(id) {
      uni.showModal({
        title: '确认删除',
        content: '确定要删除这篇日记吗？',
        success: (res) => {
          if (res.confirm) {
            // 调用后端删除日记接口
            request({
              url: config.DIARY_DELETE.replace('<int:diary_id>', id),
              method: 'DELETE',
              header: {
                'Authorization': 'Bearer ' + this.token
              }
            }).then(res => {
              if (res.msg === '删除成功') {
                uni.showToast({
                  title: '删除成功',
                  icon: 'success'
                })
                // 重新加载日记列表
                this.loadDiaryList()
              } else {
                uni.showToast({
                  title: res.msg || '删除失败',
                  icon: 'none'
                })
              }
            }).catch(err => {
              uni.showToast({
                title: '删除失败',
                icon: 'none'
              })
            })
          }
        }
      })
    },
    
    onImageError(diary) {
      console.log('图片加载失败:', diary.coverImage);
      // 图片加载失败时，清除coverImage以显示占位符
      // 使用Vue.set或者通过索引更新数组元素来确保响应性
      const index = this.diaries.findIndex(item => item.id === diary.id);
      if (index !== -1) {
        this.diaries[index].coverImage = '/static/images/placeholder.svg';
      }
    },
    
    goToLogin() {
      uni.navigateTo({
        url: '/pages/login/login'
      })
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
  margin-bottom: 30rpx;
  padding-top: 20rpx;
}

.title {
  font-size: 40rpx;
  font-weight: bold;
  color: #333;
  text-shadow: 1rpx 1rpx 2rpx rgba(0,0,0,0.1);
}

.filter-bar {
  background: #fff;
  border-radius: 20rpx;
  padding: 20rpx;
  margin-bottom: 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.05);
}

.search-box {
  margin-bottom: 20rpx;
}

.search-input {
  width: 100%;
  height: 70rpx;
  padding: 0 20rpx;
  background: #f8f8f8;
  border-radius: 10rpx;
  font-size: 28rpx;
  box-shadow: inset 0 1rpx 3rpx rgba(0,0,0,0.1);
}

.filter-options {
  display: flex;
  justify-content: space-between;
}

.filter-option {
  flex: 1;
  text-align: center;
  padding: 15rpx;
  background: #f8f8f8;
  border-radius: 10rpx;
  margin: 0 10rpx;
  font-size: 26rpx;
  box-shadow: 0 2rpx 5rpx rgba(0,0,0,0.05);
}

.diary-list {
  display: flex;
  flex-direction: column;
  gap: 30rpx;
  padding-bottom: 150rpx;
}

.diary-item {
  background: #fff;
  border-radius: 20rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.05);
  transition: all 0.3s ease;
}

.diary-item:hover {
  transform: translateY(-5rpx);
  box-shadow: 0 8rpx 25rpx rgba(0,0,0,0.1);
}

.diary-image {
  width: 100%;
  height: 300rpx;
  overflow: hidden;
}

.diary-image-content {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.diary-image-placeholder {
  width: 100%;
  height: 300rpx;
  background: linear-gradient(135deg, #c9d6ff 0%, #e2e2e2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-icon {
  font-size: 80rpx;
}

.diary-content {
  padding: 20rpx;
}

.diary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15rpx;
}

.diary-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
}

.emotion-tag {
  padding: 5rpx 15rpx;
  border-radius: 20rpx;
  font-size: 24rpx;
}

.emotion-开心 {
  background-color: #FFE4B5;
  color: #FF8C00;
}

.emotion-感动 {
  background-color: #E6E6FA;
  color: #9370DB;
}

.emotion-兴奋 {
  background-color: #FFB6C1;
  color: #FF69B4;
}

.emotion-平静 {
  background-color: #E0FFFF;
  color: #20B2AA;
}

.emotion-忧郁 {
  background-color: #D3D3D3;
  color: #696969;
}

.emotion-思念 {
  background-color: #DDA0DD;
  color: #8B008B;
}

.diary-location {
  font-size: 26rpx;
  color: #666;
  margin-bottom: 15rpx;
}

.diary-excerpt {
  font-size: 26rpx;
  color: #999;
  margin-bottom: 20rpx;
  line-height: 1.5;
}

.diary-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.diary-date {
  font-size: 24rpx;
  color: #999;
}

.diary-actions {
  display: flex;
}

.action-item {
  margin-left: 30rpx;
  font-size: 26rpx;
  color: #007AFF;
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

.fab {
  position: fixed;
  right: 50rpx;
  bottom: 100rpx;
  width: 100rpx;
  height: 100rpx;
  background: linear-gradient(135deg, #007AFF 0%, #00d4ff 100%);
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 4rpx 20rpx rgba(0,122,255,0.3);
  transition: all 0.3s ease;
}

.fab:hover {
  transform: scale(1.05);
}

.plus-icon {
  font-size: 60rpx;
  color: white;
  font-weight: bold;
}
</style>
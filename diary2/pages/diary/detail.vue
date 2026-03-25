<template>
  <view class="container">
    <view class="diary-header">
      <text class="diary-title">{{ diaryData.title }}</text>
      <view class="diary-meta">
        <text class="meta-item">📅 {{ formatDate(diaryData.date) }}</text>
        <text class="meta-item">📍 {{ diaryData.location }}</text>
        <view class="emotion-tag" :class="'emotion-' + diaryData.emotion">
          {{ getEmotionLabel(diaryData.emotion) }}
        </view>
      </view>
    </view>
    
    <view class="diary-content">
      <swiper 
        v-if="diaryData.images && diaryData.images.length > 0" 
        class="image-swiper"
        indicator-dots
        autoplay
      >
        <swiper-item 
          v-for="(image, index) in diaryData.images" 
          :key="index"
        >
          <image 
            :src="image" 
            mode="aspectFit" 
            class="diary-image"
            @click="previewImage(image)"
          />
        </swiper-item>
      </swiper>
      
      <view class="video-section" v-if="diaryData.videos && diaryData.videos.length > 0">
        <view 
          v-for="(video, index) in diaryData.videos" 
          :key="index"
          class="diary-video"
        >
          <video :src="video.url" class="video-player" controls></video>
        </view>
      </view>
      
      <view class="content-rich-wrap">
        <rich-text class="content-rich" :nodes="diaryData.content"></rich-text>
      </view>
    </view>
    
    <view class="ai-analysis" v-if="aiAnalysis">
      <view class="analysis-header">
        <text class="analysis-title">🤖 AI智能分析</text>
      </view>
      <view class="analysis-content">
        <view class="analysis-item">
          <text class="analysis-label">情感分析:</text>
          <text>{{ aiAnalysis.emotion_analysis }}</text>
        </view>
        <view class="analysis-item">
          <text class="analysis-label">关键词:</text>
          <view class="keywords">
            <text 
              v-for="(keyword, index) in parseKeywords(aiAnalysis.keywords)" 
              :key="index"
              class="keyword-tag"
            >
              {{ keyword }}
            </text>
          </view>
        </view>
        <view class="analysis-item">
          <text class="analysis-label">旅行建议:</text>
          <text>{{ aiAnalysis.travel_advice }}</text>
        </view>
      </view>
    </view>
    
    <view class="share-section">
      <button class="share-btn" @click="generateShareLink">
        <text>🔗 生成分享链接</text>
      </button>
      <button class="edit-btn" @click="editDiary">
        <text>✏️ 编辑日记</text>
      </button>
    </view>
  </view>
</template>

<script>
import request from '../../utils/request.js'
import config from '../../api/config.js'

export default {
  data() {
    return {
      diaryId: null,
      diaryData: {
        title: '',
        location: '',
        date: '',
        emotion: '',
        content: '',
        images: [],
        videos: []
      },
      aiAnalysis: null
    }
  },
  
  onLoad(options) {
    if (options.id) {
      this.diaryId = options.id
      this.loadDiaryData(options.id)
      this.loadAiAnalysis(options.id)
    }
  },
  
  methods: {
    loadDiaryData(id) {
      // 调用后端获取日记详情接口
      request({
        url: config.DIARY_DETAIL.replace('<int:diary_id>', id),
        method: 'GET',
        header: {
          'Authorization': 'Bearer ' + this.$store.state.token
        }
      }).then(res => {
        this.diaryData = {
          title: res.title,
          location: res.location,
          date: res.date,
          emotion: res.emotion,
          content: res.content,
          images: res.images || [],
          videos: res.videos || []
        }
      }).catch(err => {
        uni.showToast({
          title: '加载日记失败',
          icon: 'none'
        })
      })
    },
    
    loadAiAnalysis(id) {
      // 调用后端AI分析接口
      request({
        url: config.AI_ANALYSIS,
        method: 'POST',
        data: {
          content: this.diaryData.content
        },
        header: {
          'Authorization': 'Bearer ' + this.$store.state.token
        }
      }).then(res => {
        this.aiAnalysis = res
      }).catch(err => {
        // 使用默认分析结果
        this.aiAnalysis = {
          emotion_analysis: '这篇日记表达了作者对旅行地的喜爱之情，整体情绪非常积极向上。',
          keywords: '["旅行", "美好", "回忆"]',
          travel_advice: '根据您的旅行经历，推荐您下次可以尝试不同的旅行方式。'
        }
      })
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
    
    parseKeywords(keywords) {
      try {
        return JSON.parse(keywords)
      } catch (e) {
        return typeof keywords === 'string' ? keywords.split(',') : []
      }
    },
    
    previewImage(imageUrl) {
      uni.previewImage({
        urls: [imageUrl]
      })
    },
    
    generateShareLink() {
      // 调用后端API生成分享链接
      request({
        url: config.SHARE_GENERATE,
        method: 'POST',
        data: {
          diary_id: this.diaryId
        },
        header: {
          'Authorization': 'Bearer ' + this.$store.state.token
        }
      }).then(res => {
        if (res.share_link) {
          // 复制到剪贴板
          uni.setClipboardData({
            data: res.share_link,
            success: () => {
              uni.showToast({
                title: '分享链接已复制到剪贴板',
                icon: 'success'
              })
            }
          })
        }
      }).catch(err => {
        uni.showToast({
          title: '生成分享链接失败',
          icon: 'none'
        })
      })
    },
    
    editDiary() {
      uni.navigateTo({
        url: `/pages/diary/edit?id=${this.diaryId}`
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

.diary-header {
  background: #fff;
  border-radius: 20rpx;
  padding: 30rpx;
  margin-bottom: 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.05);
}

.diary-title {
  font-size: 40rpx;
  font-weight: bold;
  color: #333;
  display: block;
  margin-bottom: 20rpx;
  text-shadow: 1rpx 1rpx 2rpx rgba(0,0,0,0.1);
}

.diary-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.meta-item {
  font-size: 26rpx;
  color: #666;
  margin-right: 30rpx;
  margin-bottom: 10rpx;
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

.diary-content {
  background: #fff;
  border-radius: 20rpx;
  padding: 30rpx;
  margin-bottom: 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.05);
}

.image-swiper {
  height: 400rpx;
  margin-bottom: 30rpx;
  border-radius: 15rpx;
  overflow: hidden;
}

.diary-image {
  width: 100%;
  height: 100%;
}

.video-section {
  margin-bottom: 30rpx;
}

.diary-video {
  margin-bottom: 20rpx;
}

.video-player {
  width: 100%;
  height: 400rpx;
  border-radius: 15rpx;
  overflow: hidden;
}

.content-rich-wrap {
  font-size: 30rpx;
  line-height: 1.6;
  color: #333;
  overflow: hidden;
}

.content-rich {
  display: block;
  word-break: break-word;
}

.ai-analysis {
  background: #fff;
  border-radius: 20rpx;
  padding: 30rpx;
  margin-bottom: 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.05);
}

.analysis-header {
  margin-bottom: 20rpx;
}

.analysis-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
}

.analysis-item {
  margin-bottom: 20rpx;
}

.analysis-label {
  font-weight: bold;
  margin-right: 15rpx;
  color: #007AFF;
}

.keywords {
  display: flex;
  flex-wrap: wrap;
}

.keyword-tag {
  padding: 5rpx 15rpx;
  margin: 10rpx 10rpx 0 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10rpx;
  font-size: 24rpx;
  color: white;
}

.share-section {
  display: flex;
  justify-content: space-between;
  padding-bottom: 30rpx;
}

.share-btn, .edit-btn {
  flex: 1;
  height: 100rpx;
  border: none;
  border-radius: 15rpx;
  font-size: 32rpx;
  margin: 0 10rpx;
  box-shadow: 0 4rpx 10rpx rgba(0,0,0,0.1);
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.share-btn {
  background: linear-gradient(135deg, #007AFF 0%, #00d4ff 100%);
  color: white;
}

.edit-btn {
  background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
  color: white;
}

.share-btn:hover, .edit-btn:hover {
  transform: translateY(-5rpx);
  box-shadow: 0 8rpx 15rpx rgba(0,0,0,0.15);
}
</style>
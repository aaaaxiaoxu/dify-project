<template>
  <view class="container">
    <view class="header">
      <text class="title">{{ isEdit ? '编辑日记' : '写日记' }}</text>
    </view>
    
    <view class="form-group">
      <input 
        class="form-input title-input" 
        placeholder="请输入标题" 
        v-model="diaryData.title"
      />
    </view>
    
    <view class="form-group">
      <view class="location-section">
        <input 
          class="form-input" 
          placeholder="请输入地点" 
          v-model="diaryData.location"
        />
        <button class="location-btn" @click="getCurrentLocation">
          <text v-if="!gettingLocation">获取当前位置</text>
          <text v-else>定位中...</text>
        </button>
      </view>
    </view>
    
    <view class="form-group">
      <view class="date-section">
        <text class="label">日期:</text>
        <picker mode="date" :value="diaryData.date" @change="handleDateChange">
          <view class="date-display">
            {{ diaryData.date || '请选择日期' }}
          </view>
        </picker>
      </view>
    </view>
    
    <view class="form-group">
      <view class="emotion-section">
        <text class="label">当时心情:</text>
        <view class="emotion-options">
          <view 
            v-for="(emotion, index) in emotionOptions" 
            :key="index"
            class="emotion-option"
            :class="{ active: diaryData.emotion === emotion.value }"
            @click="selectEmotion(emotion.value)"
          >
            <text>{{ emotion.label }}</text>
          </view>
        </view>
      </view>
    </view>
    
    <view class="form-group">
      <textarea 
        class="content-textarea" 
        placeholder="记录下这次旅行的美好时光..." 
        v-model="diaryData.content"
        maxlength="-1"
      />
    </view>
    
    <view class="form-group">
      <view class="image-section">
        <text class="label">照片:</text>
        <view class="image-upload-area">
          <view 
            v-for="(image, index) in diaryData.images" 
            :key="index"
            class="uploaded-image"
          >
            <image :src="image" mode="aspectFill" />
            <text class="remove-image" @click="removeImage(index)">×</text>
          </view>
          
          <view class="upload-button" @click="chooseImage" v-if="diaryData.images.length < 9">
            <text class="plus-icon">+</text>
            <text class="upload-text">添加照片</text>
          </view>
        </view>
      </view>
    </view>
    
    <view class="form-group">
      <view class="video-section">
        <text class="label">视频:</text>
        <view class="video-upload-area">
          <view 
            v-for="(video, index) in diaryData.videos" 
            :key="index"
            class="uploaded-video"
          >
            <video :src="video.url" class="video-preview" controls></video>
            <text class="remove-video" @click="removeVideo(index)">×</text>
          </view>
          
          <view class="upload-button" @click="chooseVideo" v-if="diaryData.videos.length < 5">
            <text class="plus-icon">+</text>
            <text class="upload-text">添加视频</text>
          </view>
        </view>
      </view>
    </view>
    
    <view class="ai-suggestion">
      <view class="suggestion-header">
        <text class="suggestion-title">AI写作建议</text>
        <button class="refresh-btn" @click="getAiSuggestion" :disabled="gettingSuggestion">
          <text v-if="!gettingSuggestion">刷新建议</text>
          <text v-else>生成中...</text>
        </button>
      </view>
      
      <view class="suggestion-content" v-if="aiSuggestion">
        <text>{{ aiSuggestion }}</text>
      </view>
      
      <view class="suggestion-placeholder" v-else>
        <text>点击"刷新建议"获取AI写作建议</text>
      </view>
    </view>
    
    <view class="form-actions">
      <button class="save-btn" @click="saveDiary">
        <text>{{ isEdit ? '更新日记' : '保存日记' }}</text>
      </button>
      <button class="cancel-btn" @click="cancelEdit">
        <text>取消</text>
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
      isEdit: false,
      gettingLocation: false,
      gettingSuggestion: false,
      diaryId: null,
      diaryData: {
        title: '',
        location: '',
        date: '',
        emotion: '',
        content: '',
        images: [],
        videos: [],
        latitude: null,
        longitude: null
      },
      emotionOptions: [
        { label: '😊 开心', value: '开心' },
        { label: '😢 感动', value: '感动' },
        { label: '🤩 兴奋', value: '兴奋' },
        { label: '😌 平静', value: '平静' },
        { label: '😔 忧郁', value: '忧郁' },
        { label: '🥺 思念', value: '思念' }
      ],
      aiSuggestion: ''
    }
  },
  
  onLoad(options) {
    if (options.id) {
      this.isEdit = true
      this.diaryId = options.id
      this.loadDiaryData(options.id)
    } else {
      // 设置默认日期为今天
      const today = new Date()
      this.diaryData.date = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
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
          videos: res.videos || [],
          latitude: res.latitude || null,
          longitude: res.longitude || null
        }
      }).catch(err => {
        uni.showToast({
          title: '加载日记失败',
          icon: 'none'
        })
      })
    },
    
    handleDateChange(e) {
      this.diaryData.date = e.detail.value
    },
    
    selectEmotion(emotion) {
      this.diaryData.emotion = emotion
    },
    
    getCurrentLocation() {
      this.gettingLocation = true
      
      // 使用uni.getLocation获取准确位置
      uni.getLocation({
        type: 'gcj02', // 使用国测局坐标系，适用于腾讯地图
        geocode: true, // 获取详细地址信息
        success: (res) => {
          console.log('定位成功', res)
          this.gettingLocation = false
          
          // 保存经纬度到数据中
          this.diaryData.latitude = res.latitude
          this.diaryData.longitude = res.longitude
          
          // 如果有地址信息，则使用详细地址作为地点名称
          if (res.address) {
            // 优先使用中文地址
            const address = res.address
            let locationStr = ''
            
            // 按重要性拼接地址
            if (address.province) locationStr += address.province
            if (address.city) locationStr += address.city
            if (address.district) locationStr += address.district
            if (address.poiName) locationStr += address.poiName
            else if (address.street) locationStr += address.street
            
            this.diaryData.location = locationStr || '未知位置'
          } else {
            // 如果没有地址信息，使用默认位置，但仍然保存经纬度
            this.diaryData.location = '未知位置'
          }
          
          uni.showToast({
            title: '定位成功',
            icon: 'success'
          })
        },
        fail: (err) => {
          console.error('定位失败', err)
          this.gettingLocation = false
          
          // 定位失败时使用模拟数据
          this.diaryData.location = '杭州市西湖区'
          this.diaryData.latitude = 30.242289
          this.diaryData.longitude = 120.143669
          
          uni.showToast({
            title: '定位失败，使用默认位置',
            icon: 'none'
          })
        }
      })
    },
    
    chooseImage() {
      uni.chooseImage({
        count: 9 - this.diaryData.images.length,
        success: (res) => {
          this.diaryData.images = [...this.diaryData.images, ...res.tempFilePaths]
        }
      })
    },
    
    removeImage(index) {
      this.diaryData.images.splice(index, 1)
    },
    
    chooseVideo() {
      uni.chooseVideo({
        success: (res) => {
          if (this.diaryData.videos.length < 5) {
            this.diaryData.videos.push({
              url: res.tempFilePath,
              thumbnail: '' // 实际应用中可以从视频中提取缩略图
            })
          } else {
            uni.showToast({
              title: '最多只能上传5个视频',
              icon: 'none'
            })
          }
        }
      })
    },
    
    removeVideo(index) {
      this.diaryData.videos.splice(index, 1)
    },
    
    getAiSuggestion() {
      this.gettingSuggestion = true
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
        this.gettingSuggestion = false
        // 构建更丰富的AI建议显示内容
        let suggestionText = res.emotion_analysis || ''
        
        if (res.keywords && res.keywords.length > 0) {
          suggestionText += `\n\n关键词: ${res.keywords.join(', ')}`
        }
        
        if (res.travel_advice) {
          suggestionText += `\n\n旅行建议: ${res.travel_advice}`
        }
        
        if (res.writing_style) {
          suggestionText += `\n\n写作风格: ${res.writing_style}`
        }
        
        if (res.writing_suggestion) {
          suggestionText += `\n\n写作建议: ${res.writing_suggestion}`
        }
        
        this.aiSuggestion = suggestionText || '你可以描述一下当时的感受和周围的环境。'
      }).catch(err => {
        this.gettingSuggestion = false
        this.aiSuggestion = '你可以描述一下当时的感受和周围的环境。'
      })
    },
    
    saveDiary() {
      if (!this.diaryData.title) {
        uni.showToast({
          title: '请输入标题',
          icon: 'none'
        })
        return
      }
      
      if (!this.diaryData.location) {
        uni.showToast({
          title: '请输入地点',
          icon: 'none'
        })
        return
      }
      
      if (!this.diaryData.date) {
        uni.showToast({
          title: '请选择日期',
          icon: 'none'
        })
        return
      }
      
      if (!this.diaryData.emotion) {
        uni.showToast({
          title: '请选择心情',
          icon: 'none'
        })
        return
      }
      
      if (!this.diaryData.content) {
        uni.showToast({
          title: '请输入内容',
          icon: 'none'
        })
        return
      }
      
      uni.showLoading({
        title: '保存中...'
      })
      
      // 根据是编辑还是创建调用不同的接口
      const url = this.isEdit ? config.DIARY_UPDATE.replace('<int:diary_id>', this.diaryId) : config.DIARY_CREATE
      const method = this.isEdit ? 'PUT' : 'POST'
      
      // 调用后端保存日记接口
      request({
        url: url,
        method: method,
        data: {
          title: this.diaryData.title,
          location: this.diaryData.location,
          date: this.diaryData.date,
          emotion: this.diaryData.emotion,
          content: this.diaryData.content,
          images: this.diaryData.images,
          videos: this.diaryData.videos,
          latitude: this.diaryData.latitude,
          longitude: this.diaryData.longitude
        },
        header: {
          'Authorization': 'Bearer ' + this.$store.state.token
        }
      }).then(res => {
        uni.hideLoading()
        // 检查响应状态码而不是响应内容
        if (res.msg === '创建成功' || res.msg === '更新成功' || res.diary_id) {
          uni.showToast({
            title: this.isEdit ? '更新成功' : '创建成功',
            icon: 'success'
          })
          
          setTimeout(() => {
            uni.navigateBack()
          }, 1500)
        } else {
          uni.showToast({
            title: res.msg || '保存失败',
            icon: 'none'
          })
        }
      }).catch(err => {
        uni.hideLoading()
        console.error('保存日记失败:', err)
        // 即使出现错误，也检查响应内容
        if (err && err.data && (err.data.msg === '创建成功' || err.data.msg === '更新成功')) {
          uni.showToast({
            title: this.isEdit ? '更新成功' : '创建成功',
            icon: 'success'
          })
          
          setTimeout(() => {
            uni.navigateBack()
          }, 1500)
        } else {
          uni.showToast({
            title: '保存失败',
            icon: 'none'
          })
        }
      })
    },
    
    cancelEdit() {
      uni.navigateBack()
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

.form-group {
  margin-bottom: 30rpx;
  background: #fff;
  border-radius: 20rpx;
  padding: 20rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.05);
  transition: all 0.3s ease;
}

.form-group:hover {
  box-shadow: 0 8rpx 25rpx rgba(0,0,0,0.1);
}

.form-input {
  width: 100%;
  padding: 20rpx;
  font-size: 28rpx;
  border: none;
  outline: none;
  background: #f8f8f8;
  border-radius: 10rpx;
}

.title-input {
  font-size: 36rpx;
  font-weight: bold;
}

.location-section {
  display: flex;
  align-items: center;
}

.location-btn {
  flex-shrink: 0;
  margin-left: 20rpx;
  padding: 15rpx 20rpx;
  background: linear-gradient(135deg, #007AFF 0%, #00d4ff 100%);
  color: white;
  border: none;
  border-radius: 10rpx;
  font-size: 24rpx;
  box-shadow: 0 4rpx 10rpx rgba(0,122,255,0.3);
  transition: all 0.3s ease;
}

.location-btn:hover {
  transform: translateY(-2rpx);
  box-shadow: 0 6rpx 15rpx rgba(0,122,255,0.4);
}

.date-section {
  display: flex;
  align-items: center;
}

.label {
  font-size: 28rpx;
  margin-right: 20rpx;
  color: #333;
  font-weight: 500;
}

.date-display {
  flex: 1;
  padding: 20rpx;
  background: #f8f8f8;
  border-radius: 10rpx;
  font-size: 28rpx;
}

.emotion-section {
  display: flex;
  flex-direction: column;
}

.emotion-options {
  display: flex;
  flex-wrap: wrap;
  margin-top: 20rpx;
}

.emotion-option {
  padding: 15rpx 25rpx;
  margin: 10rpx;
  background: #f8f8f8;
  border-radius: 30rpx;
  font-size: 24rpx;
  transition: all 0.3s ease;
}

.emotion-option:hover {
  transform: translateY(-2rpx);
}

.emotion-option.active {
  background: linear-gradient(135deg, #007AFF 0%, #00d4ff 100%);
  color: white;
  box-shadow: 0 4rpx 10rpx rgba(0,122,255,0.3);
}

.content-textarea {
  width: 100%;
  height: 300rpx;
  padding: 20rpx;
  font-size: 28rpx;
  border: none;
  outline: none;
  resize: none;
  background: #f8f8f8;
  border-radius: 10rpx;
}

.image-section, .video-section {
  display: flex;
  flex-direction: column;
}

.image-upload-area, .video-upload-area {
  display: flex;
  flex-wrap: wrap;
  margin-top: 20rpx;
}

.uploaded-image, .uploaded-video {
  position: relative;
  width: 150rpx;
  height: 150rpx;
  margin: 10rpx;
}

.uploaded-image image {
  width: 100%;
  height: 100%;
  border-radius: 10rpx;
}

.video-preview {
  width: 100%;
  height: 100%;
  border-radius: 10rpx;
}

.remove-image, .remove-video {
  position: absolute;
  top: -15rpx;
  right: -15rpx;
  width: 40rpx;
  height: 40rpx;
  background-color: #ff4d4f;
  border-radius: 50%;
  color: white;
  text-align: center;
  line-height: 40rpx;
  font-size: 28rpx;
  box-shadow: 0 2rpx 5rpx rgba(0,0,0,0.2);
}

.upload-button {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: 150rpx;
  height: 150rpx;
  margin: 10rpx;
  border: 2rpx dashed #007AFF;
  border-radius: 10rpx;
  transition: all 0.3s ease;
}

.upload-button:hover {
  background-color: rgba(0,122,255,0.1);
}

.plus-icon {
  font-size: 60rpx;
  color: #007AFF;
}

.upload-text {
  font-size: 20rpx;
  color: #007AFF;
}

.ai-suggestion {
  background: #fff;
  border-radius: 20rpx;
  padding: 20rpx;
  margin-bottom: 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.05);
}

.suggestion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.suggestion-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
}

.refresh-btn {
  padding: 10rpx 20rpx;
  background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
  color: white;
  border: none;
  border-radius: 10rpx;
  font-size: 24rpx;
  box-shadow: 0 4rpx 10rpx rgba(106,17,203,0.3);
  transition: all 0.3s ease;
}

.refresh-btn:hover {
  transform: translateY(-2rpx);
  box-shadow: 0 6rpx 15rpx rgba(106,17,203,0.4);
}

.refresh-btn[disabled] {
  background: #ccc;
  box-shadow: none;
}

.suggestion-content {
  padding: 20rpx;
  background: #f8f8f8;
  border-radius: 10rpx;
  font-size: 26rpx;
  line-height: 1.5;
}

.suggestion-placeholder {
  padding: 20rpx;
  text-align: center;
  color: #999;
  font-size: 26rpx;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  padding-bottom: 30rpx;
}

.save-btn, .cancel-btn {
  flex: 1;
  height: 100rpx;
  border: none;
  border-radius: 15rpx;
  font-size: 32rpx;
  margin: 0 10rpx;
  box-shadow: 0 4rpx 10rpx rgba(0,0,0,0.1);
  transition: all 0.3s ease;
}

.save-btn {
  background: linear-gradient(135deg, #007AFF 0%, #00d4ff 100%);
  color: white;
}

.cancel-btn {
  background: #f8f8f8;
  color: #333;
}

.save-btn:hover, .cancel-btn:hover {
  transform: translateY(-5rpx);
  box-shadow: 0 8rpx 15rpx rgba(0,0,0,0.15);
}
</style>
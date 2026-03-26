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
      <button class="share-btn" @click="showShareDialog = true">
        <text>🔗 生成分享链接</text>
      </button>
      <button class="edit-btn" @click="editDiary">
        <text>✏️ 编辑日记</text>
      </button>
    </view>

    <!-- 已有分享链接 -->
    <view class="existing-shares" v-if="existingShares.length > 0">
      <text class="existing-title">已生成的分享链接</text>
      <view
        class="existing-item"
        v-for="item in existingShares"
        :key="item.id"
      >
        <view class="existing-left">
          <view class="existing-row">
            <view class="existing-status" :class="'st-' + item.status">
              <text>{{ shareStatusText(item.status) }}</text>
            </view>
            <text class="existing-meta" v-if="item.has_password">🔒 有密码</text>
            <text class="existing-meta">👁 {{ item.view_count }}次访问</text>
          </view>
          <text class="existing-time">{{ item.created_at ? item.created_at.slice(0, 16).replace('T', ' ') : '' }}</text>
        </view>
        <view class="existing-actions">
          <button
            class="copy-btn"
            :class="{ disabled: item.status !== 'active' }"
            @click="copyExistingLink(item.token)"
          >复制</button>
          <button
            class="delete-btn"
            @click="deleteShare(item.id)"
          >删除</button>
        </view>
      </view>
    </view>

    <!-- 分享配置弹窗 -->
    <view class="share-mask" v-if="showShareDialog" @click.self="showShareDialog = false">
      <view class="share-dialog">
        <text class="dialog-title">分享设置</text>

        <!-- 有效期 -->
        <view class="dialog-field">
          <text class="field-label">有效期</text>
          <view class="option-group">
            <view
              class="option-chip"
              :class="{ active: shareForm.expire === 7 }"
              @click="shareForm.expire = 7"
            ><text>7天</text></view>
            <view
              class="option-chip"
              :class="{ active: shareForm.expire === 30 }"
              @click="shareForm.expire = 30"
            ><text>30天</text></view>
            <view
              class="option-chip"
              :class="{ active: shareForm.expire === 0 }"
              @click="shareForm.expire = 0"
            ><text>永久</text></view>
          </view>
        </view>

        <!-- 访问密码 -->
        <view class="dialog-field">
          <text class="field-label">访问密码（选填）</text>
          <input
            class="field-input"
            v-model="shareForm.password"
            placeholder="留空表示公开访问"
            type="text"
          />
        </view>

        <!-- 访问次数 -->
        <view class="dialog-field">
          <text class="field-label">访问次数上限（选填）</text>
          <input
            class="field-input"
            v-model="shareForm.viewLimit"
            placeholder="留空表示不限次数"
            type="number"
          />
        </view>

        <view class="dialog-actions">
          <button class="dialog-cancel" @click="showShareDialog = false">取消</button>
          <button class="dialog-confirm" @click="generateShareLink">确认分享</button>
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
      aiAnalysis: null,
      showShareDialog: false,
      existingShares: [],
      shareForm: {
        expire: 7,
        password: '',
        viewLimit: ''
      }
    }
  },
  
  onLoad(options) {
    if (options.id) {
      this.diaryId = options.id
      this.loadDiaryData(options.id)
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
        // 日记数据加载完成后再调用 AI 分析
        this.loadAiAnalysis(this.diaryId)
        // 加载已有分享链接
        this.loadExistingShares(this.diaryId)
      }).catch(err => {
        uni.showToast({
          title: '加载日记失败',
          icon: 'none'
        })
      })
    },
    
    loadAiAnalysis(id) {
      // 调用后端AI分析接口，传 diary_id，后端会自动查库/调 Dify
      request({
        url: config.AI_ANALYSIS,
        method: 'POST',
        data: {
          diary_id: id
        },
        header: {
          'Authorization': 'Bearer ' + this.$store.state.token
        }
      }).then(res => {
        this.aiAnalysis = res
      }).catch(err => {
        // 分析失败时不显示分析模块
        this.aiAnalysis = null
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
      const data = { diary_id: this.diaryId }

      if (this.shareForm.expire > 0) {
        data.expire_days = this.shareForm.expire
      }
      if (this.shareForm.password) {
        data.view_password = this.shareForm.password
      }
      if (this.shareForm.viewLimit) {
        data.view_limit = parseInt(this.shareForm.viewLimit)
      }

      request({
        url: config.SHARE_GENERATE,
        method: 'POST',
        data,
        header: {
          'Authorization': 'Bearer ' + this.$store.state.token
        }
      }).then(res => {
        this.showShareDialog = false
        if (res.share_token) {
          const link = config.SHARE_PAGE + res.share_token
          
          // 立刻把新链接插入到页面列表最前面，不等后端二次请求
          this.existingShares.unshift({
            id: Date.now(),
            token: res.share_token,
            has_password: res.has_password,
            expire_time: res.expire_time,
            view_limit: res.view_limit,
            view_count: 0,
            status: 'active',
            created_at: new Date().toISOString()
          })
          
          uni.setClipboardData({
            data: link,
            success: () => {
              let tipParts = ['分享链接已复制到剪贴板']
              if (res.has_password) tipParts.push('密码: ' + this.shareForm.password)
              if (res.expire_time) tipParts.push('有效期至 ' + res.expire_time.slice(0, 10))
              uni.showModal({
                title: '分享成功',
                content: tipParts.join('\n'),
                showCancel: false
              })
            }
          })
          // 重置表单
          this.shareForm = { expire: 7, password: '', viewLimit: '' }
        }
      }).catch(err => {
        uni.showToast({ title: '生成分享链接失败', icon: 'none' })
      })
    },
    
    editDiary() {
      uni.navigateTo({
        url: `/pages/diary/edit?id=${this.diaryId}`
      })
    },
    
    loadExistingShares(diaryId) {
      request({
        url: config.SHARE_BY_DIARY + diaryId,
        method: 'GET',
        header: {
          'Authorization': 'Bearer ' + this.$store.state.token
        }
      }).then(res => {
        this.existingShares = Array.isArray(res) ? res : []
      }).catch(() => {
        this.existingShares = []
      })
    },
    
    copyExistingLink(token) {
      const link = config.SHARE_PAGE + token
      uni.setClipboardData({
        data: link,
        success: () => {
          uni.showToast({ title: '链接已复制', icon: 'success' })
        }
      })
    },
    
    shareStatusText(status) {
      const map = { active: '有效', expired: '已过期', revoked: '已撤销', limit_reached: '次数已满' }
      return map[status] || status
    },
    
    deleteShare(shareId) {
      uni.showModal({
        title: '确认删除',
        content: '删除后该分享链接将永久失效，确定吗？',
        success: (res) => {
          if (!res.confirm) return
          request({
            url: config.SHARE_DELETE + shareId,
            method: 'POST',
            header: { 'Authorization': 'Bearer ' + this.$store.state.token }
          }).then(() => {
            this.existingShares = this.existingShares.filter(s => s.id !== shareId)
            uni.showToast({ title: '已删除', icon: 'success' })
          }).catch(() => {
            uni.showToast({ title: '删除失败', icon: 'none' })
          })
        }
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

/* 已有分享链接 */
.existing-shares {
  background: #fff;
  border-radius: 20rpx;
  padding: 24rpx 30rpx;
  margin-bottom: 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.05);
}

.existing-title {
  display: block;
  font-size: 28rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 20rpx;
}

.existing-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18rpx 0;
  border-bottom: 1rpx solid #f5f5f5;
}

.existing-item:last-child {
  border-bottom: none;
}

.existing-left {
  flex: 1;
  overflow: hidden;
}

.existing-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-bottom: 8rpx;
}

.existing-status {
  padding: 4rpx 14rpx;
  border-radius: 16rpx;
  font-size: 20rpx;
}

.st-active {
  background: #e8f5e9;
  color: #43a047;
}

.st-expired {
  background: #fff3e0;
  color: #ef6c00;
}

.st-revoked {
  background: #fce4ec;
  color: #e53935;
}

.st-limit_reached {
  background: #ede7f6;
  color: #5e35b1;
}

.existing-meta {
  font-size: 22rpx;
  color: #999;
}

.existing-time {
  font-size: 22rpx;
  color: #bbb;
}

.existing-actions {
  display: flex;
  gap: 10rpx;
  margin-left: 16rpx;
  flex-shrink: 0;
}

.copy-btn {
  width: 100rpx;
  height: 56rpx;
  line-height: 56rpx;
  text-align: center;
  font-size: 24rpx;
  border: none;
  border-radius: 10rpx;
  background: linear-gradient(135deg, #007AFF 0%, #00d4ff 100%);
  color: #fff;
  padding: 0;
}

.copy-btn.disabled {
  background: #ddd;
  color: #999;
}

.delete-btn {
  width: 100rpx;
  height: 56rpx;
  line-height: 56rpx;
  text-align: center;
  font-size: 24rpx;
  border: none;
  border-radius: 10rpx;
  background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
  color: #fff;
  padding: 0;
}

/* 分享弹窗 */
.share-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

.share-dialog {
  width: 85%;
  background: #fff;
  border-radius: 24rpx;
  padding: 40rpx;
  box-shadow: 0 20rpx 60rpx rgba(0, 0, 0, 0.2);
}

.dialog-title {
  display: block;
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
  text-align: center;
  margin-bottom: 36rpx;
}

.dialog-field {
  margin-bottom: 30rpx;
}

.field-label {
  display: block;
  font-size: 26rpx;
  color: #666;
  margin-bottom: 14rpx;
}

.option-group {
  display: flex;
  gap: 16rpx;
}

.option-chip {
  flex: 1;
  text-align: center;
  padding: 16rpx 0;
  border-radius: 12rpx;
  background: #f0f0f0;
  font-size: 26rpx;
  color: #666;
  transition: all 0.2s ease;
}

.option-chip.active {
  background: linear-gradient(135deg, #007AFF 0%, #00d4ff 100%);
  color: #fff;
  box-shadow: 0 4rpx 12rpx rgba(0, 122, 255, 0.3);
}

.field-input {
  width: 100%;
  height: 72rpx;
  border: 2rpx solid #e5e5e5;
  border-radius: 12rpx;
  padding: 0 20rpx;
  font-size: 28rpx;
  color: #333;
  box-sizing: border-box;
}

.dialog-actions {
  display: flex;
  gap: 20rpx;
  margin-top: 36rpx;
}

.dialog-cancel,
.dialog-confirm {
  flex: 1;
  height: 80rpx;
  border-radius: 12rpx;
  font-size: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
}

.dialog-cancel {
  background: #f0f0f0;
  color: #666;
}

.dialog-confirm {
  background: linear-gradient(135deg, #007AFF 0%, #00d4ff 100%);
  color: #fff;
  box-shadow: 0 4rpx 12rpx rgba(0, 122, 255, 0.3);
}
</style>
<template>
  <view class="container">
    <view class="header">
      <text class="title">我的日记</text>
    </view>

    <view class="view-switch">
      <view
        class="view-tab"
        :class="{ active: viewMode === 'published' }"
        @click="viewMode = 'published'"
      >
        已发布
      </view>
      <view
        class="view-tab"
        :class="{ active: viewMode === 'drafts' }"
        @click="viewMode = 'drafts'"
      >
        草稿箱
      </view>
    </view>
    
    <view class="filter-bar">
      <view class="search-box">
        <input 
          class="search-input" 
          :placeholder="viewMode === 'drafts' ? '搜索草稿...' : '搜索日记...'" 
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
        @click="openDiary(diary)"
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
            <view v-if="diary.isDraft" class="draft-badge">草稿</view>
            <view class="emotion-tag" :class="'emotion-' + diary.emotion">
              {{ getEmotionLabel(diary.emotion) }}
            </view>
          </view>
          <text class="diary-location">📍 {{ diary.location }}</text>
          <text class="diary-excerpt">{{ contentExcerpt(diary.content) }}</text>
          <view class="diary-footer">
            <text class="diary-date">{{ formatDiaryMeta(diary) }}</text>
            <view class="diary-actions">
              <text class="action-item" @click.stop="handleEdit(diary.id)">{{ diary.isDraft ? '继续编辑' : '编辑' }}</text>
              <text class="action-item" @click.stop="handleDelete(diary.id)">删除</text>
            </view>
          </view>
        </view>
      </view>
      
      <view v-if="filteredDiaries.length === 0" class="empty-state">
        <text class="empty-icon">📖</text>
        <text>{{ viewMode === 'drafts' ? '草稿箱为空' : '暂无相关日记' }}</text>
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
import { stripHtml } from '../../utils/html.js'

export default {
  data() {
    return {
      searchKeyword: '',
      selectedEmotion: '',
      selectedDate: '',
      viewMode: 'published',
      emotionOptions: ['全部', '开心', '感动', '兴奋', '平静', '忧郁', '思念'],
      publishedDiaries: [],
      draftDiaries: []
    }
  },
  
  computed: {
    token() {
      return this.$store.state.token
    },

    currentDiaries() {
      return this.viewMode === 'drafts' ? this.draftDiaries : this.publishedDiaries
    },

    filteredDiaries() {
      let result = [...this.currentDiaries].sort((a, b) => {
        const left = a.isDraft ? (a.updatedAt || a.createdAt || a.date) : (a.date || a.createdAt)
        const right = b.isDraft ? (b.updatedAt || b.createdAt || b.date) : (b.date || b.createdAt)
        return new Date(right || 0) - new Date(left || 0)
      })
      
      if (this.searchKeyword) {
        const kw = this.searchKeyword
        result = result.filter((diary) => {
          const plain = stripHtml(diary.content || '')
          return diary.title.includes(kw) || plain.includes(kw)
        })
      }
      
      if (this.selectedEmotion && this.selectedEmotion !== '全部') {
        result = result.filter((diary) => diary.emotion === this.selectedEmotion)
      }
      
      if (this.selectedDate) {
        result = result.filter((diary) => diary.date === this.selectedDate)
      }
      
      return result
    }
  },
  
  onLoad() {
    this.loadDiaryList()
  },
  
  onShow() {
    this.loadDiaryList()
  },
  
  methods: {
    normalizeDiaryListItem(diary) {
      return {
        id: diary.id,
        title: diary.title || '未命名草稿',
        location: diary.location || '未填写地点',
        date: diary.date,
        updatedAt: diary.updated_at,
        createdAt: diary.created_at,
        emotion: diary.emotion || '未设置',
        content: diary.content || '',
        coverImage: this.getCoverImage(diary.images),
        images: diary.images || [],
        isDraft: !!diary.is_draft
      }
    },

    contentExcerpt(html) {
      const t = stripHtml(html || '')
      if (!t) return this.viewMode === 'drafts' ? '草稿内容未填写' : '…'
      if (t.length <= 80) return t
      return `${t.substring(0, 80)}…`
    },

    loadDiaryList() {
      if (!this.token) {
        this.publishedDiaries = []
        this.draftDiaries = []
        uni.showToast({
          title: '请先登录',
          icon: 'none'
        })
        return
      }

      Promise.all([
        request({
          url: config.DIARY_LIST,
          method: 'GET',
          header: {
            'Authorization': 'Bearer ' + this.token
          }
        })
          .then((data) => ({ ok: true, data }))
          .catch((error) => ({ ok: false, error })),
        request({
          url: config.DIARY_DRAFTS,
          method: 'GET',
          header: {
            'Authorization': 'Bearer ' + this.token
          }
        })
          .then((data) => ({ ok: true, data }))
          .catch((error) => ({ ok: false, error }))
      ]).then(([publishedResult, draftResult]) => {
        if (publishedResult.ok) {
          this.publishedDiaries = (publishedResult.data || []).map((diary) => this.normalizeDiaryListItem(diary))
        } else {
          console.error('获取已发布日记失败:', publishedResult.error)
          this.publishedDiaries = []
        }

        if (draftResult.ok) {
          this.draftDiaries = (draftResult.data || []).map((diary) => this.normalizeDiaryListItem(diary))
        } else {
          console.error('获取草稿列表失败:', draftResult.error)
          this.draftDiaries = []
        }

        if (!publishedResult.ok && !draftResult.ok) {
          uni.showToast({
            title: '获取日记列表失败',
            icon: 'none'
          })
        }
      })
    },
    
    getCoverImage(images) {
      if (!images || !Array.isArray(images) || images.length === 0) {
        return '/static/images/placeholder.svg'
      }
      
      const firstImage = images[0]
      if (!firstImage) {
        return '/static/images/placeholder.svg'
      }
      
      return firstImage
    },
    
    handleSearch() {},
    
    handleEmotionChange(e) {
      this.selectedEmotion = this.emotionOptions[e.detail.value]
    },
    
    handleDateChange(e) {
      this.selectedDate = e.detail.value
    },
    
    getEmotionLabel(emotion) {
      if (emotion === '未设置') {
        return '待完善'
      }
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

    formatDiaryMeta(diary) {
      if (diary.isDraft) {
        return `最近保存 ${this.formatDate(diary.updatedAt || diary.createdAt || diary.date)}`
      }
      return this.formatDate(diary.date)
    },
    
    formatDate(dateString) {
      if (!dateString) return '时间待定'
      const date = new Date(dateString)
      if (Number.isNaN(date.getTime())) return '时间待定'
      return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`
    },
    
    goToWriteDiary() {
      uni.navigateTo({
        url: '/pages/diary/edit'
      })
    },
    
    openDiary(diary) {
      if (diary.isDraft) {
        this.handleEdit(diary.id)
        return
      }
      uni.navigateTo({
        url: `/pages/diary/detail?id=${diary.id}`
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
            request({
              url: config.DIARY_DELETE.replace('<int:diary_id>', id),
              method: 'DELETE',
              header: {
                'Authorization': 'Bearer ' + this.token
              }
            }).then((resp) => {
              if (resp.msg === '删除成功') {
                uni.showToast({
                  title: '删除成功',
                  icon: 'success'
                })
                this.loadDiaryList()
              } else {
                uni.showToast({
                  title: resp.msg || '删除失败',
                  icon: 'none'
                })
              }
            }).catch(() => {
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
      const patchCover = (items) => {
        const index = items.findIndex((item) => item.id === diary.id)
        if (index !== -1) {
          items[index].coverImage = '/static/images/placeholder.svg'
          return true
        }
        return false
      }
      if (patchCover(this.publishedDiaries)) return
      patchCover(this.draftDiaries)
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

.view-switch {
  display: flex;
  gap: 16rpx;
  margin-bottom: 24rpx;
}

.view-tab {
  flex: 1;
  text-align: center;
  padding: 18rpx 0;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.82);
  color: #475569;
  font-size: 26rpx;
  box-shadow: 0 4rpx 12rpx rgba(15, 23, 42, 0.08);
}

.view-tab.active {
  background: linear-gradient(135deg, #0f766e 0%, #14b8a6 100%);
  color: #fff;
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

.diary-content {
  padding: 20rpx;
}

.diary-header {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 10rpx;
  margin-bottom: 15rpx;
}

.diary-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
}

.draft-badge {
  margin-left: auto;
  padding: 6rpx 16rpx;
  border-radius: 20rpx;
  font-size: 22rpx;
  background: rgba(249, 115, 22, 0.14);
  color: #c2410c;
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

.emotion-未设置 {
  background-color: #FDE68A;
  color: #92400E;
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
  transform: scale(1.1);
  box-shadow: 0 6rpx 25rpx rgba(0,122,255,0.4);
}

.plus-icon {
  font-size: 60rpx;
  color: white;
}
</style>

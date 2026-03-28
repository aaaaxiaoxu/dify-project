<template>
  <view class="container">
    <view class="profile-header">
      <view class="avatar-section">
        <view class="avatar-box" @click="chooseAvatar">
          <image
            v-if="userInfo.avatar_url"
            class="avatar-image"
            :src="userInfo.avatar_url"
            mode="aspectFill"
          />
          <view v-else class="avatar-placeholder">
            <text class="avatar-icon">👤</text>
          </view>
          <view class="avatar-mask">
            <text class="avatar-mask-text">{{ uploadingAvatar ? '上传中' : '更换头像' }}</text>
          </view>
        </view>
        <view class="user-info">
          <text class="username">{{ userInfo.nickname || userInfo.username }}</text>
          <text class="user-account">账号：{{ userInfo.username || '-' }}</text>
          <text class="user-desc">手机号：{{ userInfo.phone || '-' }}</text>
        </view>
      </view>
      
      <button class="edit-profile-btn" @click="openEditProfile">编辑资料</button>
    </view>

    <view class="intro-card">
      <text class="intro-label">个人简介</text>
      <text class="intro-content">{{ userInfo.bio || '还没有填写个人简介，点“编辑资料”补充一下。' }}</text>
    </view>
    
    <view class="stats-grid">
      <view class="stat-card">
        <text class="stat-value">{{ userStats.diaryCount }}</text>
        <text class="stat-label">篇日记</text>
      </view>
      <view class="stat-card">
        <text class="stat-value">{{ userStats.cityCount }}</text>
        <text class="stat-label">个城市</text>
      </view>
      <view class="stat-card">
        <text class="stat-value">{{ userStats.kmCount }}</text>
        <text class="stat-label">公里</text>
      </view>
    </view>
    
    <view class="menu-list">
      <view class="menu-item" @click="goToMyDiaries">
        <text class="menu-icon">📝</text>
        <text class="menu-text">我的日记</text>
        <text class="menu-arrow">></text>
      </view>
      
      <view class="menu-item" @click="goToTravelMap">
        <text class="menu-icon">🗺️</text>
        <text class="menu-text">旅行地图</text>
        <text class="menu-arrow">></text>
      </view>
      
      <view class="menu-item" @click="goToShareManage">
        <text class="menu-icon">🔗</text>
        <text class="menu-text">分享管理</text>
        <text class="menu-arrow">></text>
      </view>

      <view class="menu-item" @click="goToTravelReport">
        <text class="menu-icon">🧭</text>
        <text class="menu-text">智能旅行总结</text>
        <text class="menu-arrow">></text>
      </view>
      
      <view class="menu-item" @click="goToSettings">
        <text class="menu-icon">⚙️</text>
        <text class="menu-text">设置</text>
        <text class="menu-arrow">></text>
      </view>
      
      <view class="menu-item" @click="goToAbout">
        <text class="menu-icon">ℹ️</text>
        <text class="menu-text">关于我们</text>
        <text class="menu-arrow">></text>
      </view>
      
      <view class="menu-item admin-upgrade-item" @click="showAdminUpgrade" v-if="!isAdmin">
        <text class="menu-icon">🛡️</text>
        <text class="menu-text">升级成为管理员</text>
        <text class="menu-arrow">></text>
      </view>
      
      <view class="menu-item admin-badge-item" v-if="isAdmin">
        <text class="menu-icon">🛡️</text>
        <text class="menu-text">管理员身份已激活</text>
        <text class="admin-badge">✓</text>
      </view>
      
      <view class="menu-item logout-item" @click="logout">
        <text class="menu-icon">🚪</text>
        <text class="menu-text">退出登录</text>
        <text class="menu-arrow">></text>
      </view>
    </view>

    <view v-if="showEditPopup" class="popup-mask" @click="closeEditProfile">
      <view class="popup-card" @click.stop>
        <view class="popup-header">
          <text class="popup-title">编辑资料</text>
          <text class="popup-close" @click="closeEditProfile">×</text>
        </view>

        <view class="form-group">
          <text class="form-label">昵称</text>
          <input
            v-model.trim="editForm.nickname"
            class="form-input"
            type="text"
            maxlength="20"
            placeholder="请输入昵称"
          />
        </view>

        <view class="form-group">
          <text class="form-label">手机号</text>
          <input
            v-model.trim="editForm.phone"
            class="form-input"
            type="number"
            maxlength="20"
            placeholder="请输入手机号"
          />
        </view>

        <view class="form-group">
          <text class="form-label">个人简介</text>
          <textarea
            v-model="editForm.bio"
            class="form-textarea"
            maxlength="200"
            placeholder="介绍一下你喜欢的旅行方式、去过的地方，或者此刻想出发去哪里"
          />
        </view>

        <view class="popup-actions">
          <button class="popup-btn popup-btn-secondary" :disabled="savingProfile" @click="closeEditProfile">
            取消
          </button>
          <button class="popup-btn popup-btn-primary" :loading="savingProfile" @click="submitEditProfile">
            保存
          </button>
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
      userInfo: {
        username: 'traveler',
        nickname: '旅行者',
        avatar_url: '',
        bio: ''
      },
      userStats: {
        diaryCount: 0,
        cityCount: 0,
        kmCount: 0
      },
      isAdmin: false,
      showEditPopup: false,
      savingProfile: false,
      uploadingAvatar: false,
      editForm: {
        nickname: '',
        phone: '',
        bio: ''
      }
    }
  },
  
  onShow() {
    this.loadUserData()
    this.checkAdminStatus()
  },
  
  methods: {
    loadUserData() {
      const token = this.$store && this.$store.state ? this.$store.state.token : ''
      
      if (!token) {
        console.log('用户未登录')
        return
      }
      
      // 获取用户信息
      request({
        url: config.USER_PROFILE,
        method: 'GET',
        header: {
          'Authorization': 'Bearer ' + token
        }
      }).then(res => {
        this.userInfo = res
        this.$store.commit('SET_USER_INFO', res)
      }).catch(err => {
        console.error('获取用户信息失败:', err)
      })
      
      // 获取统计数据
      request({
        url: config.MAP_STATS,
        method: 'GET',
        header: {
          'Authorization': 'Bearer ' + token
        }
      }).then(res => {
        this.userStats.diaryCount =
          res.diary_count != null ? res.diary_count : 0
        this.userStats.cityCount = res.city_count
        this.userStats.kmCount = res.km_count
      }).catch(err => {
        console.error('获取统计数据失败:', err)
      })
    },

    openEditProfile() {
      const token = this.$store && this.$store.state ? this.$store.state.token : ''
      if (!token) {
        uni.showToast({ title: '请先登录', icon: 'none' })
        return
      }

      this.editForm.nickname = this.userInfo.nickname || ''
      this.editForm.phone = this.userInfo.phone || ''
      this.editForm.bio = this.userInfo.bio || ''
      this.showEditPopup = true
    },

    closeEditProfile() {
      if (this.savingProfile) return
      this.showEditPopup = false
    },

    chooseAvatar() {
      const token = this.$store && this.$store.state ? this.$store.state.token : ''
      if (!token) {
        uni.showToast({ title: '请先登录', icon: 'none' })
        return
      }
      if (this.uploadingAvatar) return

      uni.chooseImage({
        count: 1,
        sizeType: ['compressed'],
        sourceType: ['album', 'camera'],
        success: (res) => {
          const filePath = res.tempFilePaths && res.tempFilePaths[0]
          if (!filePath) return
          this.uploadAvatar(filePath)
        }
      })
    },

    uploadAvatar(filePath) {
      const token = this.$store && this.$store.state ? this.$store.state.token : ''
      if (!token) {
        uni.showToast({ title: '请先登录', icon: 'none' })
        return
      }

      this.uploadingAvatar = true
      uni.showLoading({
        title: '上传头像中',
        mask: true
      })

      uni.uploadFile({
        url: config.FILE_UPLOAD,
        filePath,
        name: 'file',
        formData: {
          media_type: 'image'
        },
        header: {
          Authorization: 'Bearer ' + token
        },
        success: (res) => {
          try {
            const body = typeof res.data === 'string' ? JSON.parse(res.data) : res.data
            if (body && body.url) {
              this.saveAvatarUrl(body.url)
              return
            }
            throw new Error((body && body.msg) || '头像上传失败')
          } catch (err) {
            uni.hideLoading()
            this.uploadingAvatar = false
            uni.showToast({
              title: err.message || '头像上传失败',
              icon: 'none'
            })
          }
        },
        fail: (err) => {
          uni.hideLoading()
          this.uploadingAvatar = false
          uni.showToast({
            title: (err && err.errMsg) || '头像上传失败',
            icon: 'none'
          })
        }
      })
    },

    saveAvatarUrl(avatarUrl) {
      const token = this.$store && this.$store.state ? this.$store.state.token : ''
      request({
        url: config.USER_PROFILE,
        method: 'PUT',
        header: {
          'Authorization': 'Bearer ' + token
        },
        data: {
          avatar_url: avatarUrl
        }
      }).then(res => {
        const nextUserInfo = res.user || {
          ...this.userInfo,
          avatar_url: avatarUrl
        }
        this.userInfo = nextUserInfo
        this.$store.commit('SET_USER_INFO', nextUserInfo)
        uni.showToast({
          title: '头像更新成功',
          icon: 'success'
        })
      }).catch(err => {
        const msg = (err.data && err.data.msg) ? err.data.msg : '头像保存失败'
        uni.showToast({
          title: msg,
          icon: 'none'
        })
      }).finally(() => {
        uni.hideLoading()
        this.uploadingAvatar = false
      })
    },

    submitEditProfile() {
      const token = this.$store && this.$store.state ? this.$store.state.token : ''
      const nickname = (this.editForm.nickname || '').trim()
      const phone = String(this.editForm.phone || '').trim()
      const bio = (this.editForm.bio || '').trim()

      if (!token) {
        uni.showToast({ title: '请先登录', icon: 'none' })
        return
      }

      if (!nickname) {
        uni.showToast({ title: '请输入昵称', icon: 'none' })
        return
      }

      if (!phone) {
        uni.showToast({ title: '请输入手机号', icon: 'none' })
        return
      }

      this.savingProfile = true

      request({
        url: config.USER_PROFILE,
        method: 'PUT',
        header: {
          'Authorization': 'Bearer ' + token
        },
        data: {
          nickname,
          phone,
          avatar_url: this.userInfo.avatar_url || '',
          bio
        }
      }).then(res => {
        const nextUserInfo = res.user || {
          ...this.userInfo,
          nickname,
          phone,
          bio
        }

        this.userInfo = nextUserInfo
        this.$store.commit('SET_USER_INFO', nextUserInfo)
        this.showEditPopup = false
        uni.showToast({
          title: res.msg || '保存成功',
          icon: 'success'
        })
      }).catch(err => {
        const msg = (err.data && err.data.msg) ? err.data.msg : '保存失败，请稍后重试'
        uni.showToast({
          title: msg,
          icon: 'none'
        })
      }).finally(() => {
        this.savingProfile = false
      })
    },
    
    goToMyDiaries() {
      uni.switchTab({
        url: '/pages/diary/list'
      })
    },
    
    goToTravelMap() {
      uni.switchTab({
        url: '/pages/map/map'
      })
    },
    
    goToShareManage() {
      uni.navigateTo({
        url: '/pages/share/manage'
      })
    },

    goToTravelReport() {
      uni.navigateTo({
        url: '/pages/report/report'
      })
    },
    
    goToSettings() {
      uni.showToast({
        title: '功能开发中',
        icon: 'none'
      })
    },
    
    goToAbout() {
      uni.navigateTo({
        url: '/pages/profile/disclaimer'
      })
    },
    
    checkAdminStatus() {
      const token = this.$store && this.$store.state ? this.$store.state.token : ''
      if (!token) return
      
      request({
        url: config.ADMIN_CHECK,
        method: 'GET',
        header: {
          'Authorization': 'Bearer ' + token
        }
      }).then(res => {
        this.isAdmin = res.is_admin
        this.$store.commit('SET_IS_ADMIN', res.is_admin)
      }).catch(err => {
        console.error('检查管理员状态失败:', err)
      })
    },
    
    showAdminUpgrade() {
      uni.showModal({
        title: '升级成为管理员',
        content: '',
        editable: true,
        placeholderText: '请输入管理员密钥',
        success: (res) => {
          if (res.confirm && res.content) {
            this.doAdminUpgrade(res.content.trim())
          }
        }
      })
    },
    
    doAdminUpgrade(secretKey) {
      const token = this.$store && this.$store.state ? this.$store.state.token : ''
      if (!token) {
        uni.showToast({ title: '请先登录', icon: 'none' })
        return
      }
      
      request({
        url: config.ADMIN_UPGRADE,
        method: 'POST',
        header: {
          'Authorization': 'Bearer ' + token
        },
        data: { secret_key: secretKey }
      }).then(res => {
        uni.showToast({ title: res.msg || '升级成功', icon: 'success' })
        this.isAdmin = true
        this.$store.commit('SET_IS_ADMIN', true)
      }).catch(err => {
        const msg = (err.data && err.data.msg) ? err.data.msg : '密钥错误'
        uni.showToast({ title: msg, icon: 'none' })
      })
    },
    
    logout() {
      uni.showModal({
        title: '确认退出',
        content: '确定要退出登录吗？',
        success: (res) => {
          if (res.confirm) {
            // 清除用户信息
            this.$store.commit('SET_TOKEN', '')
            this.$store.commit('SET_USER_INFO', null)
            this.$store.commit('SET_IS_ADMIN', false)
            
            uni.showToast({
              title: '已退出登录',
              icon: 'success'
            })
            
            // 跳转到登录页
            setTimeout(() => {
              uni.redirectTo({
                url: '/pages/login/login'
              })
            }, 1500)
          }
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

.profile-header {
  background: #fff;
  border-radius: 20rpx;
  padding: 40rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.05);
}

.avatar-section {
  display: flex;
  align-items: center;
}

.avatar-box {
  width: 120rpx;
  height: 120rpx;
  margin-right: 30rpx;
  position: relative;
}

.avatar-image,
.avatar-placeholder {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #c9d6ff 0%, #e2e2e2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 3rpx solid #007AFF;
  overflow: hidden;
}

.avatar-icon {
  font-size: 60rpx;
}

.avatar-mask {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 34rpx;
  border-bottom-left-radius: 60rpx;
  border-bottom-right-radius: 60rpx;
  background: rgba(15, 23, 42, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-mask-text {
  font-size: 18rpx;
  color: #fff;
}

.user-info {
  display: flex;
  flex-direction: column;
}

.username {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 10rpx;
}

.user-account {
  font-size: 24rpx;
  color: #6b7280;
  margin-bottom: 8rpx;
}

.user-desc {
  font-size: 26rpx;
  color: #666;
}

.edit-profile-btn {
  padding: 15rpx 30rpx;
  background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
  color: white;
  border: none;
  border-radius: 10rpx;
  font-size: 26rpx;
  box-shadow: 0 4rpx 10rpx rgba(106,17,203,0.3);
  transition: all 0.3s ease;
}

.edit-profile-btn::after {
  border: none;
}

.edit-profile-btn:hover {
  transform: translateY(-2rpx);
  box-shadow: 0 6rpx 15rpx rgba(106,17,203,0.4);
}

.intro-card {
  background: #fff;
  border-radius: 20rpx;
  padding: 28rpx 32rpx;
  margin-bottom: 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.05);
}

.intro-label {
  display: block;
  font-size: 24rpx;
  color: #94a3b8;
  margin-bottom: 12rpx;
}

.intro-content {
  display: block;
  font-size: 28rpx;
  line-height: 1.7;
  color: #334155;
}

.stats-grid {
  display: flex;
  justify-content: space-between;
  margin-bottom: 30rpx;
}

.stat-card {
  flex: 1;
  background: #fff;
  border-radius: 20rpx;
  padding: 30rpx;
  text-align: center;
  margin: 0 10rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.05);
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5rpx);
  box-shadow: 0 8rpx 25rpx rgba(0,0,0,0.1);
}

.stat-value {
  display: block;
  font-size: 40rpx;
  font-weight: bold;
  color: #007AFF;
  margin-bottom: 10rpx;
}

.stat-label {
  font-size: 24rpx;
  color: #999;
}

.menu-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 30rpx;
  background: #fff;
  border-radius: 20rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.05);
  transition: all 0.3s ease;
}

.menu-item:hover {
  transform: translateX(10rpx);
  box-shadow: 0 6rpx 25rpx rgba(0,0,0,0.1);
}

.menu-icon {
  font-size: 40rpx;
  margin-right: 20rpx;
}

.menu-text {
  flex: 1;
  font-size: 30rpx;
  color: #333;
}

.menu-arrow {
  color: #ccc;
  font-size: 30rpx;
}

.logout-item {
  background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
  color: white;
}

.logout-item .menu-text {
  color: white;
}

.admin-upgrade-item {
  background: linear-gradient(135deg, #f5f0ff 0%, #ede7ff 100%);
  border: 1rpx solid #d4c5f9;
}

.admin-upgrade-item .menu-text {
  color: #6a11cb;
  font-weight: 500;
}

.admin-badge-item {
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
  border: 1rpx solid #a5d6a7;
}

.admin-badge-item .menu-text {
  color: #2e7d32;
  font-weight: 500;
}

.admin-badge {
  color: #2e7d32;
  font-size: 32rpx;
  font-weight: bold;
}

.popup-mask {
  position: fixed;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32rpx;
  z-index: 999;
  box-sizing: border-box;
}

.popup-card {
  width: 100%;
  background: #fff;
  border-radius: 24rpx;
  padding: 32rpx;
  box-sizing: border-box;
  box-shadow: 0 20rpx 60rpx rgba(15, 23, 42, 0.18);
}

.popup-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 28rpx;
}

.popup-title {
  font-size: 34rpx;
  font-weight: 600;
  color: #1f2937;
}

.popup-close {
  font-size: 40rpx;
  color: #94a3b8;
  line-height: 1;
}

.form-group {
  margin-bottom: 24rpx;
}

.form-label {
  display: block;
  margin-bottom: 12rpx;
  font-size: 26rpx;
  color: #475569;
}

.form-input {
  width: 100%;
  height: 88rpx;
  padding: 0 24rpx;
  background: #f8fafc;
  border: 2rpx solid #e2e8f0;
  border-radius: 16rpx;
  font-size: 28rpx;
  color: #1f2937;
  box-sizing: border-box;
}

.form-textarea {
  width: 100%;
  min-height: 180rpx;
  padding: 24rpx;
  background: #f8fafc;
  border: 2rpx solid #e2e8f0;
  border-radius: 16rpx;
  font-size: 28rpx;
  line-height: 1.6;
  color: #1f2937;
  box-sizing: border-box;
}

.popup-actions {
  display: flex;
  gap: 20rpx;
  margin-top: 32rpx;
}

.popup-btn {
  flex: 1;
  height: 88rpx;
  border-radius: 16rpx;
  font-size: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.popup-btn::after {
  border: none;
}

.popup-btn-secondary {
  background: #eef2ff;
  color: #475569;
}

.popup-btn-primary {
  background: linear-gradient(135deg, #2563eb 0%, #0ea5e9 100%);
  color: #fff;
}
</style>

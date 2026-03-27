<template>
  <view class="container">
    <view class="profile-header">
      <view class="avatar-section">
        <view class="avatar-placeholder">
          <text class="avatar-icon">👤</text>
        </view>
        <view class="user-info">
          <text class="username">{{ userInfo.nickname || userInfo.username }}</text>
          <text class="user-desc">✈️ 旅行爱好者</text>
        </view>
      </view>
      
      <button class="edit-profile-btn">编辑资料</button>
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
        nickname: '旅行者'
      },
      userStats: {
        diaryCount: 0,
        cityCount: 0,
        kmCount: 0
      },
      isAdmin: false
    }
  },
  
  onLoad() {
    this.loadUserData()
  },
  
  onShow() {
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

.avatar-placeholder {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  margin-right: 30rpx;
  background: linear-gradient(135deg, #c9d6ff 0%, #e2e2e2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 3rpx solid #007AFF;
}

.avatar-icon {
  font-size: 60rpx;
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

.edit-profile-btn:hover {
  transform: translateY(-2rpx);
  box-shadow: 0 6rpx 15rpx rgba(106,17,203,0.4);
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
</style>

<template>
  <view class="container">
    <view class="loading-tip" v-if="authChecking">
      <text>校验权限中...</text>
    </view>

    <view class="admin-panel" v-else-if="isAdmin">
      <!-- 顶部 Tab 切换 -->
      <view class="tab-bar">
        <view 
          class="tab-item" 
          :class="{ active: currentTab === 'users' }" 
          @click="switchTab('users')"
        >
          <text>管理用户</text>
        </view>
        <view 
          class="tab-item" 
          :class="{ active: currentTab === 'diaries' }" 
          @click="switchTab('diaries')"
        >
          <text>管理日记</text>
        </view>
      </view>
      
      <!-- 搜索栏 -->
      <view class="search-bar">
        <input 
          class="search-input" 
          :placeholder="currentTab === 'users' ? '搜索用户名/昵称/手机号' : '搜索标题/地点/内容'" 
          v-model="keyword"
          @confirm="doSearch"
        />
        <button class="search-btn" @click="doSearch">搜索</button>
      </view>
      
      <!-- 用户管理 -->
      <view class="list-content" v-if="currentTab === 'users'">
        <view class="empty-tip" v-if="userList.length === 0 && !loading">
          <text>暂无用户数据</text>
        </view>
        
        <view class="user-card" v-for="user in userList" :key="user.id">
          <view class="card-header">
            <view class="user-avatar">
              <image class="user-avatar-image" :src="getAvatarUrl(user.avatar_url)" mode="aspectFill"></image>
            </view>
            <view class="user-main-info">
              <text class="user-nickname">{{ user.nickname }}</text>
              <text class="user-username">@{{ user.username }}</text>
            </view>
            <view class="user-badges">
              <text class="badge badge-admin" v-if="user.is_admin">管理员</text>
              <text class="badge badge-frozen" v-if="user.is_frozen">已冻结</text>
            </view>
          </view>
          <view class="card-body">
            <view class="info-row">
              <text class="info-label">手机号:</text>
              <text class="info-value">{{ user.phone }}</text>
            </view>
            <view class="info-row">
              <text class="info-label">日记数:</text>
              <text class="info-value">{{ user.diary_count }} 篇</text>
            </view>
            <view class="info-row">
              <text class="info-label">注册时间:</text>
              <text class="info-value">{{ user.created_at }}</text>
            </view>
          </view>
          <view class="card-actions">
            <button 
              class="action-btn" 
              :class="user.is_frozen ? 'unfreeze-btn' : 'freeze-btn'"
              @click="toggleFreeze(user)"
              :disabled="user.is_admin"
            >
              {{ user.is_frozen ? '解冻' : '冻结' }}
            </button>
          </view>
        </view>
        
        <!-- 分页 -->
        <view class="pagination" v-if="totalPages > 1">
          <button class="page-btn" :disabled="currentPage <= 1" @click="changePage(currentPage - 1)">上一页</button>
          <text class="page-info">{{ currentPage }} / {{ totalPages }}</text>
          <button class="page-btn" :disabled="currentPage >= totalPages" @click="changePage(currentPage + 1)">下一页</button>
        </view>
      </view>
      
      <!-- 日记管理 -->
      <view class="list-content" v-if="currentTab === 'diaries'">
        <view class="empty-tip" v-if="diaryList.length === 0 && !loading">
          <text>暂无日记数据</text>
        </view>
        
        <view class="diary-card" v-for="diary in diaryList" :key="diary.id">
          <view class="card-header">
            <view class="diary-title-row">
              <text class="diary-title">{{ diary.title }}</text>
              <text class="badge badge-draft" v-if="diary.is_draft">草稿</text>
            </view>
          </view>
          <view class="card-body">
            <view class="info-row">
              <text class="info-label">作者:</text>
              <text class="info-value">{{ diary.author_name }} (@{{ diary.author_username }})</text>
            </view>
            <view class="info-row">
              <text class="info-label">地点:</text>
              <text class="info-value">{{ diary.location }}</text>
            </view>
            <view class="info-row">
              <text class="info-label">日期:</text>
              <text class="info-value">{{ diary.date }}</text>
            </view>
            <view class="info-row">
              <text class="info-label">情绪:</text>
              <text class="info-value">{{ diary.emotion }}</text>
            </view>
            <view class="info-row">
              <text class="info-label">图片:</text>
              <text class="info-value">{{ diary.image_count }} 张</text>
            </view>
            <view class="diary-content-preview">
              <text class="content-text">{{ diary.content }}</text>
            </view>
          </view>
          <view class="card-actions">
            <button class="action-btn delete-btn" @click="deleteDiary(diary)">删除</button>
          </view>
        </view>
        
        <!-- 分页 -->
        <view class="pagination" v-if="diaryTotalPages > 1">
          <button class="page-btn" :disabled="diaryCurrentPage <= 1" @click="changeDiaryPage(diaryCurrentPage - 1)">上一页</button>
          <text class="page-info">{{ diaryCurrentPage }} / {{ diaryTotalPages }}</text>
          <button class="page-btn" :disabled="diaryCurrentPage >= diaryTotalPages" @click="changeDiaryPage(diaryCurrentPage + 1)">下一页</button>
        </view>
      </view>
      
      <!-- 加载中 -->
      <view class="loading-tip" v-if="loading">
        <text>加载中...</text>
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
      authChecking: true,
      isAdmin: false,
      currentTab: 'users',
      keyword: '',
      loading: false,
      defaultAvatar: '/static/images/default-avatar.svg',
      
      // 用户管理
      userList: [],
      currentPage: 1,
      totalPages: 1,
      
      // 日记管理
      diaryList: [],
      diaryCurrentPage: 1,
      diaryTotalPages: 1
    }
  },
  
  onShow() {
    this.checkAdmin()
  },
  
  methods: {
    getAvatarUrl(avatarUrl) {
      return avatarUrl || this.defaultAvatar
    },

    getToken() {
      return this.$store && this.$store.state ? this.$store.state.token : ''
    },
    
    checkAdmin() {
      const token = this.getToken()
      if (!token) {
        this.isAdmin = false
        this.authChecking = false
        this.$store.commit('SET_IS_ADMIN', false)
        uni.redirectTo({
          url: '/pages/login/login'
        })
        return
      }

      this.authChecking = true
      
      request({
        url: config.ADMIN_CHECK,
        method: 'GET',
        header: { 'Authorization': 'Bearer ' + token }
      }).then(res => {
        const isAdmin = !!(res && res.is_admin)
        this.isAdmin = isAdmin
        this.authChecking = false
        this.$store.commit('SET_IS_ADMIN', isAdmin)
        if (!isAdmin) {
          this.redirectNoPermission()
          return
        }
        this.loadData()
      }).catch(err => {
        console.error('检查管理员状态失败:', err)
        this.isAdmin = false
        this.authChecking = false
        this.$store.commit('SET_IS_ADMIN', false)
        this.redirectNoPermission()
      })
    },

    redirectNoPermission() {
      uni.showToast({
        title: '无权限访问',
        icon: 'none'
      })
      setTimeout(() => {
        uni.switchTab({
          url: '/pages/profile/profile'
        })
      }, 300)
    },
    
    switchTab(tab) {
      this.currentTab = tab
      this.keyword = ''
      this.loadData()
    },
    
    doSearch() {
      if (this.currentTab === 'users') {
        this.currentPage = 1
      } else {
        this.diaryCurrentPage = 1
      }
      this.loadData()
    },
    
    loadData() {
      if (this.currentTab === 'users') {
        this.loadUsers()
      } else {
        this.loadDiaries()
      }
    },
    
    loadUsers() {
      const token = this.getToken()
      if (!token) return
      
      this.loading = true
      request({
        url: config.ADMIN_USERS + '?page=' + this.currentPage + '&per_page=20&keyword=' + encodeURIComponent(this.keyword),
        method: 'GET',
        header: { 'Authorization': 'Bearer ' + token }
      }).then(res => {
        this.userList = res.users || []
        this.totalPages = res.pages || 1
        this.loading = false
      }).catch(err => {
        console.error('获取用户列表失败:', err)
        this.loading = false
        uni.showToast({ title: '获取用户列表失败', icon: 'none' })
      })
    },
    
    loadDiaries() {
      const token = this.getToken()
      if (!token) return
      
      this.loading = true
      request({
        url: config.ADMIN_DIARIES + '?page=' + this.diaryCurrentPage + '&per_page=20&keyword=' + encodeURIComponent(this.keyword),
        method: 'GET',
        header: { 'Authorization': 'Bearer ' + token }
      }).then(res => {
        this.diaryList = res.diaries || []
        this.diaryTotalPages = res.pages || 1
        this.loading = false
      }).catch(err => {
        console.error('获取日记列表失败:', err)
        this.loading = false
        uni.showToast({ title: '获取日记列表失败', icon: 'none' })
      })
    },
    
    toggleFreeze(user) {
      if (user.is_admin) {
        uni.showToast({ title: '不能冻结管理员', icon: 'none' })
        return
      }
      
      const action = user.is_frozen ? '解冻' : '冻结'
      uni.showModal({
        title: '确认操作',
        content: `确定要${action}用户 "${user.nickname}" 吗？`,
        success: (res) => {
          if (res.confirm) {
            const token = this.getToken()
            request({
              url: config.ADMIN_FREEZE_USER + user.id + '/freeze',
              method: 'POST',
              header: { 'Authorization': 'Bearer ' + token }
            }).then(res => {
              uni.showToast({ title: res.msg || '操作成功', icon: 'success' })
              user.is_frozen = res.is_frozen
            }).catch(err => {
              const msg = (err.data && err.data.msg) ? err.data.msg : '操作失败'
              uni.showToast({ title: msg, icon: 'none' })
            })
          }
        }
      })
    },
    
    deleteDiary(diary) {
      uni.showModal({
        title: '确认删除',
        content: `确定要删除日记「${diary.title}」吗？此操作不可恢复。`,
        success: (res) => {
          if (res.confirm) {
            const token = this.getToken()
            request({
              url: config.ADMIN_DELETE_DIARY + diary.id,
              method: 'DELETE',
              header: { 'Authorization': 'Bearer ' + token }
            }).then(res => {
              uni.showToast({ title: res.msg || '删除成功', icon: 'success' })
              this.loadDiaries()
            }).catch(err => {
              const msg = (err.data && err.data.msg) ? err.data.msg : '删除失败'
              uni.showToast({ title: msg, icon: 'none' })
            })
          }
        }
      })
    },
    
    changePage(page) {
      this.currentPage = page
      this.loadUsers()
    },
    
    changeDiaryPage(page) {
      this.diaryCurrentPage = page
      this.loadDiaries()
    }
  }
}
</script>

<style scoped>
.container {
  padding: 20rpx;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4edf9 100%);
  min-height: 100vh;
}

/* Tab 栏 */
.tab-bar {
  display: flex;
  background: #fff;
  border-radius: 16rpx;
  overflow: hidden;
  margin-bottom: 20rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.05);
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: 24rpx 0;
  font-size: 30rpx;
  color: #666;
  transition: all 0.3s;
}

.tab-item.active {
  color: #fff;
  background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
  font-weight: bold;
}

/* 搜索栏 */
.search-bar {
  display: flex;
  gap: 16rpx;
  margin-bottom: 20rpx;
}

.search-input {
  flex: 1;
  background: #fff;
  border-radius: 16rpx;
  padding: 18rpx 24rpx;
  font-size: 28rpx;
  box-shadow: 0 2rpx 10rpx rgba(0,0,0,0.05);
}

.search-btn {
  padding: 18rpx 32rpx;
  background: #007AFF;
  color: #fff;
  border: none;
  border-radius: 16rpx;
  font-size: 28rpx;
}

/* 卡片通用样式 */
.user-card, .diary-card {
  background: #fff;
  border-radius: 16rpx;
  margin-bottom: 20rpx;
  padding: 24rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.05);
}

.card-header {
  display: flex;
  align-items: center;
  margin-bottom: 16rpx;
  padding-bottom: 16rpx;
  border-bottom: 1rpx solid #f0f0f0;
}

.user-avatar {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  margin-right: 20rpx;
  overflow: hidden;
}

.user-avatar-image {
  width: 100%;
  height: 100%;
  display: block;
}

.user-main-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.user-nickname {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
}

.user-username {
  font-size: 24rpx;
  color: #999;
  margin-top: 4rpx;
}

.user-badges {
  display: flex;
  gap: 10rpx;
}

.badge {
  padding: 6rpx 16rpx;
  border-radius: 20rpx;
  font-size: 22rpx;
  font-weight: 500;
}

.badge-admin {
  background: #e8f5e9;
  color: #2e7d32;
}

.badge-frozen {
  background: #fbe9e7;
  color: #d32f2f;
}

.badge-draft {
  background: #fff3e0;
  color: #e65100;
}

.card-body {
  margin-bottom: 16rpx;
}

.info-row {
  display: flex;
  margin-bottom: 8rpx;
}

.info-label {
  font-size: 26rpx;
  color: #999;
  width: 140rpx;
}

.info-value {
  font-size: 26rpx;
  color: #333;
  flex: 1;
}

/* 日记标题行 */
.diary-title-row {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.diary-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
}

.diary-content-preview {
  background: #f8f8f8;
  border-radius: 10rpx;
  padding: 16rpx;
  margin-top: 12rpx;
}

.content-text {
  font-size: 24rpx;
  color: #666;
  line-height: 1.6;
}

/* 操作按钮 */
.card-actions {
  display: flex;
  justify-content: flex-end;
  gap: 16rpx;
  padding-top: 16rpx;
  border-top: 1rpx solid #f0f0f0;
}

.action-btn {
  padding: 12rpx 36rpx;
  border: none;
  border-radius: 10rpx;
  font-size: 26rpx;
  color: #fff;
}

.freeze-btn {
  background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
}

.unfreeze-btn {
  background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%);
}

.delete-btn {
  background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
}

.action-btn[disabled] {
  opacity: 0.4;
}

/* 分页 */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20rpx;
  padding: 30rpx 0;
}

.page-btn {
  padding: 14rpx 30rpx;
  background: #007AFF;
  color: #fff;
  border: none;
  border-radius: 10rpx;
  font-size: 26rpx;
}

.page-btn[disabled] {
  background: #ccc;
  color: #999;
}

.page-info {
  font-size: 28rpx;
  color: #666;
}

/* 空提示 */
.empty-tip {
  text-align: center;
  padding: 80rpx 0;
  color: #999;
  font-size: 28rpx;
}

/* 加载中 */
.loading-tip {
  text-align: center;
  padding: 40rpx 0;
  color: #999;
  font-size: 28rpx;
}
</style>

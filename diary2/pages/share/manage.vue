<template>
  <view class="container">
    <view class="page-header">
      <text class="page-title">分享管理</text>
      <text class="page-desc">管理你创建的所有分享链接</text>
    </view>

    <!-- 空状态 -->
    <view class="empty-state" v-if="!loading && shareList.length === 0">
      <text class="empty-icon">🔗</text>
      <text class="empty-text">暂无分享链接</text>
      <text class="empty-sub">在日记详情页点击"生成分享链接"即可创建</text>
    </view>

    <!-- 分享列表 -->
    <view class="share-list" v-if="shareList.length > 0">
      <view
        class="share-card"
        v-for="(item, index) in shareList"
        :key="item.id"
        @click="toggleDetail(index)"
      >
        <view class="card-top">
          <view class="card-info">
            <text class="card-title">{{ item.diary_title }}</text>
            <text class="card-time">{{ formatTime(item.created_at) }}</text>
          </view>
          <view class="status-badge" :class="'status-' + item.status">
            <text>{{ statusLabel(item.status) }}</text>
          </view>
        </view>

        <view class="card-stats">
          <view class="stat-item">
            <text class="stat-num">{{ item.view_count }}</text>
            <text class="stat-label">次访问</text>
          </view>
          <view class="stat-item" v-if="item.view_limit">
            <text class="stat-num">{{ item.view_limit }}</text>
            <text class="stat-label">次上限</text>
          </view>
          <view class="stat-item">
            <text class="stat-num">{{ item.has_password ? '已设置' : '公开' }}</text>
            <text class="stat-label">密码</text>
          </view>
          <view class="stat-item">
            <text class="stat-num">{{ item.expire_time ? item.expire_time.slice(0, 10) : '永久' }}</text>
            <text class="stat-label">有效期</text>
          </view>
        </view>

        <!-- 展开的详情 -->
        <view class="card-detail" v-if="expandedIndex === index">
          <!-- 访问趋势 -->
          <view class="chart-section" v-if="detailStats && detailStats.daily_views && detailStats.daily_views.length > 0">
            <text class="detail-label">近期访问趋势</text>
            <view class="bar-chart">
              <view
                class="bar-item"
                v-for="(dv, di) in detailStats.daily_views"
                :key="di"
              >
                <view class="bar-fill" :style="{ height: barHeight(dv.count) + 'rpx' }"></view>
                <text class="bar-date">{{ dv.date }}</text>
              </view>
            </view>
          </view>
          <view class="chart-section" v-else>
            <text class="detail-label">暂无访问记录</text>
          </view>

          <!-- 操作按钮 -->
          <view class="detail-actions">
            <button class="action-copy" @click.stop="copyLink(item.token)">复制链接</button>
            <button
              class="action-revoke"
              v-if="item.status === 'active'"
              @click.stop="revokeShare(item.id, index)"
            >撤销分享</button>
            <button
              class="action-delete"
              @click.stop="deleteShare(item.id, index)"
            >删除</button>
          </view>
        </view>
      </view>
    </view>

    <!-- 加载中 -->
    <view class="loading-state" v-if="loading">
      <text class="loading-text">加载中...</text>
    </view>
  </view>
</template>

<script>
import request from '../../utils/request.js'
import config from '../../api/config.js'

export default {
  data() {
    return {
      shareList: [],
      loading: false,
      expandedIndex: -1,
      detailStats: null
    }
  },

  onLoad() {
    this.fetchList()
  },

  onPullDownRefresh() {
    this.fetchList().then(() => uni.stopPullDownRefresh())
  },

  methods: {
    fetchList() {
      this.loading = true
      return request({
        url: config.SHARE_LIST,
        method: 'GET',
        header: { 'Authorization': 'Bearer ' + this.$store.state.token }
      }).then(res => {
        this.shareList = Array.isArray(res) ? res : []
      }).catch(() => {
        uni.showToast({ title: '加载失败', icon: 'none' })
      }).finally(() => {
        this.loading = false
      })
    },

    toggleDetail(index) {
      if (this.expandedIndex === index) {
        this.expandedIndex = -1
        this.detailStats = null
        return
      }
      this.expandedIndex = index
      this.loadStats(this.shareList[index].id)
    },

    loadStats(shareId) {
      this.detailStats = null
      request({
        url: config.SHARE_STATS + shareId,
        method: 'GET',
        header: { 'Authorization': 'Bearer ' + this.$store.state.token }
      }).then(res => {
        this.detailStats = res
      })
    },

    revokeShare(shareId, index) {
      uni.showModal({
        title: '确认撤销',
        content: '撤销后此分享链接将无法访问，确定吗？',
        success: (res) => {
          if (!res.confirm) return
          request({
            url: config.SHARE_REVOKE + shareId,
            method: 'POST',
            header: { 'Authorization': 'Bearer ' + this.$store.state.token }
          }).then(() => {
            this.shareList[index].status = 'revoked'
            this.shareList[index].is_active = false
            uni.showToast({ title: '已撤销', icon: 'success' })
          }).catch(() => {
            uni.showToast({ title: '撤销失败', icon: 'none' })
          })
        }
      })
    },

    copyLink(token) {
      const link = config.SHARE_PAGE + token
      uni.setClipboardData({
        data: link,
        success: () => uni.showToast({ title: '已复制', icon: 'success' })
      })
    },

    deleteShare(shareId, index) {
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
            this.shareList.splice(index, 1)
            this.expandedIndex = -1
            uni.showToast({ title: '已删除', icon: 'success' })
          }).catch(() => {
            uni.showToast({ title: '删除失败', icon: 'none' })
          })
        }
      })
    },

    barHeight(count) {
      if (!this.detailStats || !this.detailStats.daily_views) return 0
      const max = Math.max(...this.detailStats.daily_views.map(d => d.count), 1)
      return Math.round((count / max) * 120)
    },

    statusLabel(status) {
      const map = {
        active: '有效',
        expired: '已过期',
        revoked: '已撤销',
        limit_reached: '次数已满'
      }
      return map[status] || status
    },

    formatTime(iso) {
      if (!iso) return ''
      return iso.slice(0, 16).replace('T', ' ')
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

.page-header {
  margin-bottom: 30rpx;
}

.page-title {
  display: block;
  font-size: 40rpx;
  font-weight: bold;
  color: #333;
}

.page-desc {
  display: block;
  font-size: 24rpx;
  color: #999;
  margin-top: 8rpx;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 120rpx 0;
}

.empty-icon {
  font-size: 80rpx;
  margin-bottom: 20rpx;
}

.empty-text {
  font-size: 32rpx;
  color: #999;
}

.empty-sub {
  font-size: 24rpx;
  color: #bbb;
  margin-top: 10rpx;
}

/* 卡片列表 */
.share-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.share-card {
  background: #fff;
  border-radius: 20rpx;
  padding: 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20rpx;
}

.card-info {
  flex: 1;
}

.card-title {
  display: block;
  font-size: 30rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 6rpx;
}

.card-time {
  font-size: 22rpx;
  color: #bbb;
}

.status-badge {
  padding: 6rpx 18rpx;
  border-radius: 20rpx;
  font-size: 22rpx;
}

.status-active {
  background: #e8f5e9;
  color: #43a047;
}

.status-expired {
  background: #fff3e0;
  color: #ef6c00;
}

.status-revoked {
  background: #fce4ec;
  color: #e53935;
}

.status-limit_reached {
  background: #ede7f6;
  color: #5e35b1;
}

/* 统计行 */
.card-stats {
  display: flex;
  justify-content: space-between;
}

.stat-item {
  text-align: center;
  flex: 1;
}

.stat-num {
  display: block;
  font-size: 28rpx;
  font-weight: bold;
  color: #007AFF;
}

.stat-label {
  display: block;
  font-size: 20rpx;
  color: #999;
  margin-top: 4rpx;
}

/* 展开详情 */
.card-detail {
  margin-top: 24rpx;
  padding-top: 24rpx;
  border-top: 1rpx solid #f0f0f0;
}

.chart-section {
  margin-bottom: 24rpx;
}

.detail-label {
  display: block;
  font-size: 24rpx;
  color: #999;
  margin-bottom: 16rpx;
}

/* 简易柱状图 */
.bar-chart {
  display: flex;
  align-items: flex-end;
  height: 150rpx;
  gap: 12rpx;
}

.bar-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
}

.bar-fill {
  width: 100%;
  min-height: 8rpx;
  background: linear-gradient(180deg, #007AFF 0%, #00d4ff 100%);
  border-radius: 6rpx 6rpx 0 0;
  transition: height 0.3s ease;
}

.bar-date {
  font-size: 18rpx;
  color: #bbb;
  margin-top: 6rpx;
}

/* 操作按钮 */
.detail-actions {
  display: flex;
  gap: 16rpx;
}

.action-copy,
.action-revoke,
.action-delete {
  flex: 1;
  height: 68rpx;
  border-radius: 12rpx;
  font-size: 26rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
}

.action-copy {
  background: linear-gradient(135deg, #007AFF 0%, #00d4ff 100%);
  color: #fff;
}

.action-revoke {
  background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
  color: #fff;
}

.action-delete {
  background: #f5f5f5;
  color: #e53935;
  border: 1rpx solid #e53935;
}

/* 加载中 */
.loading-state {
  text-align: center;
  padding: 60rpx 0;
}

.loading-text {
  font-size: 28rpx;
  color: #999;
}
</style>

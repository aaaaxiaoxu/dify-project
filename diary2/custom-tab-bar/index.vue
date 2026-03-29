<template>
  <view class="tab-bar-root">
    <view class="tab-bar-placeholder"></view>
    <view class="tab-bar">
      <view
        v-for="tab in visibleTabs"
        :key="tab.pagePath"
        class="tab-item"
        :class="{ active: currentPath === tab.pagePath }"
        @click="switchTab(tab)"
      >
        <image
          class="tab-icon"
          :src="currentPath === tab.pagePath ? tab.selectedIconPath : tab.iconPath"
          mode="aspectFit"
        />
        <text class="tab-label">{{ tab.text }}</text>
      </view>
    </view>
  </view>
</template>

<script>
import store from '../store'
import request from '../utils/request.js'
import config from '../api/config.js'

const BASE_TABS = [
  {
    text: '首页',
    pagePath: '/pages/index/index',
    iconPath: '/static/tabbar/home.png',
    selectedIconPath: '/static/tabbar/home-active.png'
  },
  {
    text: '日记',
    pagePath: '/pages/diary/list',
    iconPath: '/static/tabbar/diary.png',
    selectedIconPath: '/static/tabbar/diary-active.png'
  },
  {
    text: '足迹',
    pagePath: '/pages/map/map',
    iconPath: '/static/tabbar/map.png',
    selectedIconPath: '/static/tabbar/map-active.png'
  },
  {
    text: '统计',
    pagePath: '/pages/stats/stats',
    iconPath: '/static/tabbar/stats.png',
    selectedIconPath: '/static/tabbar/stats-active.png'
  },
  {
    text: '我的',
    pagePath: '/pages/profile/profile',
    iconPath: '/static/tabbar/mine.png',
    selectedIconPath: '/static/tabbar/mine-active.png'
  }
]

const ADMIN_TAB = {
  text: '管理',
  pagePath: '/pages/admin/admin',
  iconPath: '/static/tabbar/admin.png',
  selectedIconPath: '/static/tabbar/admin-active.png'
}

export default {
  data() {
    return {
      currentPath: ''
    }
  },

  computed: {
    isAdmin() {
      return !!store.state.isAdmin
    },

    visibleTabs() {
      return this.isAdmin ? [...BASE_TABS, ADMIN_TAB] : BASE_TABS
    }
  },

  created() {
    this.syncCurrentPath()
    this.refreshAdminStatus()
  },

  mounted() {
    this.syncCurrentPath()
  },

  pageLifetimes: {
    show() {
      this.syncCurrentPath()
      this.refreshAdminStatus()
    }
  },

  methods: {
    syncCurrentPath() {
      const pages = getCurrentPages()
      const currentPage = pages && pages.length ? pages[pages.length - 1] : null
      const route = currentPage && (currentPage.route || (currentPage.$page && currentPage.$page.route))
      this.currentPath = route ? `/${String(route).split('?')[0]}` : ''
    },

    refreshAdminStatus() {
      const token = store.state.token || ''
      if (!token) {
        store.commit('SET_IS_ADMIN', false)
        return
      }

      request({
        url: config.ADMIN_CHECK,
        method: 'GET',
        header: {
          Authorization: 'Bearer ' + token
        }
      }).then((res) => {
        store.commit('SET_IS_ADMIN', !!(res && res.is_admin))
      }).catch(() => {
        store.commit('SET_IS_ADMIN', false)
      })
    },

    switchTab(tab) {
      if (!tab || this.currentPath === tab.pagePath) return
      this.currentPath = tab.pagePath
      uni.switchTab({
        url: tab.pagePath
      })
    }
  }
}
</script>

<style scoped>
.tab-bar-root {
  position: relative;
}

.tab-bar-placeholder {
  height: calc(120rpx + env(safe-area-inset-bottom));
}

.tab-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 999;
  display: flex;
  align-items: stretch;
  justify-content: space-around;
  min-height: 120rpx;
  padding-bottom: env(safe-area-inset-bottom);
  background: rgba(255, 255, 255, 0.98);
  border-top: 1rpx solid rgba(148, 163, 184, 0.22);
  box-shadow: 0 -8rpx 24rpx rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(18rpx);
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  min-height: 120rpx;
}

.tab-icon {
  width: 44rpx;
  height: 44rpx;
}

.tab-label {
  font-size: 22rpx;
  color: #7a7e83;
  line-height: 1;
}

.tab-item.active .tab-label {
  color: #007aff;
  font-weight: 600;
}
</style>

<template>
  <view class="container">
    <view class="header">
      <text class="title">旅行足迹</text>
    </view>
    
    <view class="map-container">
      <!-- 腾讯地图组件 -->
      <map 
        id="map" 
        ref="map" 
        class="map-placeholder"
        :longitude="mapCenter.longitude" 
        :latitude="mapCenter.latitude" 
        :scale="mapScale"
        :markers="mapMarkers"
        :polyline="mapPolyline"
        show-location
        @markertap="onMarkerTap"
      ></map>
    </view>
    
    <view class="stats-section">
      <!-- 时间筛选 -->
      <view class="filter-bar">
        <view 
          v-for="tab in filterTabs" 
          :key="tab.value"
          class="filter-chip"
          :class="{ active: activeFilter === tab.value }"
          @click="onFilterChange(tab.value)"
        >
          <text>{{ tab.label }}</text>
        </view>
      </view>
      
      <!-- 自定义日期范围 -->
      <view v-if="activeFilter === 'custom'" class="custom-date-range">
        <picker mode="date" :value="customStartDate" @change="onStartDateChange">
          <view class="date-picker-btn">{{ customStartDate || '开始日期' }}</view>
        </picker>
        <text class="date-range-sep">至</text>
        <picker mode="date" :value="customEndDate" @change="onEndDateChange">
          <view class="date-picker-btn">{{ customEndDate || '结束日期' }}</view>
        </picker>
      </view>
      
      <view class="stats-card">
        <view class="stat-item">
          <text class="stat-number">{{ travelStats.totalCities }}</text>
          <text class="stat-label">城市</text>
        </view>
        <view class="stat-item">
          <text class="stat-number">{{ travelStats.totalDistance }}</text>
          <text class="stat-label">公里</text>
        </view>
        <view class="stat-item">
          <text class="stat-number">{{ travelStats.totalDays }}</text>
          <text class="stat-label">天数</text>
        </view>
      </view>
    </view>
    
    <view class="travel-history">
      <view class="section-header">
        <text class="section-title">旅行历史</text>
      </view>
      
      <view class="history-list">
        <view 
          v-for="(record, index) in travelHistory" 
          :key="index"
          class="history-item"
          @click="showOnMap(record)"
        >
          <view class="history-info">
            <text class="history-location">{{ record.location }}</text>
            <text class="history-date">{{ formatDate(record.date) }}</text>
          </view>
          <view class="history-emotion">
            <text>{{ getEmotionLabel(record.emotion) }}</text>
          </view>
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
      mapCenter: {
        longitude: 104.195397, // 中国中心经度
        latitude: 35.861660    // 中国中心纬度
      },
      mapScale: 4, // 初始缩放级别
      mapMarkers: [],
      mapPolyline: [],
      travelStats: {
        totalCities: 0,
        totalDistance: 0,
        totalDays: 0
      },
      travelHistory: [],
      allTravelHistory: [],      // 完整数据（未筛选）
      activeFilter: 'all',
      customStartDate: '',
      customEndDate: '',
      filterTabs: [
        { label: '全部', value: 'all' },
        { label: '本月', value: 'month' },
        { label: '去年', value: 'lastYear' },
        { label: '自定义', value: 'custom' }
      ]
    }
  },
  
  onLoad() {
    this.loadMapData()
  },
  
  onShow() {
    // 页面每次显示时重新加载数据
    this.loadMapData()
  },
  
  methods: {
    haversineKm(lat1, lon1, lat2, lon2) {
      const R = 6371
      const toRad = (d) => (d * Math.PI) / 180
      const dLat = toRad(lat2 - lat1)
      const dLon = toRad(lon2 - lon1)
      const a =
        Math.sin(dLat / 2) ** 2 +
        Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2
      const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(Math.max(0, 1 - a)))
      return R * c
    },

    /** 与后端逻辑一致：不同地点数、有坐标时按时间序累加球面距离、不同日期数 */
    computeFootprintFromRecords(records) {
      if (!records || !records.length) {
        return { cities: 0, distanceKm: 0, days: 0 }
      }
      const locs = new Set()
      const dayKeys = new Set()
      for (const r of records) {
        if (r.location && String(r.location).trim()) {
          locs.add(String(r.location).trim())
        }
        if (r.date) {
          const d = new Date(r.date)
          if (Number.isFinite(d.getTime())) {
            const y = d.getFullYear()
            const m = String(d.getMonth() + 1).padStart(2, '0')
            const day = String(d.getDate()).padStart(2, '0')
            dayKeys.add(`${y}-${m}-${day}`)
          }
        }
      }
      const withCoord = [...records]
        .filter((r) => r.longitude && r.latitude)
        .sort((a, b) => {
          const ta = new Date(a.date).getTime()
          const tb = new Date(b.date).getTime()
          if (Number.isFinite(ta) && Number.isFinite(tb) && ta !== tb) return ta - tb
          return 0
        })
      let dist = 0
      for (let i = 1; i < withCoord.length; i++) {
        dist += this.haversineKm(
          withCoord[i - 1].latitude,
          withCoord[i - 1].longitude,
          withCoord[i].latitude,
          withCoord[i].longitude
        )
      }
      return {
        cities: locs.size,
        distanceKm: Math.round(dist * 10) / 10,
        days: dayKeys.size
      }
    },

    loadMapData() {
      // 调用后端获取详细地图数据接口
      const token = this.$store && this.$store.state ? this.$store.state.token : ''
      
      if (!token) {
        console.log('用户未登录，使用默认数据')
        this.loadDefaultData()
        return
      }
      
      request({
        url: config.MAP_DETAIL,
        method: 'GET',
        header: {
          'Authorization': 'Bearer ' + token
        }
      }).then(res => {
        // 保存完整数据
        this.allTravelHistory = res.history.map(item => ({
          location: item.location,
          date: item.date,
          emotion: item.emotion,
          longitude: item.longitude || 0,
          latitude: item.latitude || 0
        }))
        
        // 按当前筛选条件过滤并渲染
        this.applyFilter()
      }).catch(err => {
        console.error('获取地图数据失败:', err)
        // 出错时使用默认数据
        this.loadDefaultData()
      })
    },
    
    loadDefaultData() {
      // 使用默认数据
      this.allTravelHistory = [
        {
          location: '杭州西湖',
          date: '2023-05-15',
          emotion: '开心',
          longitude: 120.143669,
          latitude: 30.242289
        },
        {
          location: '丽江古城',
          date: '2023-04-22',
          emotion: '感动',
          longitude: 100.233024,
          latitude: 26.872303
        },
        {
          location: '三亚亚龙湾',
          date: '2023-03-10',
          emotion: '兴奋',
          longitude: 109.647202,
          latitude: 18.195288
        },
        {
          location: '北京故宫',
          date: '2023-01-15',
          emotion: '平静',
          longitude: 116.397026,
          latitude: 39.918058
        },
        {
          location: '桂林漓江',
          date: '2022-11-05',
          emotion: '思念',
          longitude: 110.290199,
          latitude: 25.269362
        }
      ]
      
      this.applyFilter()
    },
    
    setMapMarkers() {
      // ---- 1. 先按日期升序排列，计算每条记录的时间序号 ----
      const sortedForPath = [...this.travelHistory]
        .filter(record => record.longitude && record.latitude)
        .sort((a, b) => {
          const ta = new Date(a.date).getTime()
          const tb = new Date(b.date).getTime()
          const na = Number.isFinite(ta)
          const nb = Number.isFinite(tb)
          if (na && !nb) return -1
          if (!na && nb) return 1
          if (na && nb && ta !== tb) return ta - tb
          return 0
        })

      // 记录对象 → 时间序号（1-based）
      const chronoOrder = new Map()
      sortedForPath.forEach((record, idx) => {
        chronoOrder.set(record, idx + 1)
      })
      const totalStops = sortedForPath.length

      // ---- 2. 创建地图标记点，callout 中带序号 ----
      this.mapMarkers = this.travelHistory.map((record, index) => {
        let color = '#007AFF'
        let iconPath = '/static/custom-icons/location-pin.svg'

        switch(record.emotion) {
          case '开心':
            color = '#FFD700'
            iconPath = '/static/custom-icons/location-pin-happy.svg'
            break
          case '感动':
            color = '#1E90FF'
            iconPath = '/static/custom-icons/location-pin-moved.svg'
            break
          case '兴奋':
            color = '#FF4500'
            iconPath = '/static/custom-icons/location-pin-excited.svg'
            break
          case '平静':
            color = '#32CD32'
            iconPath = '/static/custom-icons/location-pin-calm.svg'
            break
          case '忧郁':
            color = '#4169E1'
            iconPath = '/static/custom-icons/location-pin-sad.svg'
            break
          case '思念':
            color = '#8A2BE2'
            iconPath = '/static/custom-icons/location-pin-miss.svg'
            break
          case '感伤':
            color = '#708090'
            iconPath = '/static/custom-icons/location-pin-sentimental.svg'
            break
        }

        // 拼接序号前缀，如 "② 丽江古城"
        const order = chronoOrder.get(record)
        let calloutContent = record.location
        if (order) {
          calloutContent = this.getCircledNumber(order) + ' ' + record.location
        }

        return {
          id: index,
          longitude: record.longitude || 0,
          latitude: record.latitude || 0,
          title: record.location,
          iconPath: iconPath,
          width: 40,
          height: 40,
          callout: {
            content: calloutContent,
            display: 'ALWAYS',
            borderRadius: 8,
            padding: 12,
            bgColor: '#ffffff',
            color: '#333333',
            textAlign: 'center',
            borderColor: color,
            borderWidth: 2,
            fontSize: 14,
            fontWeight: 'bold'
          }
        }
      })

      // ---- 3. 绘制轨迹连线 ----
      const points = sortedForPath.map(record => ({
        longitude: record.longitude,
        latitude: record.latitude
      }))

      this.mapPolyline = []

      if (points.length >= 2) {
        // 白色背景线，增强可见性
        this.mapPolyline.push({
          points: points,
          color: '#FFFFFF99',
          width: 12,
          dottedLine: false
        })
        // 主轨迹线 + 箭头
        this.mapPolyline.push({
          points: points,
          color: '#007AFF',
          width: 6,
          dottedLine: false,
          arrowLine: true,
          borderColor: '#005EC4',
          borderWidth: 1
        })
      }

      // 根据足迹范围自动调整地图视野
      this.fitMapToBounds(points);
    },
    
    // 根据所有点自动调整地图视野
    fitMapToBounds(points) {
      if (points.length === 0) return;
      
      if (points.length === 1) {
        // 只有一个点，设置为中心点并适当缩放
        this.mapCenter = {
          longitude: points[0].longitude,
          latitude: points[0].latitude
        };
        this.mapScale = 14;
        return;
      }
      
      // 计算边界
      let minLat = points[0].latitude;
      let maxLat = points[0].latitude;
      let minLng = points[0].longitude;
      let maxLng = points[0].longitude;
      
      points.forEach(point => {
        if (point.latitude < minLat) minLat = point.latitude;
        if (point.latitude > maxLat) maxLat = point.latitude;
        if (point.longitude < minLng) minLng = point.longitude;
        if (point.longitude > maxLng) maxLng = point.longitude;
      });
      
      // 设置中心点
      this.mapCenter = {
        longitude: (minLng + maxLng) / 2,
        latitude: (minLat + maxLat) / 2
      };
      
      // 根据跨度计算合适的缩放级别，确保显示所有点
      const latSpan = maxLat - minLat;
      const lngSpan = maxLng - minLng;

      if (latSpan === 0 && lngSpan === 0) {
        this.mapScale = 14;
        return;
      }

      // 增加更大的边距以确保所有标记都能完整显示
      const latMargin = latSpan * 1.2; // 增加边距到1.2倍
      const lngMargin = lngSpan * 1.2; // 增加边距到1.2倍
      
      // 更精确地计算适合所有点的缩放级别
      // 使用更宽松的缩放算法确保所有点都能显示
      const latZoom = Math.floor(Math.log2(360 / (latSpan + latMargin)));
      const lngZoom = Math.floor(Math.log2(360 / (lngSpan + lngMargin)));
      
      // 取较小的缩放级别并减去一个偏移值以增加一些边距
      this.mapScale = Math.min(latZoom, lngZoom) - 1;
      
      // 确保缩放级别在合理范围内，现在设置为更小的值以获得更大的视野
      this.mapScale = Math.max(2, Math.min(this.mapScale, 7)); // 最大缩放级别从8调整为7
    },
    
    getEmotionLabel(emotion) {
      const labels = {
        '开心': '😊',
        '感动': '😢',
        '兴奋': '🤩',
        '平静': '😌',
        '忧郁': '😔',
        '思念': '🥺',
        '感伤': '😿'
      }
      return labels[emotion] || emotion
    },
    
    // 数字 → 带圈序号，如 1→①  5→⑤  21→"21"
    getCircledNumber(n) {
      const circled = [
        '①','②','③','④','⑤','⑥','⑦','⑧','⑨','⑩',
        '⑪','⑫','⑬','⑭','⑮','⑯','⑰','⑱','⑲','⑳'
      ]
      if (n >= 1 && n <= 20) return circled[n - 1]
      return String(n)
    },
    
    // ---- 时间筛选相关 ----
    onFilterChange(value) {
      this.activeFilter = value
      if (value === 'custom') {
        // 如果已经选过日期，立即应用
        if (this.customStartDate && this.customEndDate) {
          this.applyFilter()
        }
      } else {
        this.applyFilter()
      }
    },
    
    onStartDateChange(e) {
      this.customStartDate = e.detail.value
      if (this.customEndDate) {
        if (this.customStartDate > this.customEndDate) {
          uni.showToast({ title: '开始日期不能晚于结束日期', icon: 'none' })
          return
        }
        this.applyFilter()
      }
    },
    
    onEndDateChange(e) {
      this.customEndDate = e.detail.value
      if (this.customStartDate) {
        if (this.customStartDate > this.customEndDate) {
          uni.showToast({ title: '结束日期不能早于开始日期', icon: 'none' })
          return
        }
        this.applyFilter()
      }
    },
    
    getFilterDateRange() {
      const now = new Date()
      switch (this.activeFilter) {
        case 'all':
          return null
        case 'month': {
          const y = now.getFullYear()
          const m = now.getMonth()     // 0-based
          const firstDay = new Date(y, m, 1)
          const lastDay = new Date(y, m + 1, 0)
          return {
            start: this.toDateStr(firstDay),
            end: this.toDateStr(lastDay)
          }
        }
        case 'lastYear': {
          const y = now.getFullYear() - 1
          return { start: `${y}-01-01`, end: `${y}-12-31` }
        }
        case 'custom': {
          if (this.customStartDate && this.customEndDate) {
            return { start: this.customStartDate, end: this.customEndDate }
          }
          return null
        }
        default:
          return null
      }
    },
    
    toDateStr(d) {
      const y = d.getFullYear()
      const m = String(d.getMonth() + 1).padStart(2, '0')
      const day = String(d.getDate()).padStart(2, '0')
      return `${y}-${m}-${day}`
    },
    
    applyFilter() {
      const range = this.getFilterDateRange()
      
      if (!range) {
        this.travelHistory = [...this.allTravelHistory]
      } else {
        this.travelHistory = this.allTravelHistory.filter(record => {
          if (!record.date) return false
          return record.date >= range.start && record.date <= range.end
        })
      }
      
      // 重新计算统计数据
      const local = this.computeFootprintFromRecords(this.travelHistory)
      this.travelStats.totalCities = local.cities
      this.travelStats.totalDistance = local.distanceKm
      this.travelStats.totalDays = local.days
      
      // 重建地图标记和轨迹线
      this.setMapMarkers()
    },
    
    formatDate(dateString) {
      const date = new Date(dateString)
      return `${date.getMonth() + 1}月${date.getDate()}日`
    },
    
    showOnMap(record) {
      // 移动地图中心到指定位置
      this.mapCenter = {
        longitude: record.longitude || this.mapCenter.longitude,
        latitude: record.latitude || this.mapCenter.latitude
      }
      
      // 适当放大以便更好地查看
      this.mapScale = 14;
      
      uni.showToast({
        title: `在地图上显示 ${record.location}`,
        icon: 'none'
      })
    },
    
    onMarkerTap(e) {
      const markerId = e.detail.markerId;
      const record = this.travelHistory[markerId];
      if (record) {
        uni.showModal({
          title: record.location,
          content: `时间: ${this.formatDate(record.date)}\n心情: ${record.emotion}`,
          showCancel: false
        })
      }
    }
  }
}
</script>

<style scoped>
.container {
  padding: 30rpx;
}

.header {
  margin-bottom: 30rpx;
}

.title {
  font-size: 40rpx;
  font-weight: bold;
  color: #333;
}

.map-container {
  background: #fff;
  border-radius: 20rpx;
  height: 700rpx;
  margin-bottom: 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.05);
  overflow: hidden;
}

.map-placeholder {
  width: 100%;
  height: 100%;
}

.stats-section {
  margin-bottom: 30rpx;
}

.filter-bar {
  display: flex;
  gap: 16rpx;
  margin-bottom: 24rpx;
}

.filter-chip {
  padding: 12rpx 30rpx;
  border-radius: 30rpx;
  background: #f0f0f0;
  font-size: 26rpx;
  color: #666;
}

.filter-chip.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.custom-date-range {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 24rpx;
}

.date-picker-btn {
  padding: 14rpx 24rpx;
  background: #f0f0f0;
  border-radius: 12rpx;
  font-size: 26rpx;
  color: #333;
}

.date-range-sep {
  font-size: 26rpx;
  color: #999;
}

.stats-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 20rpx;
  padding: 40rpx 0;
  display: flex;
  justify-content: space-around;
  box-shadow: 0 10rpx 20rpx rgba(0,0,0,0.1);
}

.stat-item {
  text-align: center;
}

.stat-number {
  display: block;
  font-size: 48rpx;
  font-weight: bold;
  color: #fff;
  margin-bottom: 10rpx;
}

.stat-label {
  font-size: 24rpx;
  color: rgba(255,255,255,0.8);
}

.travel-history {
  background: #fff;
  border-radius: 20rpx;
  padding: 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.05);
}

.section-header {
  margin-bottom: 20rpx;
}

.section-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20rpx;
  background: #f8f8f8;
  border-radius: 10rpx;
  transition: all 0.3s ease;
}

.history-item:hover {
  background: #e0e0e0;
  transform: translateY(-2rpx);
}

.history-info {
  display: flex;
  flex-direction: column;
}

.history-location {
  font-size: 30rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 10rpx;
}

.history-date {
  font-size: 24rpx;
  color: #999;
}

.history-emotion {
  font-size: 36rpx;
}
</style>
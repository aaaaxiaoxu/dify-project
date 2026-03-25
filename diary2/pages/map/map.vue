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
      travelHistory: []
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
        // 设置统计数据
        this.travelStats.totalCities = res.stats.total_cities
        this.travelStats.totalDistance = res.stats.total_distance
        this.travelStats.totalDays = res.stats.total_days
        
        // 设置旅行历史
        this.travelHistory = res.history.map(item => ({
          location: item.location,
          date: item.date,
          emotion: item.emotion,
          longitude: item.longitude || 0,
          latitude: item.latitude || 0
        }))
        
        // 设置地图标记点
        this.setMapMarkers()
      }).catch(err => {
        console.error('获取地图数据失败:', err)
        // 出错时使用默认数据
        this.loadDefaultData()
      })
    },
    
    loadDefaultData() {
      // 使用默认数据
      this.travelHistory = [
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
      
      this.travelStats.totalCities = 12
      this.travelStats.totalDistance = 2450
      this.travelStats.totalDays = 45
      
      // 设置地图标记点
      this.setMapMarkers()
    },
    
    setMapMarkers() {
      // 创建地图标记点
      this.mapMarkers = this.travelHistory.map((record, index) => {
        // 根据情绪选择不同颜色的标记点
        let color = '#007AFF'; // 默认蓝色
        let iconPath = '/static/custom-icons/location-pin.svg'; // 默认图标
        
        switch(record.emotion) {
          case '开心':
            color = '#FFD700'; // 金色
            iconPath = '/static/custom-icons/location-pin-happy.svg';
            break;
          case '感动':
            color = '#1E90FF'; // 道奇蓝
            iconPath = '/static/custom-icons/location-pin-moved.svg';
            break;
          case '兴奋':
            color = '#FF4500'; // 橙红色
            iconPath = '/static/custom-icons/location-pin-excited.svg';
            break;
          case '平静':
            color = '#32CD32'; // 酸橙绿
            iconPath = '/static/custom-icons/location-pin-calm.svg';
            break;
          case '忧郁':
            color = '#4169E1'; // 皇家蓝
            iconPath = '/static/custom-icons/location-pin-sad.svg';
            break;
          case '思念':
            color = '#8A2BE2'; // 蓝紫色
            iconPath = '/static/custom-icons/location-pin-miss.svg';
            break;
        }
        
        return {
          id: index,
          longitude: record.longitude || 0,
          latitude: record.latitude || 0,
          title: record.location,
          // 使用更有吸引力的标记点
          iconPath: iconPath,
          width: 40,
          height: 40,
          callout: {
            content: record.location,
            display: 'ALWAYS', // 始终显示标记点名称
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
      
      // 创建轨迹线
      const points = this.travelHistory
        .filter(record => record.longitude && record.latitude)
        .map(record => {
          return {
            longitude: record.longitude,
            latitude: record.latitude
          }
        })
      
      if (points.length > 1) {
        this.mapPolyline = [{
          points: points,
          color: '#007AFFCC', // 半透明蓝色
          width: 8, // 从6增加到8
          dottedLine: false,
          arrowLine: true, // 显示箭头方向
          borderColor: '#007AFF',
          borderWidth: 1
        }]
      }
      
      // 如果点数较多，添加一个更粗的背景线以增强可见性
      if (points.length > 2) {
        this.mapPolyline.unshift({
          points: points,
          color: '#FFFFFF99', // 更明显的半透明白色背景线
          width: 12, // 从10增加到12
          dottedLine: false
        });
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
        '思念': '🥺'
      }
      return labels[emotion] || emotion
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
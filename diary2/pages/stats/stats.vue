<template>
  <view class="container">
    <view class="header">
      <text class="title">统计分析</text>
      <text class="subtitle">情感与频率洞察</text>
    </view>

    <!-- 概览卡片 -->
    <view class="overview-cards">
      <view class="card-item">
        <text class="card-number">{{ totalDiaries }}</text>
        <text class="card-label">日记总数</text>
      </view>
      <view class="card-item">
        <text class="card-number">{{ topEmotion }}</text>
        <text class="card-label">主要情绪区间</text>
      </view>
      <view class="card-item">
        <text class="card-number">{{ avgScoreDisplay }}</text>
        <text class="card-label">平均情绪评分</text>
      </view>
    </view>

    <!-- 情感倾向分布饼图 -->
    <view class="chart-section">
      <view class="section-header">
        <text class="section-title">情绪评分分布</text>
      </view>
      <view class="chart-wrapper">
        <canvas
          canvas-id="pieChart"
          id="pieChart"
          class="chart-canvas"
          :style="{ width: canvasWidth + 'px', height: '280px' }"
        ></canvas>
      </view>
      <!-- 饼图图例 -->
      <view class="legend-list">
        <view
          v-for="(item, index) in pieData"
          :key="index"
          class="legend-item"
        >
          <view
            class="legend-dot"
            :style="{ backgroundColor: emotionColors[item.emotion] || '#999' }"
          ></view>
          <view class="legend-main">
            <text class="legend-label">{{ item.emotion }}</text>
            <text v-if="item.range" class="legend-range">{{ item.range }}</text>
          </view>
          <text class="legend-value">{{ item.count }}篇 ({{ piePercent(item.count) }})</text>
        </view>
      </view>
    </view>

    <!-- 情绪波动折线图 -->
    <view class="chart-section">
      <view class="section-header">
        <text class="section-title">情绪波动趋势</text>
        <view class="period-switch">
          <view
            class="period-tab"
            :class="{ active: trendPeriod === '7d' }"
            @click="switchPeriod('7d')"
          >
            近7天
          </view>
          <view
            class="period-tab"
            :class="{ active: trendPeriod === '30d' }"
            @click="switchPeriod('30d')"
          >
            近30天
          </view>
          <view
            class="period-tab"
            :class="{ active: trendPeriod === 'all' }"
            @click="switchPeriod('all')"
          >
            全部
          </view>
        </view>
      </view>
      <view class="chart-wrapper">
        <canvas
          canvas-id="lineChart"
          id="lineChart"
          class="chart-canvas chart-canvas-line"
          :style="{ width: canvasWidth + 'px', height: '300px' }"
        ></canvas>
      </view>
      <!-- 折线图图例 -->
      <view class="line-legend">
        <view class="legend-item">
          <view class="legend-line" style="background-color: #007AFF;"></view>
          <text class="legend-label">日记数量</text>
        </view>
        <view class="legend-item">
          <view class="legend-line" style="background-color: #FF6B6B;"></view>
          <text class="legend-label">情绪评分</text>
        </view>
      </view>
    </view>

    <!-- 底部占位 -->
    <view style="height: 120rpx;"></view>
  </view>
</template>

<script>
import request from '../../utils/request.js'
import config from '../../api/config.js'

// 情绪颜色映射
const EMOTION_COLORS = {
  '强烈积极': '#22C55E',
  '偏积极': '#84CC16',
  '中性': '#94A3B8',
  '偏消极': '#FB923C',
  '强烈消极': '#EF4444',
  '待分析': '#CBD5E1',
}

// 备用颜色（如果出现未知情绪）
const FALLBACK_COLORS = ['#60A5FA', '#FBBF24', '#F87171', '#2DD4BF', '#818CF8', '#FB923C']

export default {
  data() {
    return {
      canvasWidth: 300,
      pieData: [],
      totalDiaries: 0,
      avgEmotionScore: null,
      trendPeriod: '7d',
      trendData: { dates: [], counts: [], scores: [] },
      emotionColors: EMOTION_COLORS,
    }
  },

  computed: {
    token() {
      return this.$store.state.token
    },

    topEmotion() {
      if (!this.pieData.length) return '--'
      const sorted = [...this.pieData].sort((a, b) => b.count - a.count)
      return sorted[0].emotion
    },

    avgScoreDisplay() {
      if (this.avgEmotionScore === null) return '--'
      return this.formatScore(this.avgEmotionScore)
    },
  },

  onLoad() {
    // 获取屏幕宽度用于 canvas 尺寸
    const info = uni.getSystemInfoSync()
    this.canvasWidth = info.windowWidth - 60 // 容器 padding
  },

  onShow() {
    this.loadData()
  },

  methods: {
    loadData() {
      if (!this.token) {
        uni.showToast({ title: '请先登录', icon: 'none' })
        return
      }
      this.fetchEmotionDistribution()
      this.fetchEmotionTrend()
    },

    // ---- 饼图数据 ----
    fetchEmotionDistribution() {
      request({
        url: config.STATS_EMOTION_DISTRIBUTION,
        method: 'GET',
        header: { Authorization: 'Bearer ' + this.token },
      })
        .then((data) => {
          this.pieData = data.items || []
          this.totalDiaries = data.total || 0
          this.avgEmotionScore = this.normalizeScore(data.avg_score)
          this.$nextTick(() => {
            setTimeout(() => this.drawPieChart(), 150)
          })
        })
        .catch((err) => {
          console.error('获取情感分布失败:', err)
        })
    },

    // ---- 折线图数据 ----
    fetchEmotionTrend() {
      request({
        url: config.STATS_EMOTION_TREND + '?period=' + this.trendPeriod,
        method: 'GET',
        header: { Authorization: 'Bearer ' + this.token },
      })
        .then((data) => {
          this.trendData = data
          this.$nextTick(() => {
            setTimeout(() => this.drawLineChart(), 150)
          })
        })
        .catch((err) => {
          console.error('获取情绪趋势失败:', err)
        })
    },

    switchPeriod(period) {
      if (this.trendPeriod === period) return
      this.trendPeriod = period
      this.fetchEmotionTrend()
    },

    piePercent(count) {
      if (!this.totalDiaries) return '0%'
      return ((count / this.totalDiaries) * 100).toFixed(1) + '%'
    },

    normalizeScore(score) {
      if (score === null || score === undefined || score === '') return null
      const value = Number(score)
      if (Number.isNaN(value)) return null
      return Math.max(-1, Math.min(1, value))
    },

    formatScore(score) {
      const value = this.normalizeScore(score)
      if (value === null) return '--'
      const fixed = value.toFixed(1)
      return value > 0 ? `+${fixed}` : fixed
    },

    formatCountTick(value) {
      if (value >= 10 || Number.isInteger(value)) {
        return String(Math.round(value))
      }
      return value.toFixed(1)
    },

    formatTrendDateLabel(dateStr) {
      const granularity = this.trendData.granularity || 'day'
      const parts = String(dateStr || '').split('-')

      if (granularity === 'month') {
        if (parts.length < 2) return dateStr
        const [year, month] = parts
        return `${year.slice(-2)}/${month}`
      }

      if (parts.length < 3) return dateStr
      return `${parts[1]}/${parts[2]}`
    },

    // =================== 饼图绘制 ===================
    drawPieChart() {
      const ctx = uni.createCanvasContext('pieChart', this)
      const w = this.canvasWidth
      const h = 280
      const cx = w / 2
      const cy = h / 2
      const radius = Math.min(cx, cy) - 30

      // 清除画布
      ctx.clearRect(0, 0, w, h)

      if (!this.pieData.length) {
        ctx.setFontSize(14)
        ctx.setFillStyle('#999')
        ctx.setTextAlign('center')
        ctx.fillText('暂无数据', cx, cy)
        ctx.draw()
        return
      }

      const total = this.pieData.reduce((sum, item) => sum + (Number(item.count) || 0), 0)
      let startAngle = -Math.PI / 2 // 从顶部开始

      this.pieData.forEach((item, index) => {
        const sliceAngle = (item.count / total) * 2 * Math.PI
        const endAngle = startAngle + sliceAngle
        const color = EMOTION_COLORS[item.emotion] || FALLBACK_COLORS[index % FALLBACK_COLORS.length]

        // 绘制扇形
        ctx.beginPath()
        ctx.moveTo(cx, cy)
        ctx.arc(cx, cy, radius, startAngle, endAngle)
        ctx.closePath()
        ctx.setFillStyle(color)
        ctx.fill()

        // 绘制白色分割线
        ctx.beginPath()
        ctx.moveTo(cx, cy)
        ctx.arc(cx, cy, radius, startAngle, endAngle)
        ctx.closePath()
        ctx.setStrokeStyle('#ffffff')
        ctx.setLineWidth(2)
        ctx.stroke()

        // 在扇形中间绘制标签（仅当占比 > 8% 时）
        if (item.count / total > 0.08) {
          const midAngle = startAngle + sliceAngle / 2
          const labelRadius = radius * 0.65
          const lx = cx + labelRadius * Math.cos(midAngle)
          const ly = cy + labelRadius * Math.sin(midAngle)
          ctx.setFontSize(12)
          ctx.setFillStyle('#fff')
          ctx.setTextAlign('center')
          ctx.fillText(item.emotion, lx, ly)
        }

        startAngle = endAngle
      })

      // 中心圆（营造甜甜圈效果）
      ctx.beginPath()
      ctx.arc(cx, cy, radius * 0.4, 0, 2 * Math.PI)
      ctx.setFillStyle('#ffffff')
      ctx.fill()

      // 中心文字
      ctx.setFontSize(20)
      ctx.setFillStyle('#333')
      ctx.setTextAlign('center')
      ctx.fillText(total, cx, cy - 2)
      ctx.setFontSize(11)
      ctx.setFillStyle('#999')
      ctx.fillText('篇日记', cx, cy + 16)

      ctx.draw()
    },

    // =================== 折线图绘制 ===================
    drawLineChart() {
      const ctx = uni.createCanvasContext('lineChart', this)
      const w = this.canvasWidth
      const h = 300
      const padding = { top: 30, right: 42, bottom: 50, left: 44 }
      const chartW = w - padding.left - padding.right
      const chartH = h - padding.top - padding.bottom

      ctx.clearRect(0, 0, w, h)

      const dates = this.trendData.dates || []
      const counts = this.trendData.counts || []
      const scores = this.trendData.scores || []

      if (!dates.length) {
        ctx.setFontSize(14)
        ctx.setFillStyle('#999')
        ctx.setTextAlign('center')
        ctx.fillText('暂无数据', w / 2, h / 2)
        ctx.draw()
        return
      }

      const maxCount = Math.max(...counts, 1)
      const scoreMax = 1
      const scoreMin = -1
      const scoreRange = scoreMax - scoreMin
      const getScoreY = (score) => padding.top + ((scoreMax - score) / scoreRange) * chartH

      // ---- 绘制网格线与 Y 轴刻度 ----
      ctx.setStrokeStyle('#E5E7EB')
      ctx.setLineWidth(0.5)
      const gridLines = 4
      for (let i = 0; i <= gridLines; i++) {
        const y = padding.top + (chartH / gridLines) * i
        ctx.beginPath()
        ctx.moveTo(padding.left, y)
        ctx.lineTo(w - padding.right, y)
        ctx.stroke()

        // 左侧 Y 轴刻度（日记数量）
        const countLabel = maxCount - (maxCount / gridLines) * i
        ctx.setFontSize(10)
        ctx.setFillStyle('#007AFF')
        ctx.setTextAlign('right')
        ctx.fillText(this.formatCountTick(countLabel), padding.left - 6, y + 4)
      }

      // 右侧 Y 轴标签（情绪评分）
      for (let i = 0; i <= gridLines; i++) {
        const y = padding.top + (chartH / gridLines) * i
        const scoreLabel = (scoreMax - (scoreRange / gridLines) * i).toFixed(1)
        ctx.setFontSize(10)
        ctx.setFillStyle('#FF6B6B')
        ctx.setTextAlign('left')
        ctx.fillText(scoreLabel, w - padding.right + 4, y + 4)
      }

      // ---- X 轴日期标签 ----
      const step = dates.length <= 7 ? 1 : Math.ceil(dates.length / 7)
      dates.forEach((dateStr, i) => {
        if (i % step !== 0 && i !== dates.length - 1) return
        const x = padding.left + (chartW / (dates.length - 1 || 1)) * i
        ctx.setFontSize(9)
        ctx.setFillStyle('#666')
        ctx.setTextAlign('center')
        ctx.fillText(this.formatTrendDateLabel(dateStr), x, h - padding.bottom + 18)
      })

      // ---- 日记数量折线 ----
      ctx.beginPath()
      ctx.setStrokeStyle('#007AFF')
      ctx.setLineWidth(2.5)
      counts.forEach((count, i) => {
        const x = padding.left + (chartW / (dates.length - 1 || 1)) * i
        const y = padding.top + chartH - (count / maxCount) * chartH
        if (i === 0) {
          ctx.moveTo(x, y)
        } else {
          ctx.lineTo(x, y)
        }
      })
      ctx.stroke()

      // 日记数量数据点
      counts.forEach((count, i) => {
        const x = padding.left + (chartW / (dates.length - 1 || 1)) * i
        const y = padding.top + chartH - (count / maxCount) * chartH
        ctx.beginPath()
        ctx.arc(x, y, 3.5, 0, 2 * Math.PI)
        ctx.setFillStyle('#007AFF')
        ctx.fill()
        ctx.setStrokeStyle('#fff')
        ctx.setLineWidth(2)
        ctx.stroke()
      })

      // ---- 情绪评分折线 ----
      const validScores = scores
        .map((s, i) => {
          const value = this.normalizeScore(s)
          return value !== null ? { x: i, y: value } : null
        })
        .filter(Boolean)

      if (validScores.length > 1) {
        ctx.beginPath()
        ctx.setStrokeStyle('#FF6B6B')
        ctx.setLineWidth(2.5)
        ctx.setLineDash([8, 4])
        let hasStarted = false
        scores.forEach((score, index) => {
          const value = this.normalizeScore(score)
          if (value === null) {
            hasStarted = false
            return
          }
          const x = padding.left + (chartW / (dates.length - 1 || 1)) * index
          const y = getScoreY(value)
          if (!hasStarted) {
            ctx.moveTo(x, y)
            hasStarted = true
            return
          }
          ctx.lineTo(x, y)
        })
        ctx.stroke()
        ctx.setLineDash([])
      }

      // 情绪评分数据点
      validScores.forEach((pt) => {
        const x = padding.left + (chartW / (dates.length - 1 || 1)) * pt.x
        const y = getScoreY(pt.y)
        ctx.beginPath()
        ctx.arc(x, y, 4, 0, 2 * Math.PI)
        ctx.setFillStyle('#FF6B6B')
        ctx.fill()
        ctx.setStrokeStyle('#fff')
        ctx.setLineWidth(2)
        ctx.stroke()
      })

      ctx.draw()
    },
  },
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
  display: block;
}

.subtitle {
  font-size: 24rpx;
  color: #999;
  margin-top: 8rpx;
  display: block;
}

/* 概览卡片 */
.overview-cards {
  display: flex;
  gap: 16rpx;
  margin-bottom: 30rpx;
}

.card-item {
  flex: 1;
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx 16rpx;
  text-align: center;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.06);
}

.card-number {
  font-size: 40rpx;
  font-weight: bold;
  color: #007AFF;
  display: block;
}

.card-label {
  font-size: 22rpx;
  color: #999;
  margin-top: 8rpx;
  display: block;
}

/* 图表区域 */
.chart-section {
  background: #fff;
  border-radius: 20rpx;
  padding: 30rpx;
  margin-bottom: 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.05);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: bold;
  color: #333;
}

.chart-wrapper {
  display: flex;
  justify-content: center;
}

.chart-canvas {
  width: 100%;
  height: 280px;
}

.chart-canvas-line {
  height: 300px;
}

/* 饼图图例 */
.legend-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  margin-top: 20rpx;
  padding-top: 20rpx;
  border-top: 1rpx solid #F3F4F6;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8rpx;
  width: 45%;
}

.legend-main {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.legend-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-line {
  width: 24rpx;
  height: 4rpx;
  border-radius: 2rpx;
  flex-shrink: 0;
}

.legend-label {
  font-size: 24rpx;
  color: #666;
}

.legend-range {
  font-size: 20rpx;
  color: #94A3B8;
}

.legend-value {
  font-size: 22rpx;
  color: #999;
  margin-left: auto;
}

/* 折线图图例 */
.line-legend {
  display: flex;
  justify-content: center;
  gap: 40rpx;
  margin-top: 16rpx;
  padding-top: 16rpx;
  border-top: 1rpx solid #F3F4F6;
}

/* 时间周期切换 */
.period-switch {
  display: flex;
  gap: 8rpx;
  background: #F3F4F6;
  border-radius: 999rpx;
  padding: 4rpx;
}

.period-tab {
  padding: 10rpx 24rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
  color: #666;
}

.period-tab.active {
  background: #007AFF;
  color: #fff;
}
</style>

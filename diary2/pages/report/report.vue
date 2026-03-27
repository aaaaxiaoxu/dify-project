<template>
  <view class="container">
    <view class="hero-card">
      <text class="page-title">智能旅行总结</text>
      <text class="page-subtitle">按时间范围生成旅行报告，回顾地点、情绪和记忆点。</text>
    </view>

    <view class="panel-card">
      <text class="section-title">选择时间范围</text>
      <view class="preset-row">
        <view
          v-for="option in rangeOptions"
          :key="option.value"
          class="preset-chip"
          :class="{ active: rangeType === option.value }"
          @click="selectRange(option.value)"
        >
          {{ option.label }}
        </view>
      </view>

      <view v-if="rangeType === 'custom'" class="date-grid">
        <view class="date-block">
          <text class="date-label">开始日期</text>
          <picker mode="date" :value="startDate" @change="handleStartDateChange">
            <view class="date-value">{{ startDate || '请选择开始日期' }}</view>
          </picker>
        </view>
        <view class="date-block">
          <text class="date-label">结束日期</text>
          <picker mode="date" :value="endDate" @change="handleEndDateChange">
            <view class="date-value">{{ endDate || '请选择结束日期' }}</view>
          </picker>
        </view>
      </view>

      <button class="generate-btn" :loading="loading" :disabled="loading" @click="generateReport">
        {{ loading ? '生成中...' : '生成旅行报告' }}
      </button>
      <text class="panel-tip">报告会优先复用已有日记分析结果，未配置报告工作流时会自动回退到本地总结。</text>
    </view>

    <view v-if="reportData" class="report-stack">
	      <view class="report-card report-header">
	        <view class="header-meta">
	          <text class="source-badge" :class="'source-' + reportData.source">{{ sourceLabel }}</text>
	          <text class="period-text">{{ formatPeriod(reportData.period) }}</text>
	        </view>
        <text class="report-title">{{ report.report_title }}</text>
        <text class="report-subtitle">{{ report.report_subtitle }}</text>
	        <button class="export-btn" :loading="exporting" :disabled="exporting" @click="exportPdf">
	          {{ exporting ? '导出中...' : '导出 PDF' }}
	        </button>
	      </view>

	      <view v-if="reportImages.length" class="report-card report-images-card">
	        <text class="card-title">旅行图片</text>
	        <text class="images-tip">每篇日记最多展示 1 张图，没有图片的日记会自动跳过。</text>
	        <view class="images-grid">
	          <view
	            v-for="(item, index) in reportImages"
	            :key="'report-image-' + index"
	            class="image-card"
	          >
	            <image class="image-card-photo" :src="item.image_url" mode="aspectFill"></image>
	            <view class="image-card-meta">
	              <text class="image-card-date">{{ item.diary_date || '--' }}</text>
	              <text class="image-card-location">{{ item.location || item.diary_title || '旅行记录' }}</text>
	            </view>
	          </view>
	        </view>
	      </view>

	      <view class="stats-grid">
	        <view class="stats-card">
	          <text class="stats-value">{{ summaryStats.diary_count || 0 }}</text>
	          <text class="stats-label">篇日记</text>
        </view>
        <view class="stats-card">
          <text class="stats-value">{{ summaryStats.city_count || 0 }}</text>
          <text class="stats-label">个地点</text>
        </view>
        <view class="stats-card">
          <text class="stats-value">{{ formatDistance(summaryStats.total_distance_km) }}</text>
          <text class="stats-label">公里</text>
        </view>
        <view class="stats-card">
          <text class="stats-value">{{ formatScore(summaryStats.avg_emotion_score) }}</text>
          <text class="stats-label">平均情绪</text>
	        </view>
	      </view>

	      <view class="report-card">
	        <text class="card-title">旅程概述</text>
	        <text class="body-text">{{ report.summary }}</text>
	      </view>

      <view class="report-card" v-if="report.highlights.length">
        <text class="card-title">高光时刻</text>
        <view
          v-for="(item, index) in report.highlights"
          :key="'highlight-' + index"
          class="list-row"
        >
          <text class="list-index">{{ index + 1 }}</text>
          <text class="list-text">{{ item }}</text>
        </view>
      </view>

      <view class="report-card">
        <text class="card-title">情绪回顾</text>
        <text class="body-text">{{ report.emotion_review }}</text>
      </view>

      <view class="report-card" v-if="report.travel_preferences.length">
        <text class="card-title">旅行偏好</text>
        <view
          v-for="(item, index) in report.travel_preferences"
          :key="'preference-' + index"
          class="tag-row"
        >
          <text class="tag-dot"></text>
          <text class="tag-text">{{ item }}</text>
        </view>
      </view>

      <view class="report-card" v-if="report.next_trip_suggestions.length">
        <text class="card-title">下次旅行建议</text>
        <view
          v-for="(item, index) in report.next_trip_suggestions"
          :key="'suggestion-' + index"
          class="tag-row"
        >
          <text class="tag-dot tag-dot-accent"></text>
          <text class="tag-text">{{ item }}</text>
        </view>
      </view>

      <view v-if="report.memory_quote" class="quote-card">
        <text class="quote-mark">“</text>
        <text class="quote-text">{{ report.memory_quote }}</text>
      </view>
    </view>

    <view v-else class="empty-card">
      <text class="empty-title">{{ errorMessage || '还没有生成报告' }}</text>
      <text class="empty-text">
        {{ errorMessage || '选择一个时间范围后，手动生成一份属于这段旅程的总结。' }}
      </text>
    </view>
  </view>
</template>

<script>
import request from '../../utils/request.js'
import config from '../../api/config.js'

export default {
  data() {
    return {
      loading: false,
      exporting: false,
      rangeType: '30d',
      startDate: '',
      endDate: '',
      reportData: null,
      errorMessage: '',
      rangeOptions: [
        { label: '近7天', value: '7d' },
        { label: '近30天', value: '30d' },
        { label: '全部', value: 'all' },
        { label: '自定义', value: 'custom' },
      ],
    }
  },

  computed: {
    token() {
      return this.$store.state.token
    },

    report() {
      return this.reportData && this.reportData.report
        ? this.reportData.report
        : {
            report_title: '',
            report_subtitle: '',
            summary: '',
            highlights: [],
            emotion_review: '',
            travel_preferences: [],
            next_trip_suggestions: [],
            memory_quote: '',
          }
    },

    summaryStats() {
      return this.reportData && this.reportData.summary_stats
        ? this.reportData.summary_stats
        : {}
    },

    reportImages() {
      if (!this.reportData) return []
      if (Array.isArray(this.reportData.report_images)) {
        return this.reportData.report_images
      }
      if (this.reportData.cover_image) {
        return [this.reportData.cover_image]
      }
      return []
    },

    sourceLabel() {
      if (!this.reportData) return ''
      return this.reportData.source === 'dify' ? 'AI 工作流生成' : '本地智能总结'
    },
  },

  onLoad() {
    this.restoreCachedReport()
  },

  methods: {
    restoreCachedReport() {
      const cache = this.$store.state.reportCache || {}
      const cachedReportData = cache.reportData
      const hasCurrentImageShape =
        !cachedReportData ||
        Array.isArray(cachedReportData.report_images)

      if (cache.startDate && cache.endDate) {
        this.startDate = cache.startDate
        this.endDate = cache.endDate
      } else {
        this.initCustomRange()
      }

      this.rangeType = cache.rangeType || '30d'
      this.reportData = hasCurrentImageShape ? (cachedReportData || null) : null
      this.errorMessage = ''
    },

    initCustomRange() {
      this.endDate = this.formatDate(new Date())
      this.startDate = this.formatDate(this.offsetDate(-29))
    },

    offsetDate(days) {
      const next = new Date()
      next.setDate(next.getDate() + days)
      return next
    },

    formatDate(dateObj) {
      const year = dateObj.getFullYear()
      const month = String(dateObj.getMonth() + 1).padStart(2, '0')
      const day = String(dateObj.getDate()).padStart(2, '0')
      return `${year}-${month}-${day}`
    },

    selectRange(value) {
      this.rangeType = value
      if (value === 'custom' && (!this.startDate || !this.endDate)) {
        this.initCustomRange()
      }
    },

    handleStartDateChange(event) {
      this.startDate = event.detail.value
    },

    handleEndDateChange(event) {
      this.endDate = event.detail.value
    },

    formatPeriod(period) {
      if (!period) return ''
      return `${period.start_date} 至 ${period.end_date}`
    },

    formatScore(score) {
      if (score === null || score === undefined || score === '') return '--'
      const value = Number(score)
      if (Number.isNaN(value)) return '--'
      return value > 0 ? `+${value.toFixed(1)}` : value.toFixed(1)
    },

    formatDistance(distance) {
      if (distance === null || distance === undefined || distance === '') return '--'
      const value = Number(distance)
      if (Number.isNaN(value)) return '--'
      return value.toFixed(1)
    },

    generateReport() {
      if (!this.token) {
        uni.showToast({ title: '请先登录', icon: 'none' })
        return
      }
      if (this.loading) return

      const payload = { report_style: 'warm' }
      if (this.rangeType === 'custom') {
        if (!this.startDate || !this.endDate) {
          uni.showToast({ title: '请选择完整日期范围', icon: 'none' })
          return
        }
        if (this.startDate > this.endDate) {
          uni.showToast({ title: '开始日期不能晚于结束日期', icon: 'none' })
          return
        }
        payload.start_date = this.startDate
        payload.end_date = this.endDate
      } else {
        payload.preset = this.rangeType
      }

      this.loading = true
      this.errorMessage = ''
      uni.showLoading({ title: '生成中', mask: true })

      request({
        url: config.REPORT_GENERATE,
        method: 'POST',
        data: payload,
        header: {
          Authorization: 'Bearer ' + this.token,
        },
      })
        .then((res) => {
          this.reportData = res
          this.errorMessage = ''
          this.$store.commit('SET_REPORT_CACHE', {
            reportData: res,
            rangeType: this.rangeType,
            startDate: this.startDate,
            endDate: this.endDate,
          })
        })
        .catch((err) => {
          const msg = (err.data && err.data.msg) ? err.data.msg : '生成报告失败'
          this.reportData = null
          this.errorMessage = msg
          uni.showToast({ title: msg, icon: 'none' })
        })
        .finally(() => {
          this.loading = false
          uni.hideLoading()
        })
    },

    exportPdf() {
      if (!this.token) {
        uni.showToast({ title: '请先登录', icon: 'none' })
        return
      }
      if (!this.reportData || this.exporting) return

      this.exporting = true
      uni.showLoading({ title: '导出中', mask: true })

      request({
        url: config.REPORT_EXPORT_PDF,
        method: 'POST',
        data: this.reportData,
        header: {
          Authorization: 'Bearer ' + this.token,
        },
      })
        .then((res) => {
          const fileName = res.file_name
          if (!fileName) {
            throw new Error('未返回 PDF 文件名')
          }
          return this.downloadPdf(fileName)
        })
        .catch((err) => {
          const msg =
            (err && err.data && err.data.msg) ||
            err.message ||
            '导出 PDF 失败'
          uni.showToast({ title: msg, icon: 'none' })
        })
        .finally(() => {
          this.exporting = false
          uni.hideLoading()
        })
    },

    downloadPdf(fileName) {
      // #ifdef H5
      return new Promise((resolve, reject) => {
        uni.request({
          url: config.REPORT_DOWNLOAD + encodeURIComponent(fileName),
          method: 'GET',
          responseType: 'arraybuffer',
          header: {
            Authorization: 'Bearer ' + this.token,
          },
          success: (res) => {
            if (res.statusCode !== 200) {
              reject(new Error('PDF 下载失败'))
              return
            }
            const blob = new Blob([res.data], { type: 'application/pdf' })
            const objectUrl = window.URL.createObjectURL(blob)
            const link = document.createElement('a')
            link.href = objectUrl
            link.download = fileName
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
            window.URL.revokeObjectURL(objectUrl)
            uni.showToast({ title: 'PDF 已开始下载', icon: 'none' })
            resolve()
          },
          fail: reject,
        })
      })
      // #endif

      // #ifndef H5
      return new Promise((resolve, reject) => {
        uni.downloadFile({
          url: config.REPORT_DOWNLOAD + encodeURIComponent(fileName),
          header: {
            Authorization: 'Bearer ' + this.token,
          },
          success: (downloadRes) => {
            if (downloadRes.statusCode !== 200) {
              reject(new Error('PDF 下载失败'))
              return
            }
            uni.openDocument({
              filePath: downloadRes.tempFilePath,
              showMenu: true,
              success: resolve,
              fail: reject,
            })
          },
          fail: reject,
        })
      })
      // #endif
    },
  },
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  padding: 28rpx;
  background:
    radial-gradient(circle at top left, rgba(34, 197, 94, 0.14), transparent 30%),
    linear-gradient(180deg, #f6fbff 0%, #edf4ff 100%);
}

.hero-card,
.panel-card,
.report-card,
.quote-card,
.empty-card {
  background: rgba(255, 255, 255, 0.92);
  border-radius: 28rpx;
  box-shadow: 0 14rpx 40rpx rgba(15, 23, 42, 0.07);
  backdrop-filter: blur(8px);
}

.hero-card {
  padding: 34rpx 30rpx;
  margin-bottom: 24rpx;
}

.page-title {
  display: block;
  font-size: 42rpx;
  font-weight: 700;
  color: #0f172a;
}

.page-subtitle {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: #475569;
}

.panel-card {
  padding: 28rpx;
}

.section-title,
.card-title {
  display: block;
  font-size: 30rpx;
  font-weight: 700;
  color: #0f172a;
}

.preset-row {
  display: flex;
  flex-wrap: wrap;
  gap: 14rpx;
  margin-top: 20rpx;
}

.preset-chip {
  padding: 14rpx 24rpx;
  border-radius: 999rpx;
  background: #e2e8f0;
  color: #475569;
  font-size: 24rpx;
}

.preset-chip.active {
  background: linear-gradient(135deg, #0f6bff 0%, #1d9bf0 100%);
  color: #fff;
  box-shadow: 0 8rpx 18rpx rgba(29, 155, 240, 0.22);
}

.date-grid {
  display: flex;
  gap: 16rpx;
  margin-top: 22rpx;
}

.date-block {
  flex: 1;
  padding: 20rpx;
  border-radius: 20rpx;
  background: #f8fafc;
  border: 1rpx solid #dbeafe;
}

.date-label {
  display: block;
  font-size: 22rpx;
  color: #64748b;
}

.date-value {
  margin-top: 10rpx;
  font-size: 26rpx;
  font-weight: 600;
  color: #0f172a;
}

.generate-btn {
  margin-top: 24rpx;
  border-radius: 999rpx;
  background: linear-gradient(135deg, #0f6bff 0%, #1d9bf0 100%);
  color: #fff;
  font-size: 28rpx;
  font-weight: 600;
}

.panel-tip {
  display: block;
  margin-top: 16rpx;
  font-size: 22rpx;
  line-height: 1.7;
  color: #64748b;
}

.report-stack {
  margin-top: 24rpx;
}

.report-header,
.report-card,
.quote-card,
.empty-card {
  padding: 28rpx;
  margin-bottom: 20rpx;
}

.header-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 18rpx;
}

.source-badge {
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
  font-weight: 600;
}

.source-dify {
  background: rgba(14, 165, 233, 0.12);
  color: #0369a1;
}

.source-local {
  background: rgba(34, 197, 94, 0.12);
  color: #15803d;
}

.period-text {
  font-size: 22rpx;
  color: #64748b;
}

.report-title {
  display: block;
  font-size: 38rpx;
  line-height: 1.4;
  font-weight: 700;
  color: #0f172a;
}

.report-subtitle {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.8;
  color: #475569;
}

.export-btn {
  margin-top: 22rpx;
  border-radius: 999rpx;
  background: rgba(15, 107, 255, 0.08);
  color: #0f6bff;
  border: 1rpx solid rgba(15, 107, 255, 0.16);
  font-size: 24rpx;
  font-weight: 600;
}

.stats-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  margin-bottom: 20rpx;
}

.stats-card {
  width: calc(50% - 8rpx);
  box-sizing: border-box;
  padding: 24rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 10rpx 28rpx rgba(15, 23, 42, 0.05);
}

.stats-value {
  display: block;
  font-size: 34rpx;
  font-weight: 700;
  color: #0f6bff;
}

.stats-label {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: #64748b;
}

.body-text {
  display: block;
  margin-top: 16rpx;
  font-size: 25rpx;
  line-height: 1.9;
  color: #334155;
}

.report-images-card {
  overflow: hidden;
}

.images-tip {
  display: block;
  margin-top: 12rpx;
  font-size: 22rpx;
  line-height: 1.7;
  color: #64748b;
}

.images-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  margin-top: 18rpx;
}

.image-card {
  width: calc(50% - 8rpx);
  box-sizing: border-box;
  border-radius: 22rpx;
  overflow: hidden;
  background: #f8fbff;
  border: 1rpx solid #dbeafe;
}

.image-card-photo {
  width: 100%;
  height: 240rpx;
  display: block;
  background: #e2e8f0;
}

.image-card-meta {
  padding: 16rpx;
}

.image-card-date,
.image-card-location {
  display: block;
}

.image-card-date {
  font-size: 20rpx;
  color: #64748b;
}

.image-card-location {
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: #0f172a;
}

.list-row,
.tag-row {
  display: flex;
  align-items: flex-start;
  gap: 14rpx;
  margin-top: 18rpx;
}

.list-index {
  width: 38rpx;
  height: 38rpx;
  border-radius: 50%;
  text-align: center;
  line-height: 38rpx;
  font-size: 22rpx;
  font-weight: 700;
  color: #fff;
  background: #0f6bff;
  flex-shrink: 0;
}

.list-text,
.tag-text {
  flex: 1;
  font-size: 24rpx;
  line-height: 1.85;
  color: #334155;
}

.tag-dot {
  width: 14rpx;
  height: 14rpx;
  margin-top: 14rpx;
  border-radius: 50%;
  background: #0f6bff;
  flex-shrink: 0;
}

.tag-dot-accent {
  background: #22c55e;
}

.quote-card {
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
}

.quote-mark {
  position: absolute;
  top: 8rpx;
  left: 20rpx;
  font-size: 96rpx;
  color: rgba(255, 255, 255, 0.18);
  line-height: 1;
}

.quote-text {
  display: block;
  position: relative;
  z-index: 1;
  padding-left: 10rpx;
  font-size: 28rpx;
  line-height: 1.9;
  color: #f8fafc;
}

.empty-card {
  margin-top: 24rpx;
  text-align: center;
}

.empty-title {
  display: block;
  font-size: 30rpx;
  font-weight: 700;
  color: #0f172a;
}

.empty-text {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.8;
  color: #64748b;
}
</style>

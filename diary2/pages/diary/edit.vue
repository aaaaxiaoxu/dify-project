<template>
  <view class="container">
    <view class="header">
      <text class="title">{{ isEdit ? '编辑日记' : '写日记' }}</text>
    </view>
    
    <view class="form-group">
      <input 
        class="form-input title-input" 
        placeholder="请输入标题" 
        v-model="diaryData.title"
      />
    </view>
    
    <view class="form-group">
      <view class="location-section">
        <input 
          class="form-input location-input" 
          placeholder="请输入地点，如：北京天安门" 
          v-model="diaryData.location"
          @input="onLocationTextInput"
        />
        <view class="location-btns">
          <button class="location-btn location-btn-secondary" @click="geocodeAddress" :disabled="geocodingAddress">
            <text v-if="!geocodingAddress">解析为经纬度</text>
            <text v-else>解析中...</text>
          </button>
          <button class="location-btn" @click="getCurrentLocation" :disabled="gettingLocation">
            <text v-if="!gettingLocation">获取当前位置</text>
            <text v-else>定位中...</text>
          </button>
        </view>
      </view>
      <view class="coord-hint">
        <text :class="coordsReady ? 'coord-ok' : 'coord-warn'">
          {{ coordsReady ? '已具备经纬度，可以保存' : '保存前须完成：点「解析为经纬度」或「获取当前位置」' }}
        </text>
      </view>
    </view>
    
    <view class="form-group">
      <view class="date-section">
        <text class="label">日期:</text>
        <picker mode="date" :value="diaryData.date" @change="handleDateChange">
          <view class="date-display">
            {{ diaryData.date || '请选择日期' }}
          </view>
        </picker>
      </view>
    </view>
    
    <view class="form-group">
      <view class="emotion-section">
        <text class="label">当时心情:</text>
        <view class="emotion-options">
          <view 
            v-for="(emotion, index) in emotionOptions" 
            :key="index"
            class="emotion-option"
            :class="{ active: diaryData.emotion === emotion.value }"
            @click="selectEmotion(emotion.value)"
          >
            <text>{{ emotion.label }}</text>
          </view>
        </view>
      </view>
    </view>
    
    <view class="form-group editor-card">
      <text class="label editor-section-title">正文（富文本）</text>
      <text class="toolbar-tip">以下按钮已全部展示，自动换行；不同端（小程序/App/H5）支持程度可能略有差异。</text>
      <view class="editor-toolbar">
        <view class="toolbar-grid">
          <view
            :class="['tool-btn', formats.bold ? 'tool-active' : '']"
            data-cmd="bold"
            @tap="onFormatCommand"
          >加粗</view>
          <view
            :class="['tool-btn', formats.italic ? 'tool-active' : '']"
            data-cmd="italic"
            @tap="onFormatCommand"
          >斜体</view>
          <view
            :class="['tool-btn', formats.underline ? 'tool-active' : '']"
            data-cmd="underline"
            @tap="onFormatCommand"
          >下划</view>
          <view
            :class="['tool-btn', formats.strike ? 'tool-active' : '']"
            data-cmd="strike"
            @tap="onFormatCommand"
          >删除线</view>
          <view
            :class="['tool-btn', formats.header == 2 ? 'tool-active' : '']"
            data-cmd="header"
            data-val="2"
            @tap="onFormatCommand"
          >小标题</view>
          <view
            :class="['tool-btn', 'tool-color', formats.color === '#e53935' ? 'tool-active' : '']"
            data-cmd="color"
            data-val="#e53935"
            style="color:#e53935"
            @tap="onFormatCommand"
          >红</view>
          <view
            :class="['tool-btn', 'tool-color', formats.color === '#1e88e5' ? 'tool-active' : '']"
            data-cmd="color"
            data-val="#1e88e5"
            style="color:#1e88e5"
            @tap="onFormatCommand"
          >蓝</view>
          <view
            :class="['tool-btn', 'tool-color', formats.color === '#43a047' ? 'tool-active' : '']"
            data-cmd="color"
            data-val="#43a047"
            style="color:#43a047"
            @tap="onFormatCommand"
          >绿</view>
          <view
            :class="['tool-btn', 'tool-color', formats.color === '#fb8c00' ? 'tool-active' : '']"
            data-cmd="color"
            data-val="#fb8c00"
            style="color:#fb8c00"
            @tap="onFormatCommand"
          >橙</view>
          <view
            :class="['tool-btn', 'tool-color', formats.color === '#333333' ? 'tool-active' : '']"
            data-cmd="color"
            data-val="#333333"
            style="color:#333"
            @tap="onFormatCommand"
          >黑</view>
          <view
            :class="['tool-btn', formats.backgroundColor == '#fff59d' ? 'tool-active' : '']"
            data-cmd="backgroundColor"
            data-val="#fff59d"
            @tap="onFormatCommand"
          >高亮</view>
          <view
            :class="['tool-btn', formats.list === 'ordered' ? 'tool-active' : '']"
            data-cmd="list"
            data-val="ordered"
            @tap="onFormatCommand"
          >有序</view>
          <view
            :class="['tool-btn', formats.list === 'bullet' ? 'tool-active' : '']"
            data-cmd="list"
            data-val="bullet"
            @tap="onFormatCommand"
          >无序</view>
          <view
            :class="['tool-btn', formats.align === 'left' ? 'tool-active' : '']"
            data-cmd="align"
            data-val="left"
            @tap="onFormatCommand"
          >左对齐</view>
          <view
            :class="['tool-btn', formats.align === 'center' ? 'tool-active' : '']"
            data-cmd="align"
            data-val="center"
            @tap="onFormatCommand"
          >居中</view>
          <view
            :class="['tool-btn', formats.align === 'right' ? 'tool-active' : '']"
            data-cmd="align"
            data-val="right"
            @tap="onFormatCommand"
          >右对齐</view>
          <view
            :class="['tool-btn', formats.align === 'justify' ? 'tool-active' : '']"
            data-cmd="align"
            data-val="justify"
            @tap="onFormatCommand"
          >两端</view>
          <view class="tool-btn tool-img" @tap="insertEditorImage">插图</view>
          <view class="tool-btn" @tap="editorUndo">撤销</view>
          <view class="tool-btn" @tap="editorRedo">重做</view>
          <view class="tool-btn" @tap="insertEditorDivider">分割线</view>
          <view class="tool-btn tool-muted" @tap="removeEditorFormat">清格式</view>
        </view>
      </view>
      <editor
        id="diary-editor"
        class="ql-container diary-editor"
        placeholder="记录下这次旅行的美好时光..."
        show-img-size
        show-img-toolbar
        show-img-resize
        @ready="onEditorReady"
        @statuschange="onEditorStatusChange"
        @input="onEditorInput"
      />
    </view>
    
    <view class="form-group">
      <view class="image-section">
        <text class="label">照片:</text>
        <view class="image-upload-area">
          <view 
            v-for="(image, index) in diaryData.images" 
            :key="index"
            class="uploaded-image"
          >
            <image :src="image" mode="aspectFill" />
            <text class="remove-image" @click="removeImage(index)">×</text>
          </view>
          
          <view class="upload-button" @click="chooseImage" v-if="diaryData.images.length < 9">
            <text class="plus-icon">+</text>
            <text class="upload-text">添加照片</text>
          </view>
        </view>
      </view>
    </view>
    
    <view class="form-group">
      <view class="video-section">
        <text class="label">视频:</text>
        <view class="video-upload-area">
          <view 
            v-for="(video, index) in diaryData.videos" 
            :key="index"
            class="uploaded-video"
          >
            <video :src="video.url" class="video-preview" controls></video>
            <text class="remove-video" @click="removeVideo(index)">×</text>
          </view>
          
          <view class="upload-button" @click="chooseVideo" v-if="diaryData.videos.length < 5">
            <text class="plus-icon">+</text>
            <text class="upload-text">添加视频</text>
          </view>
        </view>
      </view>
    </view>
    
    <view class="ai-suggestion">
      <view class="suggestion-header">
        <text class="suggestion-title">AI写作建议</text>
        <button class="refresh-btn" @click="getAiSuggestion" :disabled="gettingSuggestion">
          <text v-if="!gettingSuggestion">刷新建议</text>
          <text v-else>生成中...</text>
        </button>
      </view>
      
      <view class="suggestion-content" v-if="aiSuggestion">
        <text>{{ aiSuggestion }}</text>
      </view>
      
      <view class="suggestion-placeholder" v-else>
        <text>点击"刷新建议"获取AI写作建议</text>
      </view>
    </view>
    
    <view class="form-actions">
      <button class="save-btn" @click="saveDiary">
        <text>{{ isEdit ? '更新日记' : '保存日记' }}</text>
      </button>
      <button class="cancel-btn" @click="cancelEdit">
        <text>取消</text>
      </button>
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
      isEdit: false,
      gettingLocation: false,
      geocodingAddress: false,
      gettingSuggestion: false,
      diaryId: null,
      diaryData: {
        title: '',
        location: '',
        date: '',
        emotion: '',
        content: '',
        images: [],
        videos: [],
        latitude: null,
        longitude: null
      },
      emotionOptions: [
        { label: '😊 开心', value: '开心' },
        { label: '😢 感动', value: '感动' },
        { label: '🤩 兴奋', value: '兴奋' },
        { label: '😌 平静', value: '平静' },
        { label: '😔 忧郁', value: '忧郁' },
        { label: '🥺 思念', value: '思念' }
      ],
      aiSuggestion: '',
      formats: {},
      editorCtx: null,
      _pendingEditorHtml: null,
      /** 由定位/加载回填地点时避免 @input 误清空经纬度 */
      _suppressLocationCoordClear: false
    }
  },

  computed: {
    coordsReady() {
      const lat = Number(this.diaryData.latitude)
      const lng = Number(this.diaryData.longitude)
      return (
        Number.isFinite(lat) &&
        Number.isFinite(lng) &&
        lat >= -90 &&
        lat <= 90 &&
        lng >= -180 &&
        lng <= 180
      )
    }
  },
  
  onLoad(options) {
    if (options.id) {
      this.isEdit = true
      this.diaryId = options.id
      this.loadDiaryData(options.id)
    } else {
      // 设置默认日期为今天
      const today = new Date()
      this.diaryData.date = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
    }
  },
  
  methods: {
    onEditorReady() {
      const q = uni.createSelectorQuery().in(this)
      q.select('#diary-editor')
        .context((res) => {
          if (!res || !res.context) return
          this.editorCtx = res.context
          const pending = this._pendingEditorHtml
          if (pending !== null && pending !== undefined) {
            this.editorSetHtml(pending)
            this._pendingEditorHtml = null
          }
        })
        .exec()
    },

    onEditorStatusChange(e) {
      this.formats = (e && e.detail) || {}
    },

    onEditorInput(e) {
      const html = e.detail && e.detail.html
      if (html !== undefined) {
        this.diaryData.content = html
      }
    },

    editorSetHtml(html) {
      if (!this.editorCtx) return
      const h = html && String(html).trim() ? html : '<p><br></p>'
      this.editorCtx.setContents({
        html: h
      })
      this.diaryData.content = h
    },

    onFormatCommand(e) {
      if (!this.editorCtx) {
        uni.showToast({ title: '编辑器未就绪', icon: 'none' })
        return
      }
      const ds = (e.currentTarget && e.currentTarget.dataset) || {}
      const cmd = ds.cmd
      const val = ds.val
      if (!cmd) return
      if (val !== undefined && val !== '') {
        if (cmd === 'header') {
          this.editorCtx.format(cmd, Number(val))
        } else {
          this.editorCtx.format(cmd, val)
        }
      } else {
        this.editorCtx.format(cmd)
      }
    },

    editorUndo() {
      if (!this.editorCtx) {
        uni.showToast({ title: '编辑器未就绪', icon: 'none' })
        return
      }
      this.editorCtx.undo()
    },

    editorRedo() {
      if (!this.editorCtx) {
        uni.showToast({ title: '编辑器未就绪', icon: 'none' })
        return
      }
      this.editorCtx.redo()
    },

    insertEditorDivider() {
      if (!this.editorCtx) {
        uni.showToast({ title: '编辑器未就绪', icon: 'none' })
        return
      }
      this.editorCtx.insertDivider({})
    },

    removeEditorFormat() {
      if (!this.editorCtx) {
        uni.showToast({ title: '编辑器未就绪', icon: 'none' })
        return
      }
      this.editorCtx.removeFormat()
    },

    isRemoteMediaUrl(value) {
      return typeof value === 'string' && /^https?:\/\//i.test(value)
    },

    uploadMedia(filePath, mediaType) {
      const token = this.$store && this.$store.state ? this.$store.state.token : ''
      return new Promise((resolve, reject) => {
        uni.uploadFile({
          url: config.FILE_UPLOAD,
          filePath,
          name: 'file',
          formData: {
            media_type: mediaType
          },
          header: {
            Authorization: 'Bearer ' + token
          },
          success: (res) => {
            try {
              const body = typeof res.data === 'string' ? JSON.parse(res.data) : res.data
              if (body && body.url) {
                resolve(body)
              } else {
                reject(new Error((body && body.msg) || '上传失败'))
              }
            } catch (err) {
              reject(err)
            }
          },
          fail: reject
        })
      })
    },

    uploadEditorImage(filePath) {
      return this.uploadMedia(filePath, 'image').then((res) => res.url)
    },

    async uploadPendingDiaryMedia() {
      const nextImages = []
      for (let i = 0; i < this.diaryData.images.length; i += 1) {
        const image = this.diaryData.images[i]
        if (this.isRemoteMediaUrl(image)) {
          nextImages.push(image)
          continue
        }
        uni.showLoading({ title: `上传图片 ${i + 1}/${this.diaryData.images.length}`, mask: true })
        const uploaded = await this.uploadMedia(image, 'image')
        nextImages.push(uploaded.url)
      }

      const nextVideos = []
      for (let i = 0; i < this.diaryData.videos.length; i += 1) {
        const video = this.diaryData.videos[i] || {}
        let videoUrl = video.url
        let thumbnailUrl = video.thumbnail || ''

        if (!this.isRemoteMediaUrl(videoUrl)) {
          uni.showLoading({ title: `上传视频 ${i + 1}/${this.diaryData.videos.length}`, mask: true })
          const uploadedVideo = await this.uploadMedia(videoUrl, 'video')
          videoUrl = uploadedVideo.url
        }

        if (thumbnailUrl && !this.isRemoteMediaUrl(thumbnailUrl)) {
          uni.showLoading({ title: `上传封面 ${i + 1}/${this.diaryData.videos.length}`, mask: true })
          const uploadedThumb = await this.uploadMedia(thumbnailUrl, 'image')
          thumbnailUrl = uploadedThumb.url
        }

        nextVideos.push({
          url: videoUrl,
          thumbnail: thumbnailUrl
        })
      }

      this.diaryData.images = nextImages
      this.diaryData.videos = nextVideos
    },

    insertEditorImage() {
      if (!this.editorCtx) {
        uni.showToast({ title: '编辑器未就绪', icon: 'none' })
        return
      }
      uni.chooseImage({
        count: 1,
        success: (res) => {
          const path = res.tempFilePaths && res.tempFilePaths[0]
          if (!path) return
          uni.showLoading({ title: '上传中' })
          this.uploadEditorImage(path)
            .then((url) => {
              uni.hideLoading()
              this.editorCtx.insertImage({
                src: url,
                alt: '日记插图'
              })
            })
            .catch(() => {
              uni.hideLoading()
              uni.showToast({ title: '图片上传失败', icon: 'none' })
            })
        }
      })
    },

    reverseGeocode(latitude, longitude) {
      const token = this.$store && this.$store.state ? this.$store.state.token : ''
      return request({
        url: config.MAP_REVERSE_GEOCODE,
        method: 'POST',
        data: { latitude, longitude },
        header: {
          'Authorization': 'Bearer ' + token
        }
      })
    },

    onLocationTextInput() {
      if (this._suppressLocationCoordClear) return
      this.diaryData.latitude = null
      this.diaryData.longitude = null
    },

    geocodeAddress() {
      const addr = (this.diaryData.location || '').trim()
      if (!addr) {
        uni.showToast({ title: '请先输入地点', icon: 'none' })
        return
      }
      const token = this.$store && this.$store.state ? this.$store.state.token : ''
      if (!token) {
        uni.showToast({ title: '请先登录', icon: 'none' })
        return
      }
      this.geocodingAddress = true
      request({
        url: config.MAP_GEOCODE,
        method: 'POST',
        data: { address: addr },
        header: {
          Authorization: 'Bearer ' + token
        }
      })
        .then((res) => {
          this.geocodingAddress = false
          if (res.latitude != null && res.longitude != null) {
            this.diaryData.latitude = res.latitude
            this.diaryData.longitude = res.longitude
            uni.showToast({ title: '已解析，可保存日记', icon: 'success' })
          } else {
            uni.showToast({ title: '未能解析该地点', icon: 'none' })
          }
        })
        .catch((err) => {
          this.geocodingAddress = false
          const msg = err && err.data && err.data.msg
          uni.showToast({ title: msg || '解析失败，请检查地图 Key 或网络', icon: 'none' })
        })
    },

    parseLocationText(res) {
      // 不同端返回结构不一致：可能是 address(对象/字符串) 或 addressInfo
      const addressCandidate = res.addressInfo || res.address
      if (!addressCandidate) return ''

      // 兼容字符串地址
      if (typeof addressCandidate === 'string') {
        return addressCandidate.trim()
      }

      // 兼容对象地址
      const address = addressCandidate
      let locationStr = ''
      if (address.province) locationStr += address.province
      if (address.city) locationStr += address.city
      if (address.district) locationStr += address.district
      if (address.streetNumber && address.streetNumber.street) locationStr += address.streetNumber.street
      else if (address.street) locationStr += address.street
      if (address.poiName) locationStr += address.poiName
      return locationStr
    },

    loadDiaryData(id) {
      // 调用后端获取日记详情接口
      request({
        url: config.DIARY_DETAIL.replace('<int:diary_id>', id),
        method: 'GET',
        header: {
          'Authorization': 'Bearer ' + this.$store.state.token
        }
      }).then(res => {
        this.diaryData = {
          title: res.title,
          location: res.location,
          date: res.date,
          emotion: res.emotion,
          content: res.content || '',
          images: res.images || [],
          videos: res.videos || [],
          latitude: res.latitude || null,
          longitude: res.longitude || null
        }
        this.$nextTick(() => {
          if (this.editorCtx) {
            this.editorSetHtml(this.diaryData.content)
          } else {
            this._pendingEditorHtml = this.diaryData.content
          }
        })
      }).catch(err => {
        uni.showToast({
          title: '加载日记失败',
          icon: 'none'
        })
      })
    },
    
    handleDateChange(e) {
      this.diaryData.date = e.detail.value
    },
    
    selectEmotion(emotion) {
      this.diaryData.emotion = emotion
    },
    
    getCurrentLocation() {
      this.gettingLocation = true
      
      // 使用uni.getLocation获取准确位置
      uni.getLocation({
        type: 'gcj02', // 使用国测局坐标系，适用于腾讯地图
        geocode: true, // 获取详细地址信息
        success: (res) => {
          console.log('定位成功', res)
          this.gettingLocation = false
          
          // 保存经纬度到数据中
          this.diaryData.latitude = res.latitude
          this.diaryData.longitude = res.longitude
          this._suppressLocationCoordClear = true

          const releaseSuppress = () => {
            this.$nextTick(() => {
              this._suppressLocationCoordClear = false
            })
          }

          const parsedLocation = this.parseLocationText(res)
          if (parsedLocation) {
            this.diaryData.location = parsedLocation
            releaseSuppress()
          } else if (typeof res.latitude === 'number' && typeof res.longitude === 'number') {
            // 先尝试后端反查中文地址，失败再回退到经纬度文本
            this.reverseGeocode(res.latitude, res.longitude)
              .then((geoRes) => {
                if (geoRes && geoRes.address) {
                  this.diaryData.location = geoRes.address
                } else {
                  this.diaryData.location = `${res.latitude.toFixed(6)}, ${res.longitude.toFixed(6)}`
                }
                releaseSuppress()
              })
              .catch(() => {
                this.diaryData.location = `${res.latitude.toFixed(6)}, ${res.longitude.toFixed(6)}`
                releaseSuppress()
              })
          } else {
            this.diaryData.location = '未知位置'
            releaseSuppress()
          }
          
          uni.showToast({
            title: '定位成功',
            icon: 'success'
          })
        },
        fail: (err) => {
          console.error('定位失败', err)
          this.gettingLocation = false
          
          // 定位失败时使用模拟数据
          this._suppressLocationCoordClear = true
          this.diaryData.latitude = 30.242289
          this.diaryData.longitude = 120.143669
          this.diaryData.location = '杭州市西湖区'
          this.$nextTick(() => {
            this._suppressLocationCoordClear = false
          })
          
          uni.showToast({
            title: '定位失败，使用默认位置',
            icon: 'none'
          })
        }
      })
    },
    
    chooseImage() {
      uni.chooseImage({
        count: 9 - this.diaryData.images.length,
        success: (res) => {
          this.diaryData.images = [...this.diaryData.images, ...res.tempFilePaths]
        }
      })
    },
    
    removeImage(index) {
      this.diaryData.images.splice(index, 1)
    },
    
    chooseVideo() {
      uni.chooseVideo({
        success: (res) => {
          if (this.diaryData.videos.length < 5) {
            this.diaryData.videos.push({
              url: res.tempFilePath,
              thumbnail: '' // 实际应用中可以从视频中提取缩略图
            })
          } else {
            uni.showToast({
              title: '最多只能上传5个视频',
              icon: 'none'
            })
          }
        }
      })
    },
    
    removeVideo(index) {
      this.diaryData.videos.splice(index, 1)
    },
    
    getAiSuggestion() {
      this.gettingSuggestion = true
      const send = (content) => {
        request({
          url: config.AI_ANALYSIS,
          method: 'POST',
          data: {
            content: content || ''
          },
          header: {
            'Authorization': 'Bearer ' + this.$store.state.token
          }
        })
          .then((res) => {
            this.gettingSuggestion = false
            let suggestionText = res.emotion_analysis || ''

            if (res.keywords && res.keywords.length > 0) {
              suggestionText += `\n\n关键词: ${res.keywords.join(', ')}`
            }

            if (res.travel_advice) {
              suggestionText += `\n\n旅行建议: ${res.travel_advice}`
            }

            if (res.writing_style) {
              suggestionText += `\n\n写作风格: ${res.writing_style}`
            }

            if (res.writing_suggestion) {
              suggestionText += `\n\n写作建议: ${res.writing_suggestion}`
            }

            this.aiSuggestion =
              suggestionText || '你可以描述一下当时的感受和周围的环境。'
          })
          .catch(() => {
            this.gettingSuggestion = false
            this.aiSuggestion = '你可以描述一下当时的感受和周围的环境。'
          })
      }

      if (this.editorCtx) {
        this.editorCtx.getContents({
          success: (r) => {
            const html = (r && r.html) || this.diaryData.content || ''
            send(html)
          },
          fail: () => send(this.diaryData.content || '')
        })
      } else {
        send(this.diaryData.content || '')
      }
    },
    
    saveDiary() {
      if (!this.diaryData.title) {
        uni.showToast({
          title: '请输入标题',
          icon: 'none'
        })
        return
      }
      
      if (!this.diaryData.location) {
        uni.showToast({
          title: '请输入地点',
          icon: 'none'
        })
        return
      }

      if (!this.coordsReady) {
        uni.showToast({
          title: '请先点「解析为经纬度」或「获取当前位置」',
          icon: 'none'
        })
        return
      }
      
      if (!this.diaryData.date) {
        uni.showToast({
          title: '请选择日期',
          icon: 'none'
        })
        return
      }
      
      if (!this.diaryData.emotion) {
        uni.showToast({
          title: '请选择心情',
          icon: 'none'
        })
        return
      }
      
      if (!this.editorCtx) {
        uni.showToast({
          title: '编辑器未就绪，请稍候',
          icon: 'none'
        })
        return
      }

      this.editorCtx.getContents({
        success: (r) => {
          const html = (r && r.html) || ''
          const text = ((r && r.text) || '').trim()
          const hasImg = /<img\s/i.test(html)
          if (!text && !hasImg) {
            uni.showToast({
              title: '请输入正文或插入图片',
              icon: 'none'
            })
            return
          }
          this.diaryData.content = html
          this.submitDiaryRequest()
        },
        fail: () => {
          const fallback = this.diaryData.content || ''
          if (!stripHtml(fallback) && !/<img\s/i.test(fallback)) {
            uni.showToast({
              title: '请输入正文或插入图片',
              icon: 'none'
            })
            return
          }
          this.submitDiaryRequest()
        }
      })
    },

    async submitDiaryRequest() {
      const url = this.isEdit ? config.DIARY_UPDATE.replace('<int:diary_id>', this.diaryId) : config.DIARY_CREATE
      const method = this.isEdit ? 'PUT' : 'POST'

      const runSave = () =>
        request({
          url: url,
          method: method,
          data: {
            title: this.diaryData.title,
            location: this.diaryData.location,
            date: this.diaryData.date,
            emotion: this.diaryData.emotion,
            content: this.diaryData.content,
            images: this.diaryData.images,
            videos: this.diaryData.videos,
            latitude: this.diaryData.latitude,
            longitude: this.diaryData.longitude
          },
          header: {
            'Authorization': 'Bearer ' + this.$store.state.token
          }
        })

      uni.showLoading({
        title: '准备上传媒体...',
        mask: true
      })

      try {
        await this.uploadPendingDiaryMedia()
        uni.showLoading({
          title: '保存中...',
          mask: true
        })

        const res = await runSave()
        uni.hideLoading()

        if (res.msg === '创建成功' || res.msg === '更新成功' || res.diary_id) {
          uni.showToast({
            title: this.isEdit ? '更新成功' : '创建成功',
            icon: 'success'
          })

          setTimeout(() => {
            uni.navigateBack()
          }, 1500)
        } else {
          uni.showToast({
            title: res.msg || '保存失败',
            icon: 'none'
          })
        }
      } catch (err) {
        uni.hideLoading()
        console.error('保存日记失败:', err)
        if (err && err.data && (err.data.msg === '创建成功' || err.data.msg === '更新成功')) {
          uni.showToast({
            title: this.isEdit ? '更新成功' : '创建成功',
            icon: 'success'
          })

          setTimeout(() => {
            uni.navigateBack()
          }, 1500)
        } else {
          const msg =
            (err && err.data && err.data.msg) ||
            err.message ||
            '保存失败'
          uni.showToast({
            title: msg,
            icon: 'none'
          })
        }
      }
    },
    
    cancelEdit() {
      uni.navigateBack()
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

.form-group {
  margin-bottom: 30rpx;
  background: #fff;
  border-radius: 20rpx;
  padding: 20rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.05);
  transition: all 0.3s ease;
}

.form-group:hover {
  box-shadow: 0 8rpx 25rpx rgba(0,0,0,0.1);
}

.form-input {
  width: 100%;
  padding: 20rpx;
  font-size: 28rpx;
  border: none;
  outline: none;
  background: #f8f8f8;
  border-radius: 10rpx;
}

.title-input {
  font-size: 36rpx;
  font-weight: bold;
}

.location-section {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16rpx;
}

.location-input {
  flex: 1;
  min-width: 200rpx;
}

.location-btns {
  display: flex;
  flex-shrink: 0;
  flex-wrap: wrap;
  gap: 12rpx;
}

.location-btn {
  flex-shrink: 0;
  padding: 15rpx 20rpx;
  background: linear-gradient(135deg, #007AFF 0%, #00d4ff 100%);
  color: white;
  border: none;
  border-radius: 10rpx;
  font-size: 24rpx;
  box-shadow: 0 4rpx 10rpx rgba(0,122,255,0.3);
  transition: all 0.3s ease;
}

.location-btn-secondary {
  background: linear-gradient(135deg, #5a67d8 0%, #7c3aed 100%);
  box-shadow: 0 4rpx 10rpx rgba(90,103,216,0.35);
}

.location-btn:hover {
  transform: translateY(-2rpx);
  box-shadow: 0 6rpx 15rpx rgba(0,122,255,0.4);
}

.coord-hint {
  margin-top: 16rpx;
  padding: 0 8rpx;
}

.coord-ok {
  font-size: 24rpx;
  color: #2e7d32;
}

.coord-warn {
  font-size: 24rpx;
  color: #c62828;
}

.date-section {
  display: flex;
  align-items: center;
}

.label {
  font-size: 28rpx;
  margin-right: 20rpx;
  color: #333;
  font-weight: 500;
}

.date-display {
  flex: 1;
  padding: 20rpx;
  background: #f8f8f8;
  border-radius: 10rpx;
  font-size: 28rpx;
}

.emotion-section {
  display: flex;
  flex-direction: column;
}

.emotion-options {
  display: flex;
  flex-wrap: wrap;
  margin-top: 20rpx;
}

.emotion-option {
  padding: 15rpx 25rpx;
  margin: 10rpx;
  background: #f8f8f8;
  border-radius: 30rpx;
  font-size: 24rpx;
  transition: all 0.3s ease;
}

.emotion-option:hover {
  transform: translateY(-2rpx);
}

.emotion-option.active {
  background: linear-gradient(135deg, #007AFF 0%, #00d4ff 100%);
  color: white;
  box-shadow: 0 4rpx 10rpx rgba(0,122,255,0.3);
}

.editor-section-title {
  display: block;
  margin-bottom: 8rpx;
}

.toolbar-tip {
  display: block;
  font-size: 22rpx;
  color: #888;
  line-height: 1.4;
  margin-bottom: 16rpx;
}

.editor-toolbar {
  width: 100%;
  margin-bottom: 16rpx;
}

.toolbar-grid {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  align-items: center;
  width: 100%;
}

.tool-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 12rpx 18rpx;
  margin-right: 12rpx;
  margin-bottom: 12rpx;
  font-size: 24rpx;
  color: #333;
  background: #f0f4f8;
  border-radius: 8rpx;
  box-sizing: border-box;
}

.tool-btn.tool-muted {
  background: #e8e8e8;
  color: #666;
}

.tool-btn.tool-active {
  background: #d6e8ff;
  color: #007aff;
  font-weight: 600;
}

.tool-btn.tool-img {
  background: #e8f4ff;
  color: #007aff;
}

.diary-editor {
  width: 100%;
  min-height: 360rpx;
  padding: 16rpx;
  box-sizing: border-box;
  background: #f8f8f8;
  border-radius: 10rpx;
  font-size: 28rpx;
  line-height: 1.6;
}

.image-section, .video-section {
  display: flex;
  flex-direction: column;
}

.image-upload-area, .video-upload-area {
  display: flex;
  flex-wrap: wrap;
  margin-top: 20rpx;
}

.uploaded-image, .uploaded-video {
  position: relative;
  width: 150rpx;
  height: 150rpx;
  margin: 10rpx;
}

.uploaded-image image {
  width: 100%;
  height: 100%;
  border-radius: 10rpx;
}

.video-preview {
  width: 100%;
  height: 100%;
  border-radius: 10rpx;
}

.remove-image, .remove-video {
  position: absolute;
  top: -15rpx;
  right: -15rpx;
  width: 40rpx;
  height: 40rpx;
  background-color: #ff4d4f;
  border-radius: 50%;
  color: white;
  text-align: center;
  line-height: 40rpx;
  font-size: 28rpx;
  box-shadow: 0 2rpx 5rpx rgba(0,0,0,0.2);
}

.upload-button {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: 150rpx;
  height: 150rpx;
  margin: 10rpx;
  border: 2rpx dashed #007AFF;
  border-radius: 10rpx;
  transition: all 0.3s ease;
}

.upload-button:hover {
  background-color: rgba(0,122,255,0.1);
}

.plus-icon {
  font-size: 60rpx;
  color: #007AFF;
}

.upload-text {
  font-size: 20rpx;
  color: #007AFF;
}

.ai-suggestion {
  background: #fff;
  border-radius: 20rpx;
  padding: 20rpx;
  margin-bottom: 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.05);
}

.suggestion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.suggestion-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
}

.refresh-btn {
  padding: 10rpx 20rpx;
  background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
  color: white;
  border: none;
  border-radius: 10rpx;
  font-size: 24rpx;
  box-shadow: 0 4rpx 10rpx rgba(106,17,203,0.3);
  transition: all 0.3s ease;
}

.refresh-btn:hover {
  transform: translateY(-2rpx);
  box-shadow: 0 6rpx 15rpx rgba(106,17,203,0.4);
}

.refresh-btn[disabled] {
  background: #ccc;
  box-shadow: none;
}

.suggestion-content {
  padding: 20rpx;
  background: #f8f8f8;
  border-radius: 10rpx;
  font-size: 26rpx;
  line-height: 1.5;
}

.suggestion-placeholder {
  padding: 20rpx;
  text-align: center;
  color: #999;
  font-size: 26rpx;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  padding-bottom: 30rpx;
}

.save-btn, .cancel-btn {
  flex: 1;
  height: 100rpx;
  border: none;
  border-radius: 15rpx;
  font-size: 32rpx;
  margin: 0 10rpx;
  box-shadow: 0 4rpx 10rpx rgba(0,0,0,0.1);
  transition: all 0.3s ease;
}

.save-btn {
  background: linear-gradient(135deg, #007AFF 0%, #00d4ff 100%);
  color: white;
}

.cancel-btn {
  background: #f8f8f8;
  color: #333;
}

.save-btn:hover, .cancel-btn:hover {
  transform: translateY(-5rpx);
  box-shadow: 0 8rpx 15rpx rgba(0,0,0,0.15);
}
</style>

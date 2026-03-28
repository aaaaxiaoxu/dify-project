<template>
  <view class="container">
    <view class="header">
      <text class="title">找回密码</text>
      <text class="subtitle">使用账号和绑定手机号重置密码</text>
    </view>

    <view class="form-card">
      <view class="input-group">
        <input
          class="form-input"
          type="text"
          placeholder="请输入用户名或手机号"
          v-model="formData.account"
        />
      </view>

      <view class="input-group">
        <input
          class="form-input"
          type="text"
          placeholder="请输入绑定手机号"
          v-model="formData.phone"
        />
      </view>

      <view class="input-group">
        <input
          class="form-input"
          type="password"
          placeholder="请输入新密码"
          v-model="formData.newPassword"
        />
      </view>

      <view class="input-group">
        <input
          class="form-input"
          type="password"
          placeholder="请确认新密码"
          v-model="formData.confirmPassword"
        />
      </view>

      <button class="submit-btn" @click="handleResetPassword">重置密码</button>

      <view class="footer-link">
        <text @click="goToLogin">返回登录</text>
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
      formData: {
        account: '',
        phone: '',
        newPassword: '',
        confirmPassword: ''
      }
    }
  },

  methods: {
    handleResetPassword() {
      const account = (this.formData.account || '').trim()
      const phone = (this.formData.phone || '').trim()
      const newPassword = this.formData.newPassword || ''
      const confirmPassword = this.formData.confirmPassword || ''

      if (!account) {
        uni.showToast({ title: '请输入用户名或手机号', icon: 'none' })
        return
      }

      if (!phone) {
        uni.showToast({ title: '请输入绑定手机号', icon: 'none' })
        return
      }

      if (!newPassword) {
        uni.showToast({ title: '请输入新密码', icon: 'none' })
        return
      }

      if (newPassword.length < 6) {
        uni.showToast({ title: '密码至少 6 位', icon: 'none' })
        return
      }

      if (newPassword !== confirmPassword) {
        uni.showToast({ title: '两次密码输入不一致', icon: 'none' })
        return
      }

      uni.showLoading({
        title: '重置中...'
      })

      request({
        url: config.USER_RESET_PASSWORD,
        method: 'POST',
        data: {
          account,
          phone,
          new_password: newPassword
        }
      }).then(res => {
        uni.hideLoading()
        uni.showToast({
          title: res.msg || '密码重置成功',
          icon: 'success'
        })

        setTimeout(() => {
          uni.redirectTo({
            url: '/pages/login/login'
          })
        }, 1200)
      }).catch(err => {
        uni.hideLoading()
        const msg = (err.data && err.data.msg) ? err.data.msg : '密码重置失败'
        uni.showToast({
          title: msg,
          icon: 'none'
        })
      })
    },

    goToLogin() {
      uni.navigateBack({
        fail: () => {
          uni.redirectTo({
            url: '/pages/login/login'
          })
        }
      })
    }
  }
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  padding: 100rpx 50rpx 0;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4edf9 100%);
  box-sizing: border-box;
}

.header {
  text-align: center;
  margin-bottom: 80rpx;
}

.title {
  display: block;
  font-size: 48rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 20rpx;
}

.subtitle {
  display: block;
  font-size: 28rpx;
  color: #666;
}

.form-card {
  background: rgba(255, 255, 255, 0.72);
  border-radius: 24rpx;
  padding: 40rpx 32rpx;
  box-shadow: 0 16rpx 40rpx rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(8rpx);
}

.input-group {
  margin-bottom: 32rpx;
}

.form-input {
  width: 100%;
  height: 100rpx;
  padding: 0 30rpx;
  background: #fff;
  border-radius: 15rpx;
  font-size: 30rpx;
  box-shadow: 0 4rpx 10rpx rgba(0,0,0,0.05);
  box-sizing: border-box;
}

.submit-btn {
  width: 100%;
  height: 100rpx;
  background: linear-gradient(135deg, #2563eb 0%, #06b6d4 100%);
  color: #fff;
  border: none;
  border-radius: 15rpx;
  font-size: 32rpx;
  margin-top: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(37, 99, 235, 0.22);
}

.submit-btn::after {
  border: none;
}

.footer-link {
  margin-top: 36rpx;
  text-align: center;
  color: #2563eb;
  font-size: 28rpx;
}
</style>

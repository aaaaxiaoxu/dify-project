<template>
  <view class="container">
    <view class="register-header">
      <text class="title">欢迎加入</text>
      <text class="subtitle">创建您的账户</text>
    </view>
    
    <view class="register-form">
      <view class="input-group">
        <input 
          class="form-input" 
          type="text" 
          placeholder="请输入用户名" 
          v-model="formData.username"
        />
      </view>
      
      <view class="input-group">
        <input 
          class="form-input" 
          type="text" 
          placeholder="请输入手机号" 
          v-model="formData.phone"
        />
      </view>
      
      <view class="input-group">
        <input 
          class="form-input" 
          type="password" 
          placeholder="请输入密码" 
          v-model="formData.password"
        />
      </view>
      
      <view class="input-group">
        <input 
          class="form-input" 
          type="password" 
          placeholder="请确认密码" 
          v-model="formData.confirmPassword"
        />
      </view>
      
      <button class="register-btn" @click="handleRegister">
        <text>注册</text>
      </button>
      
      <view class="form-footer">
        <text @click="goToLogin">已有账号？立即登录</text>
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
        username: '',
        phone: '',
        password: '',
        confirmPassword: ''
      }
    }
  },
  
  methods: {
    handleRegister() {
      if (!this.formData.username) {
        uni.showToast({
          title: '请输入用户名',
          icon: 'none'
        })
        return
      }
      
      if (!this.formData.phone) {
        uni.showToast({
          title: '请输入手机号',
          icon: 'none'
        })
        return
      }
      
      if (!this.formData.password) {
        uni.showToast({
          title: '请输入密码',
          icon: 'none'
        })
        return
      }
      
      if (this.formData.password !== this.formData.confirmPassword) {
        uni.showToast({
          title: '两次密码输入不一致',
          icon: 'none'
        })
        return
      }
      
      // 调用后端注册接口
      uni.showLoading({
        title: '注册中...'
      })
      
      request({
        url: config.USER_REGISTER,
        method: 'POST',
        data: {
          username: this.formData.username,
          phone: this.formData.phone,
          password: this.formData.password
        }
      }).then(res => {
        uni.hideLoading()
        if (res.msg === '注册成功') {
          uni.showToast({
            title: '注册成功',
            icon: 'success'
          })
          
          // 跳转到登录页
          setTimeout(() => {
            uni.redirectTo({
              url: '/pages/login/login'
            })
          }, 1500)
        } else {
          uni.showToast({
            title: res.msg || '注册失败',
            icon: 'none'
          })
        }
      }).catch(err => {
        uni.hideLoading()
        uni.showToast({
          title: '注册失败，请检查网络',
          icon: 'none'
        })
      })
    },
    
    goToLogin() {
      uni.navigateTo({
        url: '/pages/login/login'
      })
    }
  }
}
</script>

<style scoped>
.container {
  padding: 100rpx 50rpx 0;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4edf9 100%);
  min-height: 100vh;
  box-sizing: border-box;
}

.register-header {
  text-align: center;
  margin-bottom: 80rpx;
}

.title {
  display: block;
  font-size: 48rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 20rpx;
  text-shadow: 1rpx 1rpx 2rpx rgba(0,0,0,0.1);
}

.subtitle {
  font-size: 28rpx;
  color: #666;
}

.input-group {
  margin-bottom: 40rpx;
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
  text-align: left;
}

.register-btn {
  width: 100%;
  height: 100rpx;
  background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
  color: white;
  border: none;
  border-radius: 15rpx;
  font-size: 32rpx;
  margin-top: 50rpx;
  box-shadow: 0 4rpx 20rpx rgba(106,17,203,0.3);
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.register-btn:hover {
  transform: translateY(-5rpx);
  box-shadow: 0 8rpx 25rpx rgba(106,17,203,0.4);
}

.register-btn text {
  display: flex;
  align-items: center;
  justify-content: center;
}

.form-footer {
  text-align: center;
  margin-top: 50rpx;
  color: #007AFF;
  font-size: 28rpx;
}
</style>
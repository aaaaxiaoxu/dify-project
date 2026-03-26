<template>
  <view class="container">
    <view class="login-header">
      <text class="title">欢迎回来</text>
      <text class="subtitle">登录您的账户</text>
    </view>
    
    <view class="login-form">
      <view class="input-group">
        <input 
          class="form-input" 
          type="text" 
          placeholder="请输入手机号/用户名" 
          v-model="formData.username"
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
      
      <button class="login-btn" @click="handleLogin">
        <text>登录</text>
      </button>
      
      <view class="form-footer">
        <text @click="goToRegister">还没有账号？立即注册</text>
      </view>
    </view>
    
    <view class="social-login">
      <text class="social-title">其他登录方式</text>
      <view class="social-icons">
        <view class="social-icon">
          <text>📱</text>
        </view>
        <view class="social-icon">
          <text>💻</text>
        </view>
        <view class="social-icon">
          <text>📧</text>
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
      formData: {
        username: '',
        password: ''
      }
    }
  },
  
  onLoad() {
    console.log('Login page loaded')
  },
  
  methods: {
    handleLogin() {
      if (!this.formData.username) {
        uni.showToast({
          title: '请输入手机号/用户名',
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
      
      // 调用真实登录接口
      request({
        url: config.USER_LOGIN,
        method: 'POST',
        data: {
          username: this.formData.username,
          password: this.formData.password
        }
      }).then(res => {
        if (res.access_token) {
          // 登录成功
          uni.showToast({
            title: '登录成功',
            icon: 'success'
          })
          
          // 保存token到store和本地存储
          this.$store.commit('SET_TOKEN', res.access_token)
          
          // 保存管理员状态
          if (res.user && res.user.is_admin) {
            this.$store.commit('SET_IS_ADMIN', true)
          } else {
            this.$store.commit('SET_IS_ADMIN', false)
          }
          
          // 跳转到首页
          setTimeout(() => {
            uni.switchTab({
              url: '/pages/index/index'
            })
          }, 1500)
        } else {
          uni.showToast({
            title: res.msg || '登录失败',
            icon: 'none'
          })
        }
      }).catch(err => {
        console.error('Login error:', err)
        uni.showToast({
          title: '登录失败，请检查用户名和密码',
          icon: 'none'
        })
      })
    },
    
    goToRegister() {
      uni.navigateTo({
        url: '/pages/register/register'
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

.login-header {
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

.login-btn {
  width: 100%;
  height: 100rpx;
  background: linear-gradient(135deg, #007AFF 0%, #00d4ff 100%);
  color: white;
  border: none;
  border-radius: 15rpx;
  font-size: 32rpx;
  margin-top: 50rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,122,255,0.3);
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-btn:hover {
  transform: translateY(-5rpx);
  box-shadow: 0 8rpx 25rpx rgba(0,122,255,0.4);
}

.login-btn text {
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

.social-login {
  margin-top: 100rpx;
  text-align: center;
}

.social-title {
  font-size: 28rpx;
  color: #999;
  margin-bottom: 30rpx;
  display: block;
}

.social-icons {
  display: flex;
  justify-content: center;
  gap: 50rpx;
}

.social-icon {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40rpx;
  box-shadow: 0 4rpx 10rpx rgba(0,0,0,0.1);
  transition: all 0.3s ease;
}

.social-icon:hover {
  transform: translateY(-5rpx);
  box-shadow: 0 8rpx 15rpx rgba(0,0,0,0.15);
}
</style>
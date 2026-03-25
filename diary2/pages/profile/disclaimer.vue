<template>
  <view class="container">
    <view class="header">
      <text class="title">免责声明</text>
    </view>
    
    <view class="content">
      <view class="section">
        <text class="section-title">一、关于旅行日记应用</text>
        <text class="section-text">
          旅行日记应用（以下简称"本应用"）是由个人开发者创建和维护的开源项目。本应用旨在为用户提供记录旅行经历、分享旅行感受的平台。
        </text>
      </view>
      
      <view class="section">
        <text class="section-title">二、使用风险提示</text>
        <text class="section-text">
          1. 用户在使用本应用时，应自行承担相关风险。本应用不承担因使用本应用而导致的任何直接、间接、特殊或后果性损害。
        </text>
        <text class="section-text">
          2. 用户在记录旅行日记时，应遵守当地法律法规，不得发布违法、不实或侵犯他人权益的内容。
        </text>
        <text class="section-text">
          3. 用户应妥善保管自己的账户信息，避免泄露给他人。因账户信息泄露造成的损失由用户自行承担。
        </text>
      </view>
      
      <view class="section">
        <text class="section-title">三、内容责任</text>
        <text class="section-text">
          1. 用户在本应用中发表的任何内容仅代表其个人观点，与本应用开发者无关。
        </text>
        <text class="section-text">
          2. 本应用不对用户发表的内容的真实性、准确性或完整性作出任何保证。
        </text>
        <text class="section-text">
          3. 本应用有权但无义务对用户发表的内容进行审核，并有权删除违反规定的内容。
        </text>
      </view>
      
      <view class="section">
        <text class="section-title">四、服务变更与中断</text>
        <text class="section-text">
          1. 本应用开发者保留随时变更、中断或终止部分或全部服务的权利，且无需提前通知用户。
        </text>
        <text class="section-text">
          2. 因系统维护、升级或其他技术原因导致的服务中断，本应用不承担任何责任。
        </text>
      </view>
      
      <view class="section">
        <text class="section-title">五、知识产权</text>
        <text class="section-text">
          1. 本应用的所有知识产权归开发者所有。
        </text>
        <text class="section-text">
          2. 用户在本应用中发表的内容，其知识产权归用户本人所有，但用户同意授予本应用非独占的、免费的使用权。
        </text>
      </view>
      
      <view class="section">
        <text class="section-title">六、其他</text>
        <text class="section-text">
          1. 本免责声明的解释权归本应用开发者所有。
        </text>
        <text class="section-text">
          2. 本免责声明适用于中华人民共和国法律。
        </text>
        <text class="section-text">
          3. 如本免责声明的任何条款被视为无效或不可执行，不影响其他条款的有效性。
        </text>
      </view>
      
      <view class="section last-section">
        <text class="section-text">
          最后更新时间：2025年11月20日
        </text>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {}
  },
  methods: {
    goBack() {
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
  background: #fff;
  border-radius: 20rpx;
  padding: 40rpx;
  margin-bottom: 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.05);
  text-align: center;
}

.title {
  font-size: 40rpx;
  font-weight: bold;
  color: #333;
}

.content {
  background: #fff;
  border-radius: 20rpx;
  padding: 40rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.05);
}

.section {
  margin-bottom: 30rpx;
}

.section-title {
  display: block;
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 20rpx;
}

.section-text {
  display: block;
  font-size: 28rpx;
  color: #666;
  line-height: 1.6;
  margin-bottom: 15rpx;
}

.last-section {
  margin-bottom: 0;
  text-align: center;
  padding-top: 20rpx;
  border-top: 1rpx solid #eee;
}
</style>
<script>
	import store from './store'
	
	export default {
		store,
		onLaunch: function() {
			console.log('App Launch')
		},
		onShow: function() {
			console.log('App Show')
		},
		onHide: function() {
			console.log('App Hide')
		}
	}
</script>

<style>
	/*每个页面公共css */
	page {
	  background-color: #f5f5f5;
	  min-height: 100vh;
	}
	
	.container {
	  padding: 20rpx;
	}
	
	/* 添加全局样式 */
	button {
	  border-radius: 10rpx;
	}
	
	/* 统一卡片样式 */
	.card {
	  background: #fff;
	  border-radius: 20rpx;
	  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.05);
	}
</style>

// 封装网络请求
export default function request(options) {
  return new Promise((resolve, reject) => {
    // 打印请求信息用于调试
    console.log('发送请求:', options)
    
    uni.request({
      url: options.url,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'Content-Type': 'application/json',
        ...options.header
      },
      success: (res) => {
        console.log('请求成功:', res)
        // 2xx 都视为成功（例如创建接口常见 201）
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
        } else {
          // 详细错误信息
          console.error('请求失败:', res)
          reject(res)
        }
      },
      fail: (err) => {
        console.error('请求错误:', err)
        reject(err)
      }
    })
  })
}
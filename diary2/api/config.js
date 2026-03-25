// API配置文件
// const BASE_URL = 'http://localhost:5000/api'
const BASE_URL = 'http://47.110.157.154/api'

export default {
  BASE_URL,
  
  // 用户相关接口
  USER_REGISTER: BASE_URL + '/user/register',
  USER_LOGIN: BASE_URL + '/user/login',
  USER_PROFILE: BASE_URL + '/user/profile',
  
  // 日记相关接口
  DIARY_LIST: BASE_URL + '/diary/list',
  DIARY_CREATE: BASE_URL + '/diary/create',
  DIARY_UPDATE: BASE_URL + '/diary/update/<int:diary_id>',
  DIARY_DELETE: BASE_URL + '/diary/delete/<int:diary_id>',
  DIARY_DETAIL: BASE_URL + '/diary/detail/<int:diary_id>',
  
  // 地图相关接口
  MAP_TRAJECTORY: BASE_URL + '/map/trajectory',
  MAP_STATS: BASE_URL + '/map/stats',
  MAP_DETAIL: BASE_URL + '/map/detail',
  
  // AI分析相关接口
  AI_ANALYSIS: BASE_URL + '/ai/analysis',
  
  // 文件上传接口
  FILE_UPLOAD: BASE_URL + '/file/upload',
  
  // 分享相关接口
  SHARE_GENERATE: BASE_URL + '/share/generate',
  SHARE_DETAIL: BASE_URL + '/share/'
}
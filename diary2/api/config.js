// API配置文件
// const BASE_URL = 'http://localhost:5000/api'
const BASE_URL = 'http://localhost:8080/api'

export default {
  BASE_URL,
  
  // 用户相关接口
  USER_REGISTER: BASE_URL + '/user/register',
  USER_LOGIN: BASE_URL + '/user/login',
  USER_PROFILE: BASE_URL + '/user/profile',
  
  // 日记相关接口
  DIARY_LIST: BASE_URL + '/diary/list',
  DIARY_DRAFTS: BASE_URL + '/diary/drafts',
  DIARY_CREATE: BASE_URL + '/diary/create',
  DIARY_UPDATE: BASE_URL + '/diary/update/<int:diary_id>',
  DIARY_DELETE: BASE_URL + '/diary/delete/<int:diary_id>',
  DIARY_DETAIL: BASE_URL + '/diary/detail/<int:diary_id>',
  
  // 地图相关接口
  MAP_TRAJECTORY: BASE_URL + '/map/trajectory',
  MAP_STATS: BASE_URL + '/map/stats',
  MAP_DETAIL: BASE_URL + '/map/detail',
  MAP_REVERSE_GEOCODE: BASE_URL + '/map/reverse_geocode',
  MAP_GEOCODE: BASE_URL + '/map/geocode',
  
  // AI分析相关接口
  AI_ANALYSIS: BASE_URL + '/ai/analysis',
  AI_ANALYSIS_REFRESH: BASE_URL + '/ai/analysis/refresh',
  
  // 文件上传接口
  FILE_UPLOAD: BASE_URL + '/file/upload',
  
  // 分享相关接口
  SHARE_GENERATE: BASE_URL + '/share/generate',
  SHARE_DETAIL: BASE_URL + '/share/',
  SHARE_PAGE: BASE_URL + '/share/page/',
  SHARE_LIST: BASE_URL + '/share/list',
  SHARE_BY_DIARY: BASE_URL + '/share/diary/',
  SHARE_REVOKE: BASE_URL + '/share/revoke/',
  SHARE_DELETE: BASE_URL + '/share/delete/',
  SHARE_STATS: BASE_URL + '/share/stats/',
  
  // 统计分析接口
  STATS_EMOTION_DISTRIBUTION: BASE_URL + '/stats/emotion-distribution',
  STATS_EMOTION_TREND: BASE_URL + '/stats/emotion-trend',

  // 智能旅行总结
  REPORT_GENERATE: BASE_URL + '/report/generate',
  REPORT_EXPORT_PDF: BASE_URL + '/report/export-pdf',
  REPORT_DOWNLOAD: BASE_URL + '/report/download/',
  
  // 管理员相关接口
  ADMIN_UPGRADE: BASE_URL + '/admin/upgrade',
  ADMIN_CHECK: BASE_URL + '/admin/check',
  ADMIN_USERS: BASE_URL + '/admin/users',
  ADMIN_DIARIES: BASE_URL + '/admin/diaries',
  ADMIN_FREEZE_USER: BASE_URL + '/admin/users/',
  ADMIN_DELETE_DIARY: BASE_URL + '/admin/diaries/'
}

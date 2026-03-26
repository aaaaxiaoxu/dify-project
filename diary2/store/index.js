import { createStore } from 'vuex'

// 创建 store 实例
const store = createStore({
  state: {
    userInfo: null,
    token: uni.getStorageSync('token') || '', // 初始化时从本地存储获取token
    isAdmin: uni.getStorageSync('isAdmin') || false, // 管理员状态
    diaryList: [],
    currentDiary: null
  },
  mutations: {
    SET_USER_INFO(state, userInfo) {
      state.userInfo = userInfo
    },
    SET_TOKEN(state, token) {
      state.token = token
      // 同时保存到本地存储
      try {
        uni.setStorageSync('token', token)
      } catch (e) {
        console.error('Save token error:', e)
      }
    },
    SET_IS_ADMIN(state, isAdmin) {
      state.isAdmin = isAdmin
      try {
        uni.setStorageSync('isAdmin', isAdmin)
      } catch (e) {
        console.error('Save isAdmin error:', e)
      }
    },
    SET_DIARY_LIST(state, diaryList) {
      state.diaryList = diaryList
    },
    SET_CURRENT_DIARY(state, diary) {
      state.currentDiary = diary
    }
  },
  actions: {
    setUserInfo({ commit }, userInfo) {
      commit('SET_USER_INFO', userInfo)
    },
    setToken({ commit }, token) {
      commit('SET_TOKEN', token)
    },
    setIsAdmin({ commit }, isAdmin) {
      commit('SET_IS_ADMIN', isAdmin)
    },
    setDiaryList({ commit }, diaryList) {
      commit('SET_DIARY_LIST', diaryList)
    },
    setCurrentDiary({ commit }, diary) {
      commit('SET_CURRENT_DIARY', diary)
    }
  },
  getters: {
    isLogin: state => !!state.token,
    userInfo: state => state.userInfo,
    isAdmin: state => state.isAdmin,
    diaryList: state => state.diaryList,
    currentDiary: state => state.currentDiary
  }
})

export default store
import { defineStore } from 'pinia'
import * as api from '@/api'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null'),
  }),
  getters: {
    isLoggedIn: (s) => !!s.token,
    role: (s) => s.user?.role || '',
    username: (s) => s.user?.username || '',
  },
  actions: {
    async login(username, password) {
      const res = await api.login({ username, password })
      this.token = res.access_token
      localStorage.setItem('token', res.access_token)
      const me = res.user || await api.getMe()
      this.user = me
      localStorage.setItem('user', JSON.stringify(me))
      return me
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    },
    async refreshMe() {
      if (this.token) {
        try {
          const me = await api.getMe()
          this.user = me
          localStorage.setItem('user', JSON.stringify(me))
        } catch (e) {
          this.logout()
        }
      }
    },
    hasRole(...roles) {
      if (!this.user) return false
      if (this.user.role === 'admin') return true
      return roles.includes(this.user.role)
    },
  },
})

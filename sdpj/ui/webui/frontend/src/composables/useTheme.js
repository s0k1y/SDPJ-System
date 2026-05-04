/**
 * 主题管理 Composable
 * 支持亮色/深色模式切换
 */

import { ref, watch, onMounted } from 'vue'

const THEME_KEY = 'sdpj-theme'
const THEME_ATTR = 'data-theme'

export function useTheme() {
  // 从 localStorage 读取或使用系统偏好
  const getInitialTheme = () => {
    const stored = localStorage.getItem(THEME_KEY)
    if (stored) return stored

    // 检测系统偏好
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark'
    }

    return 'light'
  }

  const theme = ref(getInitialTheme())

  // 应用主题到 DOM
  const applyTheme = (newTheme) => {
    document.documentElement.setAttribute(THEME_ATTR, newTheme)
    localStorage.setItem(THEME_KEY, newTheme)
  }

  // 切换主题
  const toggleTheme = () => {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }

  // 设置主题
  const setTheme = (newTheme) => {
    if (newTheme === 'light' || newTheme === 'dark') {
      theme.value = newTheme
    }
  }

  // 监听主题变化
  watch(theme, (newTheme) => {
    applyTheme(newTheme)
  })

  // 监听系统主题变化
  onMounted(() => {
    applyTheme(theme.value)

    if (window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      const handleChange = (e) => {
        // 只在用户未手动设置主题时跟随系统
        if (!localStorage.getItem(THEME_KEY)) {
          theme.value = e.matches ? 'dark' : 'light'
        }
      }

      // 现代浏览器使用 addEventListener
      if (mediaQuery.addEventListener) {
        mediaQuery.addEventListener('change', handleChange)
      } else {
        // 兼容旧浏览器
        mediaQuery.addListener(handleChange)
      }
    }
  })

  return {
    theme,
    toggleTheme,
    setTheme,
    isDark: () => theme.value === 'dark',
    isLight: () => theme.value === 'light'
  }
}

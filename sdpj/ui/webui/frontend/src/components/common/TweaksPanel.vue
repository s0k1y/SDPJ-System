<template>
  <transition name="tweaks-fade">
    <div v-if="visible" class="tweaks-panel">
      <div class="tweaks-header">
        <h3 class="tweaks-title">Tweaks</h3>
        <button class="close-btn" @click="$emit('close')" aria-label="关闭">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <div class="tweaks-content">
        <!-- 主题切换 -->
        <div class="tweak-item">
          <label class="tweak-label">主题模式</label>
          <div class="theme-switcher">
            <button
              class="theme-option"
              :class="{ active: theme === 'light' }"
              @click="setTheme('light')"
            >
              <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="5"></circle>
                <line x1="12" y1="1" x2="12" y2="3"></line>
                <line x1="12" y1="21" x2="12" y2="23"></line>
              </svg>
              <span>亮色</span>
            </button>
            <button
              class="theme-option"
              :class="{ active: theme === 'dark' }"
              @click="setTheme('dark')"
            >
              <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
              </svg>
              <span>深色</span>
            </button>
          </div>
        </div>

        <!-- 字体大小 -->
        <div class="tweak-item">
          <label class="tweak-label">
            字体大小
            <span class="tweak-value">{{ fontSize }}px</span>
          </label>
          <input
            type="range"
            v-model.number="fontSize"
            min="14"
            max="18"
            step="1"
            class="slider"
          />
        </div>

        <!-- 动画速度 -->
        <div class="tweak-item">
          <label class="tweak-label">
            动画速度
            <span class="tweak-value">{{ animationSpeed }}x</span>
          </label>
          <input
            type="range"
            v-model.number="animationSpeed"
            min="0.5"
            max="2"
            step="0.1"
            class="slider"
          />
        </div>

        <!-- 紧凑模式 -->
        <div class="tweak-item">
          <label class="tweak-label">紧凑模式</label>
          <label class="switch">
            <input type="checkbox" v-model="compactMode" />
            <span class="switch-slider"></span>
          </label>
        </div>

        <!-- 显示动画 -->
        <div class="tweak-item">
          <label class="tweak-label">显示动画</label>
          <label class="switch">
            <input type="checkbox" v-model="showAnimations" />
            <span class="switch-slider"></span>
          </label>
        </div>
      </div>

      <div class="tweaks-footer">
        <button class="reset-btn" @click="resetSettings">
          重置设置
        </button>
      </div>
    </div>
  </transition>

  <!-- 浮动按钮 -->
  <button
    v-if="!visible"
    class="tweaks-trigger"
    @click="$emit('open')"
    aria-label="打开设置面板"
    title="Tweaks"
  >
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <circle cx="12" cy="12" r="3"></circle>
      <path d="M12 1v6m0 6v6m-9-9h6m6 0h6"></path>
    </svg>
  </button>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useThemeStore } from '../../store/theme'

defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

defineEmits(['close', 'open'])

const themeStore = useThemeStore()
const theme = ref(themeStore.theme)

// 设置项
const fontSize = ref(16)
const animationSpeed = ref(1)
const compactMode = ref(false)
const showAnimations = ref(true)

// 设置主题
const setTheme = (newTheme) => {
  theme.value = newTheme
  themeStore.setTheme(newTheme)
}

// 应用设置到 CSS 变量
watch([fontSize, animationSpeed, compactMode, showAnimations], () => {
  const root = document.documentElement
  root.style.setProperty('--font-size-base', `${fontSize.value}px`)
  root.style.setProperty('--animation-speed', animationSpeed.value)

  if (compactMode.value) {
    root.style.setProperty('--spacing-scale', '0.875')
  } else {
    root.style.setProperty('--spacing-scale', '1')
  }

  if (!showAnimations.value) {
    root.style.setProperty('--transition-fast', '0ms')
    root.style.setProperty('--transition-base', '0ms')
    root.style.setProperty('--transition-slow', '0ms')
  } else {
    root.style.setProperty('--transition-fast', '150ms')
    root.style.setProperty('--transition-base', '300ms')
    root.style.setProperty('--transition-slow', '500ms')
  }
})

// 重置设置
const resetSettings = () => {
  fontSize.value = 16
  animationSpeed.value = 1
  compactMode.value = false
  showAnimations.value = true
  setTheme('light')
}
</script>

<style scoped>
.tweaks-panel {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 320px;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-2xl);
  border: 1px solid var(--color-border);
  z-index: var(--z-modal);
  overflow: hidden;
  backdrop-filter: blur(12px);
}

.tweaks-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-4) var(--spacing-5);
  border-bottom: 1px solid var(--color-border);
}

.tweaks-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text);
  margin: 0;
}

.close-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-base);
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
  border: none;
  padding: 0;
}

.close-btn:hover {
  background: var(--color-surface-hover);
  color: var(--color-text);
}

.close-btn svg {
  width: 16px;
  height: 16px;
}

.tweaks-content {
  padding: var(--spacing-5);
  max-height: 500px;
  overflow-y: auto;
}

.tweak-item {
  margin-bottom: var(--spacing-5);
}

.tweak-item:last-child {
  margin-bottom: 0;
}

.tweak-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text);
  margin-bottom: var(--spacing-2);
}

.tweak-value {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  font-weight: var(--font-weight-normal);
}

/* 主题切换器 */
.theme-switcher {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-2);
}

.theme-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-3);
  border-radius: var(--radius-base);
  background: var(--color-bg);
  border: 2px solid var(--color-border);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
  font-size: var(--font-size-xs);
}

.theme-option:hover {
  border-color: var(--color-primary);
  color: var(--color-text);
}

.theme-option.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.theme-option .icon {
  width: 20px;
  height: 20px;
}

/* 滑块 */
.slider {
  width: 100%;
  height: 6px;
  border-radius: var(--radius-full);
  background: var(--color-gray-200);
  outline: none;
  -webkit-appearance: none;
  appearance: none;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--color-primary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.slider::-webkit-slider-thumb:hover {
  transform: scale(1.2);
}

.slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--color-primary);
  cursor: pointer;
  border: none;
  transition: all var(--transition-fast);
}

.slider::-moz-range-thumb:hover {
  transform: scale(1.2);
}

/* 开关 */
.switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.switch-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--color-gray-300);
  transition: var(--transition-fast);
  border-radius: var(--radius-full);
}

.switch-slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: var(--transition-fast);
  border-radius: 50%;
}

.switch input:checked + .switch-slider {
  background-color: var(--color-primary);
}

.switch input:checked + .switch-slider:before {
  transform: translateX(20px);
}

/* 底部 */
.tweaks-footer {
  padding: var(--spacing-4) var(--spacing-5);
  border-top: 1px solid var(--color-border);
}

.reset-btn {
  width: 100%;
  padding: var(--spacing-2) var(--spacing-4);
  border-radius: var(--radius-base);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  color: var(--color-text);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.reset-btn:hover {
  background: var(--color-surface-hover);
  border-color: var(--color-primary);
}

/* 浮动按钮 */
.tweaks-trigger {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 56px;
  height: 56px;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  color: white;
  box-shadow: var(--shadow-lg);
  cursor: pointer;
  transition: all var(--transition-base);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-fixed);
}

.tweaks-trigger:hover {
  transform: scale(1.1);
  box-shadow: var(--shadow-xl);
}

.tweaks-trigger:active {
  transform: scale(0.95);
}

.tweaks-trigger svg {
  width: 24px;
  height: 24px;
}

/* 动画 */
.tweaks-fade-enter-active,
.tweaks-fade-leave-active {
  transition: opacity var(--transition-base), transform var(--transition-base);
}

.tweaks-fade-enter-from {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

.tweaks-fade-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}
</style>

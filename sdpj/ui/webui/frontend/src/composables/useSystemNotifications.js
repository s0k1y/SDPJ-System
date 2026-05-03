import { ref, onMounted, onUnmounted } from 'vue'

export function useSystemNotifications() {
  const systemState = ref('')
  let ws = null

  function connect() {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    ws = new WebSocket(`${proto}://${location.host}/ws/status`)

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      if (msg.type === 'state') {
        systemState.value = msg.data
      } else if (msg.type === 'error') {
        import('element-plus').then(({ ElNotification }) => {
          ElNotification({ title: `系统异常: ${msg.err_type}`, message: msg.data, type: 'error', duration: 0 })
        })
      }
    }

    ws.onclose = () => {
      setTimeout(connect, 3000)
    }
  }

  onMounted(connect)
  onUnmounted(() => ws?.close())

  return { systemState }
}

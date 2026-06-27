<template>
  <div id="app-container">
    <nav class="sidebar">
      <div class="logo">🧠 WM Dashboard</div>
      <router-link to="/">📊 策略表现</router-link>
      <router-link to="/trades">📋 交易记录</router-link>
      <router-link to="/risk">⚠️ 风控事件</router-link>
      <router-link to="/model">🔬 模型状态</router-link>
      <div class="status" :class="wsConnected ? 'online' : 'offline'">
        {{ wsConnected ? '🟢 实时连接' : '🔴 离线' }}
      </div>
    </nav>
    <main class="content">
      <router-view :performance="performance" :equity="equity" :portfolio="portfolio"
                   :trades="trades" :riskEvents="riskEvents" :modelStatus="modelStatus"
                   :systemHealth="systemHealth" />
    </main>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

export default {
  setup() {
    const wsConnected = ref(false)
    const performance = ref({})
    const equity = ref([])
    const portfolio = ref({ positions: [] })
    const trades = ref([])
    const riskEvents = ref([])
    const modelStatus = ref({})
    const systemHealth = ref({})

    let ws = null, timer = null

    const fetchAll = async () => {
      try { const r = await axios.get('/api/v1/performance'); performance.value = r.data.data } catch(e) {}
      try { const r = await axios.get('/api/v1/equity_curve?days=60'); equity.value = r.data.data } catch(e) {}
      try { const r = await axios.get('/api/v1/portfolio'); portfolio.value = r.data.data } catch(e) {}
      try { const r = await axios.get('/api/v1/trades?limit=30'); trades.value = r.data.data } catch(e) {}
      try { const r = await axios.get('/api/v1/risk_events?limit=20'); riskEvents.value = r.data.data } catch(e) {}
      try { const r = await axios.get('/api/v1/model_status'); modelStatus.value = r.data.data } catch(e) {}
      try { const r = await axios.get('/api/v1/system_health'); systemHealth.value = r.data.data } catch(e) {}
    }

    onMounted(() => {
      fetchAll()
      timer = setInterval(fetchAll, 10000)
      try {
        ws = new WebSocket(`ws://${location.host}/ws`)
        ws.onopen = () => { wsConnected.value = true }
        ws.onclose = () => { wsConnected.value = false }
        ws.onmessage = (e) => {
          const msg = JSON.parse(e.data)
          if (msg.type === 'performance') performance.value = msg.data
        }
      } catch(e) {}
    })

    onUnmounted(() => { clearInterval(timer); if (ws) ws.close() })

    return { wsConnected, performance, equity, portfolio, trades, riskEvents, modelStatus, systemHealth }
  }
}
</script>

<style>
#app-container { display: flex; min-height: 100vh; }
.sidebar { width: 200px; background: #161b22; padding: 20px; display: flex; flex-direction: column; gap: 8px; border-right: 1px solid #30363d; }
.sidebar .logo { font-size: 16px; font-weight: bold; color: #58a6ff; margin-bottom: 20px; }
.sidebar a { color: #8b949e; text-decoration: none; padding: 8px 12px; border-radius: 6px; font-size: 14px; }
.sidebar a:hover, .sidebar a.router-link-active { background: #21262d; color: #f0f6fc; }
.sidebar .status { margin-top: auto; font-size: 12px; padding: 8px; }
.sidebar .online { color: #3fb950; } .sidebar .offline { color: #f85149; }
.content { flex: 1; padding: 24px; overflow-y: auto; }
</style>

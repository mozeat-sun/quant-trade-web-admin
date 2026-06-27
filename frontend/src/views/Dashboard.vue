<template>
  <div>
    <h2>📊 策略表现</h2>
    <div class="metrics-grid">
      <div class="metric-card"><span class="label">权益</span><span class="value">${{ fmt(performance.equity) }}</span></div>
      <div class="metric-card"><span class="label">Sharpe (60d)</span><span class="value" :class="performance.sharpe_60d > 1 ? 'green' : 'red'">{{ performance.sharpe_60d?.toFixed(2) }}</span></div>
      <div class="metric-card"><span class="label">Sortino</span><span class="value">{{ performance.sortino_60d?.toFixed(2) }}</span></div>
      <div class="metric-card"><span class="label">MaxDD</span><span class="value red">{{ (performance.maxdd * 100)?.toFixed(1) }}%</span></div>
      <div class="metric-card"><span class="label">年化收益</span><span class="value">{{ (performance.annual_return * 100)?.toFixed(1) }}%</span></div>
      <div class="metric-card"><span class="label">胜率</span><span class="value">{{ (performance.win_rate * 100)?.toFixed(0) }}%</span></div>
      <div class="metric-card"><span class="label">换手率</span><span class="value">{{ (performance.avg_turnover * 100)?.toFixed(1) }}%</span></div>
      <div class="metric-card"><span class="label">Calmar</span><span class="value">{{ performance.calmar?.toFixed(2) }}</span></div>
    </div>
    <div class="chart-container"><h3>权益曲线</h3><canvas ref="equityChart"></canvas></div>
    <div class="panel"><h3>当前持仓</h3>
      <table><thead><tr><th>股票</th><th>权重</th><th>浮动盈亏</th></tr></thead>
        <tbody><tr v-for="p in portfolio.positions" :key="p.symbol">
          <td>{{ p.symbol }}</td><td>{{ (p.weight * 100).toFixed(1) }}%</td>
          <td :class="p.pnl_pct > 0 ? 'green' : 'red'">{{ (p.pnl_pct * 100).toFixed(1) }}%</td>
        </tr></tbody>
      </table>
    </div>
  </div>
</template>

<script>
import { ref, watch, onMounted } from 'vue'
import { Chart, registerables } from 'chart.js'
Chart.register(...registerables)

export default {
  props: ['performance', 'equity', 'portfolio'],
  setup(props) {
    const equityChart = ref(null)
    let chart = null

    const fmt = (v) => v?.toLocaleString?.() ?? '--'

    watch(() => props.equity, (data) => {
      if (!data?.length || !equityChart.value) return
      if (chart) chart.destroy()
      chart = new Chart(equityChart.value, {
        type: 'line',
        data: { labels: data.map(d => d.date), datasets: [{ label: 'Equity', data: data.map(d => d.equity), borderColor: '#58a6ff', borderWidth: 1.5, pointRadius: 0, fill: false, tension: 0.3 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
          scales: { x: { ticks: { color: '#8b949e', maxTicksLimit: 10 } }, y: { ticks: { color: '#8b949e', callback: v => '$' + v.toLocaleString() } } } }
      })
    }, { immediate: true })

    return { equityChart, fmt }
  }
}
</script>

<style scoped>
.metrics-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }
.metric-card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; display: flex; flex-direction: column; gap: 4px; }
.metric-card .label { font-size: 12px; color: #8b949e; }
.metric-card .value { font-size: 22px; font-weight: bold; color: #f0f6fc; }
.green { color: #3fb950 !important; } .red { color: #f85149 !important; }
.chart-container { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; height: 300px; margin-bottom: 24px; }
.chart-container h3 { margin-top: 0; }
.panel { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; }
.panel h3 { margin-top: 0; }
table { width: 100%; border-collapse: collapse; }
th, td { text-align: left; padding: 8px 12px; border-bottom: 1px solid #21262d; font-size: 14px; }
th { color: #8b949e; font-weight: 600; }
</style>

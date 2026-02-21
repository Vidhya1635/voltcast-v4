<template>
  <div class="live-dashboard fade-in">
    <header>
      <div class="header-main">
        <h1 class="text-gradient">Live Grid Intelligence</h1>
        <div class="live-badge">
          <span class="pulse"></span> LIVE MODE
        </div>
      </div>
      <p class="text-muted">Real-time market analytics and grid intelligence</p>
    </header>

    <!-- Alerts Section -->
    <div v-if="summary && summary.alerts && summary.alerts.length" class="alerts-container">
      <div v-for="(alert, idx) in summary.alerts" :key="idx" 
           :class="['alert-banner', 'centered-alert', alert.type.toLowerCase()]">
        <AlertTriangle v-if="alert.type === 'CRITICAL'" :size="20" />
        <Info v-else :size="20" />
        <span class="alert-text">{{ alert.message }}</span>
      </div>
    </div>

    <!-- Stats Grid -->
    <div class="stats-grid" v-if="summary">
      <div class="stat-card card glass">
        <div class="stat-label">System Price (Est.)</div>
        <div class="stat-value text-gradient">${{ summary.avg_price.toFixed(2) }}</div>
        <div class="stat-sub">USD per MWh (ISO-NE LMP)</div>
      </div>
      <div class="stat-card card glass">
        <div class="stat-label">Renewable Supply</div>
        <div class="stat-value success">{{ formatNum(summary.renewable_mw) }} MW</div>
        <div class="stat-sub">Solar & Wind contribution</div>
      </div>
      <div class="stat-card card glass">
        <div class="stat-label">Peak Demand</div>
        <div class="stat-value accent">{{ formatNum(summary.peak_load) }} MW</div>
        <div class="stat-sub">Predicted for {{ formatDate(summary.peak_time) }}</div>
      </div>
    </div>

    <!-- Main Chart -->
    <div class="chart-container card" v-if="forecastData">
      <div class="chart-header">
        <h3>7-Day Horizon Intelligence</h3>
        <div class="chart-legend">
          <span class="legend-item"><i class="load"></i> Load (MW)</span>
          <span class="legend-item"><i class="net"></i> Net Load (MW)</span>
          <span class="legend-item"><i class="price"></i> Price ($)</span>
        </div>
      </div>
      <div id="liveChart" class="echart"></div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <p>Synchronizing with ISO-NE & Weather Satellites...</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue';
import { AlertTriangle, Info, Zap } from 'lucide-vue-next';
import api from '@/api';
import * as echarts from 'echarts';
import { format, parseISO } from 'date-fns';

const loading = ref(true);
const forecastData = ref(null);
const summary = ref(null);
let chart = null;

const formatNum = (v) => Math.round(v).toLocaleString();
const formatDate = (ds) => ds ? format(parseISO(ds), 'MMM do, HH:mm') : '';

const fetchLiveMode = async () => {
  loading.value = true;
  try {
    const res = await api.get('/api/live-forecast');
    forecastData.value = res.data;
    summary.value = res.data.summary;
    nextTick(initChart);
  } catch (err) {
    console.error("Live Mode synchronization failed", err);
  } finally {
    loading.value = false;
  }
};

const initChart = () => {
  const chartDom = document.getElementById('liveChart');
  if (!chartDom) return;
  chart = echarts.init(chartDom, 'dark');

  const data = forecastData.value.forecast;
  const timestamps = data.map(f => f.timestamp);
  const load = data.map(f => f.predicted_load);
  const netLoad = data.map(f => f.net_load);
  const price = data.map(f => f.price);

  const option = {
    backgroundColor: 'transparent',
    tooltip: { 
      trigger: 'axis',
      backgroundColor: '#1e293b',
      borderColor: '#334155',
      textStyle: { color: '#f8fafc' },
      formatter: (params) => {
        let tip = `<div style="padding:4px; font-family: Inter, sans-serif;">
          <b style="color: #94a3b8; font-size: 11px; text-transform: uppercase;">${format(parseISO(params[0].axisValue), 'MMM d, HH:mm')}</b><br/>
          <div style="margin-top: 5px;">`;
        params.forEach(p => {
          const valNum = parseFloat(p.value);
          if (p.value !== null && !isNaN(valNum)) {
            const isPrice = p.seriesName.includes('Price');
            const formattedVal = isPrice ? `$${valNum.toFixed(2)}` : `${Math.round(valNum).toLocaleString()} MW`;
            tip += `<div style="display: flex; justify-content: space-between; gap: 20px; margin-bottom: 2px;">
              <span><span style="color:${p.color}">●</span> ${p.seriesName}</span>
              <b style="color: #f8fafc">${formattedVal}</b>
            </div>`;
          }
        });
        return tip + '</div></div>';
      }
    },
    grid: { left: '3%', right: '5%', bottom: '10%', top: '80px', containLabel: true },
    xAxis: {
      type: 'category',
      data: timestamps,
      axisLabel: {
        formatter: (val) => format(parseISO(val), 'MMM d, HH:mm'),
        interval: 23,
        color: '#94a3b8'
      }
    },
    yAxis: [
      { 
        type: 'value', 
        name: 'Load (MW)', 
        nameTextStyle: { padding: [0, 0, 10, 0], fontWeight: 'bold' },
        splitLine: { lineStyle: { color: '#1e293b' } } 
      },
      { 
        type: 'value', 
        name: 'Price ($)', 
        nameTextStyle: { padding: [0, 0, 10, 0], fontWeight: 'bold' },
        splitLine: { show: false } 
      }
    ],
    series: [
      {
        name: 'Load (MW)',
        type: 'line',
        data: load,
        smooth: true,
        lineStyle: { color: '#6366f1', width: 3 },
        symbol: 'none'
      },
      {
        name: 'Net Load (MW)',
        type: 'line',
        data: netLoad,
        smooth: true,
        lineStyle: { color: '#10b981', width: 2, type: 'dashed' },
        symbol: 'none',
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(16, 185, 129, 0.1)' },
            { offset: 1, color: 'rgba(16, 185, 129, 0)' }
          ])
        }
      },
      {
        name: 'Price ($)',
        type: 'bar',
        yAxisIndex: 1,
        data: price,
        itemStyle: { color: 'rgba(251, 191, 36, 0.3)' }
      }
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: 0, start: 0, end: 100 },
      { type: 'inside', yAxisIndex: 0, start: 0, end: 100 },
      { type: 'slider', xAxisIndex: 0, bottom: 0, height: 20 },
      { type: 'slider', yAxisIndex: 0, right: 10, width: 20 }
    ]
  };

  chart.setOption(option);
  window.addEventListener('resize', () => chart.resize());
};

onMounted(fetchLiveMode);
</script>

<style scoped>
.live-dashboard { padding-bottom: 2rem; }

.header-main { display: flex; align-items: center; gap: 1.5rem; margin-bottom: 0.5rem; }

.live-badge {
  background: rgba(244, 63, 94, 0.1);
  color: #f43f5e;
  padding: 0.4rem 0.8rem;
  border-radius: 2rem;
  font-weight: 800;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border: 1px solid rgba(244, 63, 94, 0.2);
}

.pulse {
  width: 8px;
  height: 8px;
  background: #f43f5e;
  border-radius: 50%;
  animation: pulse-ring 1.5s infinite;
}

@keyframes pulse-ring {
  0% { transform: scale(0.8); box-shadow: 0 0 0 0 rgba(244, 63, 94, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(244, 63, 94, 0); }
  100% { transform: scale(0.8); box-shadow: 0 0 0 0 rgba(244, 63, 94, 0); }
}

.alerts-container { margin-bottom: 1.5rem; }

.alert-banner {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.5rem;
  border-radius: 0.75rem;
  margin-bottom: 0.75rem;
  font-weight: 500;
}

.alert-banner.critical { background: rgba(244, 63, 94, 0.15); border: 1px solid #f43f5e; color: #ff8095; }
.alert-banner.warning { background: rgba(251, 191, 36, 0.1); border: 1px solid #fbbf24; color: #fbbf24; }

.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; margin-bottom: 2rem; }
.stat-card { padding: 1.5rem; text-align: left; }
.stat-label { font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.5rem; }
.stat-value { font-size: 2rem; font-weight: 800; margin-bottom: 0.25rem; }
.stat-value.success { color: var(--success); }
.stat-value.accent { color: var(--accent); }
.stat-sub { font-size: 0.75rem; color: var(--text-muted); }

.chart-container { height: 500px; display: flex; flex-direction: column; }
.chart-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
.chart-legend { display: flex; gap: 1rem; font-size: 0.8rem; }
.legend-item { display: flex; align-items: center; gap: 0.5rem; }
.legend-item i { width: 12px; height: 3px; border-radius: 2px; }
.legend-item i.load { background: #6366f1; }
.legend-item i.net { background: #10b981; border: 1px dashed #10b981; }
.legend-item i.price { background: #fbbf24; opacity: 0.5; height: 8px; }

.echart { flex: 1; width: 100%; }

.loading-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(8px);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  z-index: 100; gap: 1.5rem;
}

.spinner {
  width: 40px; height: 40px; border: 4px solid rgba(255,255,255,0.1);
  border-top-color: var(--primary); border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }
.centered-alert {
  justify-content: center;
  text-align: center;
  width: 100%;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
}

.alert-text {
  color: var(--warning);
  font-weight: 600;
}

.alert-banner.critical .alert-text {
  color: var(--accent);
}
</style>

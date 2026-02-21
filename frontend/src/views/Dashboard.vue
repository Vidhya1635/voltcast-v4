<template>
  <div class="dashboard fade-in">
    <header>
      <div>
        <h1 class="text-gradient">Demand Forecast Dashboard</h1>
        <p class="text-muted">Generate 168-hour hybrid predictions</p>
      </div>
      
      <div class="controls glass card">
        <div class="input-row">
            <div class="control-group">
                <label>Forecast Start Date</label>
                <div class="input-group">
                    <input type="date" v-model="selectedDate" />
                </div>
            </div>
            <div class="control-group what-if-group">
                <label>What-If: Temperature Offset ({{ tempOffset > 0 ? '+' : '' }}{{ tempOffset }}°C)</label>
                <input type="range" v-model="tempOffset" min="-10" max="10" step="1" class="slider" />
                <div class="slider-labels">
                    <span>Chill (-10°)</span>
                    <span>Heat (+10°)</span>
                </div>
            </div>
            <button @click="generateForecast" :disabled="loading" class="btn-primary">
                <template v-if="loading">
                    <span class="spinner"></span>
                </template>
                <template v-else>
                    <Zap :size="18" /> Predict
                </template>
            </button>
        </div>
      </div>
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
    
    <div class="context-bar card" v-if="forecastData && summary">
      <div class="context-item">
        <component :is="getSeasonIcon(summary.season)" :size="18" />
        <span>Season: <strong>{{ summary.season }}</strong></span>
      </div>
      <div class="context-divider"></div>
      <div class="context-item" :class="{ 'is-holiday': summary.is_holiday }">
        <Gift :size="18" v-if="summary.is_holiday" />
        <Calendar :size="18" v-else />
        <span>Type: <strong>{{ summary.is_holiday ? 'US Holiday' : 'Normal Day' }}</strong></span>
      </div>
    </div>

    <div v-if="error" class="error-banner">
      {{ error }}
    </div>

    <!-- Stats Row -->
    <div class="stats-grid" v-if="forecastData && summary">
      <div class="stat-card card">
        <div class="stat-label">Peak Demand</div>
        <div class="stat-value">{{ formatLoad(summary.peak_load) }} MW</div>
        <div class="stat-sub">Expected at {{ formatDate(summary.peak_time) }}</div>
      </div>
      <div class="stat-card card">
        <div class="stat-label">Average Load</div>
        <div class="stat-value">{{ formatLoad(summary.avg_load) }} MW</div>
        <div class="stat-sub">Across 168-hour horizon</div>
      </div>
      <div class="stat-card card">
        <div class="stat-label">XGBoost Base</div>
        <div class="stat-value">{{ formatLoad(summary.xgb_avg) }} MW</div>
        <div class="stat-sub">Residual correction: {{ (summary.avg_load - summary.xgb_avg).toFixed(1) }} MW</div>
      </div>
      <div class="stat-card card weather-card" v-if="forecastData.forecast && forecastData.forecast[0]">
        <div class="stat-label">Initial Condition</div>
        <div class="weather-info">
          <component :is="getWeatherIcon(forecastData.forecast[0].weather_code)" :size="32" class="weather-icon" />
          <div class="weather-text">
            <div class="stat-value">{{ getWeatherLabel(forecastData.forecast[0].weather_code) }}</div>
            <div class="stat-sub">Based on Boston station</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Chart -->
    <div class="chart-container card" v-if="forecastData">
      <div class="chart-header">
        <h3>168-Hour Forecast Horizon</h3>
        <div class="chart-legend">
          <span class="legend-item"><i class="actual"></i> Actual (Past)</span>
          <span class="legend-item"><i class="gt"></i> Actual (Ground Truth)</span>
          <span class="legend-item"><i class="predict"></i> Hybrid V4 Prediction</span>
          <span class="legend-item"><i class="xgb"></i> XGBoost Base</span>
        </div>
      </div>
      <div id="forecastChart" class="echart"></div>
    </div>

    <!-- Placeholder -->
    <div v-else-if="!loading" class="placeholder card">
      <div class="placeholder-icon">📈</div>
      <h2>Ready to Predict</h2>
      <p>Select a date to generate the next 7 days of electricity load forecast.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue';
import { 
  Zap, Sun, Cloud, CloudSun, CloudFog, CloudDrizzle, 
  CloudRain, CloudSnow, CloudLightning,
  Activity, Calendar, Gift, Thermometer, Wind,
  AlertTriangle, Info, Sprout, Leaf
} from 'lucide-vue-next';
import api from '@/api';
import * as echarts from 'echarts';
import { format, parseISO } from 'date-fns';

const selectedDate = ref('2024-03-01');
const tempOffset = ref(0);
const loading = ref(false);
const error = ref(null);
const forecastData = ref(null);
const summary = ref(null);

let chart = null;

const formatLoad = (val) => Math.round(val).toLocaleString();
const formatDate = (ds) => ds ? format(parseISO(ds), 'MMM do, HH:mm') : '';

const getWeatherIcon = (code) => {
  if (code === 0) return Sun;
  if (code <= 3) return CloudSun;
  if (code <= 48) return CloudFog;
  if (code <= 55) return CloudDrizzle;
  if (code <= 65) return CloudRain;
  if (code <= 77) return CloudSnow;
  if (code <= 82) return CloudRain;
  return CloudLightning;
};

const getWeatherLabel = (code) => {
  if (code === 0) return 'Clear';
  if (code <= 3) return 'Partly Cloudy';
  if (code <= 48) return 'Foggy';
  if (code <= 55) return 'Drizzle';
  if (code <= 65) return 'Rainy';
  if (code <= 77) return 'Snowy';
  if (code <= 82) return 'Showers';
  return 'Thunderstorm';
};

const getSeasonIcon = (season) => {
  if (season === 'Summer') return Sun;
  if (season === 'Winter') return Thermometer;
  if (season === 'Spring') return Sprout;
  if (season === 'Autumn') return Leaf;
  return Activity;
};

const generateForecast = async () => {
  loading.value = true;
  error.value = null;
  
  try {
    const res = await api.post('/api/forecast', {
      start_date: `${selectedDate.value} 00:00`,
      temp_offset: tempOffset.value
    }, { timeout: 60000 });
    
    forecastData.value = res.data;
    summary.value = res.data.summary;

    nextTick(() => {
        initChart();
    });
  } catch (err) {
    error.value = err.response?.data?.error || "Failed to connect to backend.";
  } finally {
    loading.value = false;
  }
};

const initChart = () => {
  if (chart) chart.dispose();
  const chartDom = document.getElementById('forecastChart');
  chart = echarts.init(chartDom, 'dark');

  const history = forecastData.value.previous_week || [];
  const forecast = forecastData.value.forecast || [];
  const gt = forecastData.value.ground_truth || [];
  
  const allTimestamps = [
    ...history.map(h => h.Timestamp),
    ...forecast.map(f => f.timestamp)
  ];
  
  const histLen = history.length;
  const lastLoad = histLen > 0 ? history[histLen - 1].load : null;

  const actualSeries = [
    ...history.map(h => h.load),
    ...Array(forecast.length).fill(null)
  ];
  
  const predictSeries = [
    ...Array(Math.max(0, histLen - 1)).fill(null),
    lastLoad,
    ...forecast.map(f => f.predicted_load)
  ];
  
  if (predictSeries.length < allTimestamps.length) {
      predictSeries.unshift(...Array(allTimestamps.length - predictSeries.length).fill(null));
  }

  const xgbSeries = [
    ...Array(Math.max(0, histLen - 1)).fill(null),
    lastLoad,
    ...forecast.map(f => f.xgb_load)
  ];
  if (xgbSeries.length < allTimestamps.length) {
      xgbSeries.unshift(...Array(allTimestamps.length - xgbSeries.length).fill(null));
  }

  const gtSeries = [
    ...Array(Math.max(0, histLen - 1)).fill(null),
    lastLoad,
    ...(gt.length > 0 ? gt.map(g => g.load) : Array(forecast.length).fill(null))
  ];
  if (gtSeries.length < allTimestamps.length) {
      gtSeries.unshift(...Array(allTimestamps.length - gtSeries.length).fill(null));
  }

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
    grid: { left: '3%', right: '5%', bottom: '12%', top: '80px', containLabel: true },
    xAxis: {
      type: 'category',
      data: allTimestamps,
      axisLabel: {
        formatter: (val) => format(parseISO(val), 'MMM d'),
        interval: 23,
        color: '#94a3b8'
      },
      axisLine: { lineStyle: { color: '#334155' } }
    },
    yAxis: [
      {
        type: 'value',
        name: 'Load (MW)',
        nameTextStyle: { padding: [0, 0, 10, 0], fontWeight: 'bold' },
        splitLine: { lineStyle: { color: '#1e293b' } },
        axisLabel: { color: '#94a3b8' }
      },
      {
        type: 'value',
        name: 'Price ($)',
        nameTextStyle: { padding: [0, 0, 10, 0], fontWeight: 'bold' },
        splitLine: { show: false },
        axisLabel: { color: '#fbbf24' }
      }
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: 0, start: 40, end: 100 },
      { type: 'inside', yAxisIndex: 0 },
      { type: 'slider', xAxisIndex: 0, bottom: 10, height: 20 },
      { type: 'slider', yAxisIndex: 0, right: 10, width: 20 }
    ],
    series: [
      {
        name: 'Actual (Past)',
        type: 'line',
        data: actualSeries,
        symbol: 'none',
        lineStyle: { color: '#94a3b8', width: 2, type: 'dashed' },
        smooth: true
      },
      {
        name: 'Hybrid Prediction',
        type: 'line',
        data: predictSeries,
        symbol: 'none',
        lineStyle: { color: '#6366f1', width: 4 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(99, 102, 241, 0.4)' },
            { offset: 1, color: 'rgba(99, 102, 241, 0)' }
          ])
        },
        smooth: true
      },
      {
        name: 'Actual (Ground Truth)',
        type: 'line',
        data: gtSeries,
        symbol: 'none',
        lineStyle: { color: '#10b981', width: 2 },
        smooth: true,
        z: 10 // ensure it sits somewhere visible
      },
      {
        name: 'XGBoost Baseline',
        type: 'line',
        data: xgbSeries,
        symbol: 'none',
        lineStyle: { color: '#f43f5e', width: 1.5, type: 'dotted' },
        smooth: true
      },
      {
        name: 'Net Load (Renewable Corrected)',
        type: 'line',
        data: [
            ...Array(Math.max(0, histLen - 1)).fill(null),
            lastLoad,
            ...forecast.map(f => f.net_load)
        ],
        symbol: 'none',
        lineStyle: { color: '#10b981', width: 2, type: 'dashed' },
        smooth: true
      },
      {
        name: 'Market Price ($)',
        type: 'bar',
        yAxisIndex: 1,
        data: [
            ...Array(Math.max(0, histLen - 1)).fill(null),
            0,
            ...forecast.map(f => f.price)
        ],
        itemStyle: { color: 'rgba(251, 191, 36, 0.2)' }
      }
    ]
  };

  chart.setOption(option);
  window.addEventListener('resize', () => chart.resize());
};
</script>

<style scoped>
header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  gap: 2rem;
}

.controls {
  padding: 1.25rem 1.5rem;
  width: 100%;
}

.input-row {
    display: flex;
    align-items: flex-end;
    gap: 2rem;
    flex-wrap: wrap;
}

@media (max-width: 768px) {
  header {
    flex-direction: column;
    gap: 1.5rem;
  }
  
  .input-row {
    gap: 1rem;
  }
}

.control-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    min-width: 200px;
}

.what-if-group {
    flex: 1;
    min-width: 250px;
}

.slider {
    width: 100%;
    accent-color: var(--primary);
}

.slider-labels {
    display: flex;
    justify-content: space-between;
    font-size: 0.7rem;
    color: var(--text-muted);
}

.controls label {
  display: block;
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

.input-group {
  display: flex;
  gap: 1rem;
}

input[type="date"] {
  background: rgba(0,0,0,0.2);
  border: 1px solid var(--border);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  outline: none;
  flex: 1;
}

input[type="date"]::-webkit-calendar-picker-indicator {
    filter: invert(1);
}

.btn-primary {
  background: var(--primary);
  border: none;
  color: white;
  padding: 0.6rem 1.2rem;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: var(--secondary);
  box-shadow: 0 0 15px var(--primary-glow);
}

.btn-primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
  margin-bottom: 2rem;
}

@media (max-width: 900px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}

.stat-label {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 800;
  margin-bottom: 0.25rem;
}

.stat-sub {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.chart-container {
  height: 500px;
  display: flex;
  flex-direction: column;
}

.weather-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 0.5rem;
}

.weather-icon {
  color: var(--primary);
  filter: drop-shadow(0 0 8px var(--primary-glow));
}

.weather-text {
  display: flex;
  flex-direction: column;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.chart-legend {
  display: flex;
  gap: 1rem;
  font-size: 0.8rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.legend-item i {
  width: 12px;
  height: 2px;
}

.legend-item i.actual { background: #94a3b8; border: 1px dashed #94a3b8; height: 0; }
.legend-item i.gt { background: #10b981; height: 3px; }
.legend-item i.predict { background: #6366f1; height: 3px; }
.legend-item i.xgb { background: #f43f5e; border: 1px dotted #f43f5e; height: 0; }

.echart {
  flex: 1;
  width: 100%;
}

.context-bar {
  display: flex;
  padding: 0.75rem 1.5rem !important;
  margin-bottom: 1.5rem;
  gap: 2rem;
  align-items: center;
  background: rgba(255,255,255,0.03) !important;
  border: 1px solid var(--border);
  border-radius: 12px;
}

.context-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.9rem;
  color: var(--text-muted);
}

.context-item strong {
  color: var(--text);
  margin-left: 0.25rem;
}

.context-item.is-holiday {
  color: #fbbf24;
}

.context-item.is-holiday strong {
  color: #fbbf24;
}

.context-divider {
  width: 1px;
  height: 20px;
  background: var(--border);
}

.placeholder {
  height: 400px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: var(--text-muted);
}

.placeholder-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.error-banner {
  background: rgba(244, 63, 94, 0.1);
  border: 1px solid var(--accent);
  color: #fb7185;
  padding: 1rem;
  border-radius: 0.75rem;
  margin-bottom: 2rem;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

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

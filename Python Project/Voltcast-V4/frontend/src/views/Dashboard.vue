<template>
  <div class="dashboard fade-in" :style="forecastData && forecastData.forecast[0] ? getWeatherBgStyle(forecastData.forecast[0].weather_code) : {}">
    <header>
      <div>
        <h1 class="text-gradient">Demand Forecast Dashboard</h1>
        <p class="text-muted">Generate 168-hour hybrid predictions</p>
      </div>
      
      <div class="controls">
        <div class="input-row">
            <div style="display: flex; flex-direction: column; gap: 1rem; width: 100%; max-width: 250px;">
                <div class="control-group card glass control-card" style="margin: 0; padding: 1rem 1.5rem; width: 100%;">
                    <label style="font-weight: 800; display: block; margin-bottom: 0.5rem;">Forecast Start Date</label>
                    <div class="input-group">
                        <input type="date" v-model="selectedDate" />
                    </div>
                </div>
                <button @click="generateForecast" :disabled="loading" class="btn-primary" style="padding: 0.8rem; border-radius: 0.75rem; justify-content: center; font-size: 1.1rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); width: 100%;">
                    <template v-if="loading">
                        <span class="spinner"></span>
                    </template>
                    <template v-else>
                        <Zap :size="20" /> Predict
                    </template>
                </button>
            </div>
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
      <div class="context-divider" v-if="forecastData.forecast && forecastData.forecast[0]"></div>
      <div class="context-item" v-if="forecastData.forecast && forecastData.forecast[0]">
        <component :is="getWeatherIcon(forecastData.forecast[0].weather_code)" :size="18" />
        <span>Initial Condition: <strong>{{ getWeatherLabel(forecastData.forecast[0].weather_code) }}</strong></span>
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
        <div class="stat-sub">EXPECTED AT: {{ formatDate(summary.peak_time) }}</div>
      </div>
      <div class="stat-card card">
        <div class="stat-label">Average Load</div>
        <div class="stat-value">{{ formatLoad(summary.avg_load) }} MW</div>
        <div class="stat-sub">ACROSS 168-HOUR HORIZON</div>
      </div>
      <div class="stat-card card">
        <div class="stat-label">Hybrid Model Base</div>
        <div class="stat-value">{{ formatLoad(summary.xgb_avg) }} MW</div>
        <div class="stat-sub">RESIDUAL CORRECTION: {{ (summary.avg_load - summary.xgb_avg).toFixed(1) }} MW</div>
      </div>
    </div>

    <!-- Main Chart -->
    <div class="chart-container card" v-if="forecastData">
      <div class="chart-header">
        <h3>168-Hour Forecast Horizon</h3>
        <div class="chart-legend">
          <span class="legend-item"><i class="actual"></i> Actual (Past)</span>
          <span class="legend-item"><i class="gt"></i> Actual (Ground Truth)</span>
          <span class="legend-item"><i class="predict"></i> Hybrid Model Prediction</span>
          <span class="legend-item"><i class="xgb"></i> Hybrid Model Base</span>
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

    <!-- What-If Slider Block Placed Below Chart -->
    <div class="what-if-wrapper" style="display: flex; justify-content: center; margin-top: 2rem; margin-bottom: 2rem; width: 100%;">
        <div class="control-group what-if-group card glass control-card" style="display: flex; flex-direction: row; align-items: center; justify-content: space-between; gap: 1.5rem; width: 100%; max-width: 800px; border-radius: 9999px; padding: 0.75rem 2rem; margin: 0 auto; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <label style="font-size: 1rem; color: #0f172a; font-weight: 800; white-space: nowrap; margin: 0;">What-If Offset: {{ tempOffset > 0 ? '+' : '' }}{{ tempOffset }}°C</label>
            <div style="display: flex; align-items: center; gap: 1rem; flex: 1;">
                <span style="font-weight: 800; color: #0f172a; font-size: 0.85rem; white-space: nowrap;">Chill (-10°)</span>
                <div class="slider-container" style="flex: 1; position: relative;">
                   <input type="range" v-model="tempOffset" min="-10" max="10" step="1" class="slider" style="margin: 0; display: block;" />
                   <div class="slider-tooltip" :style="{ left: `calc(${((Number(tempOffset) + 10) / 20) * 100}% + ${8 - (((Number(tempOffset) + 10) / 20) * 16)}px)` }">
                     {{ tempOffset > 0 ? '+' : '' }}{{ tempOffset }}°C
                   </div>
                </div>
                <span style="font-weight: 800; color: #0f172a; font-size: 0.85rem; white-space: nowrap;">Heat (+10°)</span>
            </div>
        </div>
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

const getWeatherImage = (code) => {
  if (code === 0) return '/images/weather_sunny.png';
  if (code <= 3) return '/images/weather_cloudy.png';
  if (code <= 48) return '/images/weather_foggy.png';
  if (code <= 65) return '/images/weather_rainy.png';
  if (code <= 77) return '/images/weather_snowy.png';
  if (code <= 82) return '/images/weather_rainy.png';
  return '/images/weather_stormy.png';
};

const getWeatherBgStyle = (code) => {
  return {
    backgroundImage: `linear-gradient(to bottom, rgba(239, 246, 255, 0.85), rgba(239, 246, 255, 0.95)), url(${getWeatherImage(code)})`,
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    backgroundAttachment: 'fixed',
    transition: 'background-image 0.5s ease-in-out'
  };
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
  chart = echarts.init(chartDom);

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
        color: '#000000',
        fontWeight: 'bold',
        fontSize: 12
      },
      axisLine: { lineStyle: { color: '#000000', width: 2 } }
    },
    yAxis: [
      {
        type: 'value',
        name: 'Load (MW)',
        nameTextStyle: { padding: [0, 0, 10, 0], fontWeight: '900', color: '#000000', fontSize: 14 },
        splitLine: { lineStyle: { color: 'rgba(0,0,0,0.1)' } },
        axisLabel: { color: '#000000', fontWeight: 'bold', fontSize: 12 },
        axisLine: { show: true, lineStyle: { color: '#000000', width: 2 } }
      },
      {
        type: 'value',
        name: 'Price ($)',
        nameTextStyle: { padding: [0, 0, 10, 0], fontWeight: '900', color: '#b45309', fontSize: 14 },
        splitLine: { show: false },
        axisLabel: { color: '#b45309', fontWeight: 'bold', fontSize: 12 },
        axisLine: { show: true, lineStyle: { color: '#b45309', width: 2 } }
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
        itemStyle: { color: '#94a3b8' },
        lineStyle: { color: '#94a3b8', width: 2, type: 'dashed' },
        smooth: true
      },
      {
        name: 'Hybrid Model Prediction',
        type: 'line',
        data: predictSeries,
        symbol: 'none',
        itemStyle: { color: '#6366f1' },
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
        itemStyle: { color: '#10b981' },
        lineStyle: { color: '#10b981', width: 2 },
        smooth: true,
        z: 10 // ensure it sits somewhere visible
      },
      {
        name: 'Hybrid Model Base',
        type: 'line',
        data: xgbSeries,
        symbol: 'none',
        itemStyle: { color: '#f43f5e' },
        lineStyle: { color: '#f43f5e', width: 1.5, type: 'dotted' },
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
  flex-direction: column;
  align-items: center;
  margin-bottom: 0.5rem;
  gap: 0.5rem;
}

.controls {
  padding: 0 1.5rem;
  width: 100%;
}

.input-row {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1.5rem;
    width: 100%;
}

.control-card {
    padding: 1rem 1.5rem;
    margin: 0;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.btn-card {
    padding: 0.5rem;
    display: flex;
    min-width: 140px;
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
    margin: 8px 0;
    cursor: grab;
}

.slider:active {
    cursor: grabbing;
}

.slider-container {
    position: relative;
    width: 100%;
    display: flex;
    align-items: center;
    padding-top: 5px;
}

.slider-tooltip {
    position: absolute;
    top: -24px;
    transform: translateX(-50%);
    background: var(--primary);
    color: white;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 900;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.2s;
    white-space: nowrap;
    z-index: 10;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
}

.slider-tooltip::after {
    content: '';
    position: absolute;
    top: 100%;
    left: 50%;
    margin-left: -5px;
    border-width: 5px;
    border-style: solid;
    border-color: var(--primary) transparent transparent transparent;
}

.slider:hover ~ .slider-tooltip,
.slider:active ~ .slider-tooltip,
.slider:focus ~ .slider-tooltip {
    opacity: 1;
}

.slider-labels {
    display: flex;
    justify-content: space-between;
    font-size: 0.8rem;
    color: #0f172a;
    font-weight: 800;
}

.controls label {
  display: block;
  font-size: 0.95rem;
  color: #0f172a;
  font-weight: 800;
  margin-bottom: 0.5rem;
}

.input-group {
  display: flex;
  gap: 1rem;
}

input[type="date"] {
  background: rgba(255,255,255,0.7);
  border: 1px solid rgba(0,0,0,0.2);
  color: #000000;
  font-weight: 700;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  outline: none;
  flex: 1;
}

input[type="date"]::-webkit-calendar-picker-indicator {
    filter: none;
    cursor: pointer;
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
  font-size: 0.9rem;
  color: #1e293b; /* Darker for better visibility */
  font-weight: 700;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stat-value {
  font-size: 2rem;
  font-weight: 900;
  color: #000000; /* Pure black for maximum visibility */
  margin-bottom: 0.25rem;
}

.stat-sub {
  font-size: 0.8rem;
  color: #334155;
  font-weight: 600;
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
  justify-content: center;
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
  font-size: 1rem;
  color: #000000;
  font-weight: 700;
}

.context-item strong {
  color: #000000;
  font-weight: 900;
  margin-left: 0.35rem;
  text-decoration: underline;
}

.context-item.is-holiday {
  color: #b45309;
}

.context-item.is-holiday strong {
  color: #b45309;
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

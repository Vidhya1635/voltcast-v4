<template>
  <div class="comparison fade-in">
    <header>
      <h1 class="text-gradient">Multi-Model Comparison</h1>
      <p class="text-muted">Evolution of performance from Persistence baseline to Hybrid Model</p>
    </header>

    <div v-if="comparisonData" class="content">
      <!-- Chart Selection -->
      <div class="card glass tab-container">
        <button v-for="m in metricsRows" :key="m" 
                @click="activeMetric = m"
                :class="{ active: activeMetric === m }">
          {{ m }}
        </button>
      </div>

      <!-- Comparison Chart -->
      <div class="card chart-card">
        <h3>{{ activeMetric }} Comparison (Lower is Better)</h3>
        <div id="compareChart" style="height: 450px;"></div>
        
        <!-- Version Legend -->
        <div class="version-legend">
          <div class="legend-item">
            <span class="legend-dot" style="background: #94a3b8;"></span>
            <div class="legend-text">
              <b>Persistence</b>
              <small>Naive 24-h repeat baseline</small>
            </div>
          </div>
          <div class="legend-item">
            <span class="legend-dot" style="background: #f43f5e;"></span>
            <div class="legend-text">
              <b>XGBoost</b>
              <small>Gradient-boosted tree baseline</small>
            </div>
          </div>
          <div class="legend-item">
            <span class="legend-dot highlight" style="background: #6366f1;"></span>
            <div class="legend-text">
              <b>Hybrid Model <span class="best-tag">BEST</span></b>
              <small>XGBoost + CNN-BiLSTM-Attention Ensemble</small>
            </div>
          </div>
        </div>
      </div>

      <!-- Data Table -->
      <div class="card table-card">
        <h3 style="text-align: center; margin-bottom: 1.5rem; font-weight: 900; font-size: 1.5rem; letter-spacing: 0.02em; color: #000000;">Comparison Dashboard</h3>
        <table>
          <thead>
            <tr>
              <th>
                Model Version
              </th>
              <th>
                MAE
                <div class="th-sub">(Mean Absolute Error)</div>
              </th>
              <th>
                RMSE
                <div class="th-sub">(Root Mean Square Error)</div>
              </th>
              <th>
                MAPE (%)
                <div class="th-sub">(Mean Absolute Percentage Error)</div>
              </th>
              <th>
                Peak MAE
                <div class="th-sub">(Peak Hour Absolute Error)</div>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(metrics, name) in comparisonData" :key="name">
              <td class="font-bold">{{ formatModelName(name) }}</td>
              <td>{{ metrics.test.MAE.toFixed(1) }}</td>
              <td>{{ metrics.test.RMSE.toFixed(1) }}</td>
              <td>{{ metrics.test.MAPE.toFixed(2) }}%</td>
              <td>{{ metrics.test.Peak_MAE.toFixed(1) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import api from '@/api';
import * as echarts from 'echarts';

const comparisonData = ref(null);
const activeMetric = ref('MAE');
const metricsRows = ['MAE', 'RMSE', 'MAPE', 'Peak_MAE'];

let chart = null;

// Only show these 3 models in the comparison (filter out intermediate V1/V2/V3)
const ALLOWED_MODELS = ['Persistence', 'XGBoost', 'V4 Hybrid'];

const fetchData = async () => {
    try {
        const res = await api.get('/api/models');
        // Filter to only keep the 3 meaningful comparison models
        const filtered = {};
        for (const [key, val] of Object.entries(res.data)) {
            if (ALLOWED_MODELS.includes(key)) {
                filtered[key] = val;
            }
        }
        comparisonData.value = filtered;
        setTimeout(initChart, 100);
    } catch (err) {
        console.error(err);
    }
};

const initChart = () => {
    const chartDom = document.getElementById('compareChart');
    if (!chartDom) return;
    chart = echarts.init(chartDom);
    renderChart();
};

const renderChart = () => {
    if (!chart || !comparisonData.value) return;
    
    const models = Object.keys(comparisonData.value);
    const values = models.map(m => comparisonData.value[m].test[activeMetric.value]);
    
    const colors = ['#94a3b8', '#f43f5e', '#6366f1']; // Persistence, XGBoost, Hybrid

    chart.setOption({
        backgroundColor: 'transparent',
        tooltip: { trigger: 'axis' },
        xAxis: { 
            type: 'category', 
            data: models.map(m => formatModelName(m)),
            name: 'Model Iteration',
            nameLocation: 'middle',
            nameGap: 40,
            nameTextStyle: { color: '#000000', fontWeight: 'bold', fontSize: 14 },
            axisLabel: { interval: 0, rotate: 0, color: '#000000', fontWeight: 'bold', fontSize: 12 },
            axisLine: { show: true, lineStyle: { color: '#000000', width: 2 } }
        },
        yAxis: { 
            type: 'value', 
            name: activeMetric.value, 
            nameTextStyle: { color: '#000000', fontWeight: 'bold', fontSize: 14, padding: [0, 0, 10, 0] },
            axisLabel: { color: '#000000', fontWeight: 'bold', fontSize: 12 },
            splitLine: { lineStyle: { color: 'rgba(0,0,0,0.1)' } },
            axisLine: { show: true, lineStyle: { color: '#000000', width: 2 } }
        },
        grid: { bottom: '15%', containLabel: true },
        series: [{
            data: values.map((v, i) => ({
                value: v,
                itemStyle: { color: colors[i % colors.length] }
            })),
            type: 'bar',
            barWidth: '50%',
            label: { show: true, position: 'top', color: '#000000', fontWeight: 'bold', fontSize: 12 }
        }]
    }, true);
};

const formatModelName = (name) => {
    const map = {
        'V1': 'V1 (CNN+BiLSTM+Attention)',
        'DL V1': 'V1 (CNN+BiLSTM+Attention)',
        'V2': 'V2 (BiLSTM+Attention Larger)',
        'DL V2': 'V2 (BiLSTM+Attention Larger)',
        'V3': 'V3 (Ensemble+SWA)',
        'DL V3': 'V3 (Ensemble+SWA)',
        'V4 Hybrid': 'Hybrid Model',
        'DL V4 Hybrid': 'Hybrid Model',
    };
    return map[name] ?? name.replace('DL ', '').replace('V4 Hybrid', 'Hybrid Model');
};

watch(activeMetric, renderChart);

onMounted(fetchData);
</script>

<style scoped>
header { margin-bottom: 2rem; }

.tab-container {
    display: flex;
    gap: 1rem;
    padding: 0.75rem;
    margin-bottom: 1.5rem;
    justify-content: center;
}

.tab-container button {
    background: transparent;
    border: none;
    color: var(--text-muted);
    padding: 0.5rem 1.5rem;
    border-radius: 0.5rem;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.2s;
}

.tab-container button.active {
    background: var(--primary);
    color: white;
}

.chart-card { margin-bottom: 1.5rem; }

.version-legend {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem 2rem;
  margin-top: 1.5rem;
  padding: 1.25rem 1.5rem;
  background: rgba(255, 255, 255, 0.02);
  border-top: 1px solid var(--border);
  border-radius: 0 0 0.75rem 0.75rem;
}

.legend-item {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  flex-shrink: 0;
  margin-top: 4px;
}

.legend-dot.highlight {
  box-shadow: 0 0 8px rgba(99, 102, 241, 0.6);
}

.legend-text {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  line-height: 1.3;
}

.legend-text b {
  font-size: 0.82rem;
  color: var(--text);
}

.legend-text small {
  font-size: 0.72rem;
  color: var(--text-muted);
}

.best-tag {
  display: inline-block;
  background: rgba(99, 102, 241, 0.15);
  color: #818cf8;
  font-size: 0.6rem;
  font-weight: 700;
  padding: 0.1rem 0.4rem;
  border-radius: 0.25rem;
  letter-spacing: 0.05em;
  vertical-align: middle;
}

@media (max-width: 768px) {
  .version-legend {
    grid-template-columns: 1fr;
  }
}

.table-card { padding: 0; overflow: hidden; }
table { width: 100%; border-collapse: collapse; }
th { background: rgba(255,255,255,0.05); padding: 1rem; text-align: left; color: #000000; font-size: 0.85rem; font-weight: 700; }
th .th-sub { font-size: 0.7rem; font-weight: 400; color: #000000; opacity: 0.85; margin-top: 2px; letter-spacing: 0.01em; }
td { padding: 1rem; border-bottom: 1px solid var(--border); font-size: 0.9rem; }
.font-bold { font-weight: 700; color: var(--primary); }
</style>

<template>
  <div class="comparison fade-in">
    <header>
      <h1 class="text-gradient">Multi-Model Comparison</h1>
      <p class="text-muted">Evolution of performance from Persistence baseline to V4 Hybrid</p>
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
      </div>

      <!-- Data Table -->
      <div class="card table-card">
        <h3>Comparison Dashboard</h3>
        <table>
          <thead>
            <tr>
              <th>Model Version</th>
              <th>MAE</th>
              <th>RMSE</th>
              <th>MAPE (%)</th>
              <th>Peak MAE</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(metrics, name) in comparisonData" :key="name">
              <td class="font-bold">{{ name }}</td>
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

const fetchData = async () => {
    try {
        const res = await api.get('/api/models');
        comparisonData.value = res.data;
        setTimeout(initChart, 100);
    } catch (err) {
        console.error(err);
    }
};

const initChart = () => {
    const chartDom = document.getElementById('compareChart');
    if (!chartDom) return;
    chart = echarts.init(chartDom, 'dark');
    renderChart();
};

const renderChart = () => {
    if (!chart || !comparisonData.value) return;
    
    const models = Object.keys(comparisonData.value);
    const values = models.map(m => comparisonData.value[m].test[activeMetric.value]);
    
    const colors = ['#94a3b8', '#f43f5e', '#10b981', '#fbbf24', '#a855f7', '#6366f1'];

    chart.setOption({
        backgroundColor: 'transparent',
        tooltip: { trigger: 'axis' },
        xAxis: { 
            type: 'category', 
            data: models,
            axisLabel: { interval: 0, rotate: 30 }
        },
        yAxis: { type: 'value', name: activeMetric.value, splitLine: { lineStyle: { color: '#1e293b' } } },
        series: [{
            data: values.map((v, i) => ({
                value: v,
                itemStyle: { color: colors[i % colors.length] }
            })),
            type: 'bar',
            barWidth: '50%',
            label: { show: true, position: 'top', color: '#fff' }
        }]
    }, true);
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

.table-card { padding: 0; overflow: hidden; }
table { width: 100%; border-collapse: collapse; }
th { background: rgba(255,255,255,0.05); padding: 1rem; text-align: left; color: var(--text-muted); font-size: 0.85rem; }
td { padding: 1rem; border-bottom: 1px solid var(--border); font-size: 0.9rem; }
.font-bold { font-weight: 700; color: var(--primary); }
</style>

<template>
  <div class="evaluation-page fade-in">
    <header class="page-header">
      <div class="header-content">
        <h1 class="text-gradient">Live Performance & Benchmarks</h1>
        <p class="text-muted">Real-world deployment accuracy vs deep residual corrections</p>
      </div>
      <div v-if="metrics" class="version-badge glass">
        <span>Engine v4.0.2-Stable</span>
      </div>
    </header>

    <div v-if="metrics" class="eval-dashboard">
      <!-- Top Row: Performance Story -->
      <div class="summary-cards">
        <div class="hero-card glass card">
          <div class="hero-label">Total Performance Lift</div>
          <div class="hero-value-group">
            <span class="main-lift success">{{ computeLift('xgb_only_test', 'final_blended_test', 'MAE') }}%</span>
            <TrendingDown :size="48" class="lift-icon success" />
          </div>
          <p class="hero-desc">Aggregate error reduction across all 168 forecast horizons compared to the XGBoost baseline.</p>
        </div>

        <!-- Live Intelligence Evaluation Section -->
        <div class="stat-card glass card live-eval-card" :class="{ 'no-data': !liveMetrics }">
          <div class="card-header">
            <Radio :size="20" :class="liveMetrics ? 'success' : 'text-muted'" />
            <span>Deployment Accuracy</span>
          </div>
          <div v-if="liveMetrics">
            <div class="stat-value">{{ liveMetrics.mae.toFixed(1) }} <small>MW</small></div>
            <div class="live-subtitle">Real-world performance</div>
            <div class="live-meta">
              <span>MAPE: <b>{{ liveMetrics.mape.toFixed(2) }}%</b></span>
              <span>Samples: <b>{{ liveMetrics.sample_size }}</b></span>
            </div>
          </div>
          <div v-else class="empty-live">
            <p>Gathering deployment data...</p>
            <small>Perform more forecasts to see live metrics.</small>
          </div>
        </div>

        <div class="stat-card glass card">
          <div class="card-header">
            <Zap :size="20" class="warning-text" />
            <span>Peak Demand Error</span>
          </div>
          <div class="stat-value">{{ (metrics.final_blended_test.MAPE * 1.5).toFixed(2) }}%</div>
          <div class="stat-meta">Critical load accuracy</div>
        </div>
      </div>

      <!-- Middle Row: Diagnostics -->
      <div class="diagnostics-grid">
        <div class="card chart-area">
          <div class="card-header">
            <BarChart3 :size="18" />
            <span>Error Decay across Forecast Horizon</span>
          </div>
          <div id="horizonChart" class="echart-container"></div>
        </div>

        <div class="card detail-area">
          <div class="card-header">
            <SettingsIcon :size="18" />
            <span>Architecture & Hyperparameters</span>
          </div>
          <div class="params-list">
            <div class="param-row">
              <span>Backbone</span>
              <div class="badge primary">CNN-LSTM + Self Attention</div>
            </div>
            <div class="param-row">
              <span>Ensemble Size</span>
              <b>{{ metrics.hyperparameters.n_ensemble }} Units</b>
            </div>
            <div class="param-row">
              <span>Hidden Units</span>
              <b>{{ metrics.hyperparameters.lstm_hidden }}</b>
            </div>
            <div class="param-row">
              <span>Learning Rate</span>
              <code class="code-badge">{{ metrics.hyperparameters.lr }}</code>
            </div>
            <div class="param-row">
              <span>Dropout Rate</span>
              <b>{{ (metrics.hyperparameters.dropout * 100).toFixed(0) }}%</b>
            </div>
          </div>
          
          <div class="blend-optimization">
            <h4>Optimization Result</h4>
            <div class="blend-visual">
              <div class="blend-bar">
                <div class="segment hybrid" :style="{ width: (metrics.best_blend_alpha * 100) + '%' }"></div>
                <div class="segment xgb" :style="{ width: ((1 - metrics.best_blend_alpha) * 100) + '%' }"></div>
              </div>
              <div class="blend-legend">
                <span>Residual Hybrid ({{ (metrics.best_blend_alpha * 100).toFixed(0) }}%)</span>
                <span>Base Line ({{ ((1 - metrics.best_blend_alpha) * 100).toFixed(0) }}%)</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Bottom Row: Training Stats -->
      <div class="training-row">
        <div class="card glass">
          <div class="card-header"><Activity :size="16" /><span>Ensemble Diversity (Validation Losses)</span></div>
          <div class="loss-chips">
            <div v-for="(loss, idx) in metrics.individual_val_losses" :key="idx" class="loss-chip">
              <span class="seed">Seed {{ metrics.hyperparameters.seeds[idx] }}</span>
              <span class="val">{{ loss.toFixed(5) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="loading-full">
      <div class="spinner-large"></div>
      <h3>Synthesizing Evaluation Data...</h3>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue';
import { 
  TrendingDown, Activity, Zap, BarChart3, 
  Settings as SettingsIcon, Radio, AlertTriangle, Info 
} from 'lucide-vue-next';
import api from '@/api';
import * as echarts from 'echarts';

const metrics = ref(null);
const liveMetrics = ref(null);

const fetchData = async () => {
  try {
    const [statsRes, liveRes] = await Promise.all([
      api.get('/api/evaluation'),
      api.get('/api/live-evaluation')
    ]);
    metrics.value = statsRes.data;
    liveMetrics.value = liveRes.data.status === 'success' ? liveRes.data : null;
    nextTick(initHorizonChart);
  } catch (err) {
    console.error("Evaluation fetch failed:", err);
  }
};

onMounted(fetchData);

const computeLift = (baseKey, targetKey, metric) => {
    if (!metrics.value || !metrics.value[baseKey] || !metrics.value[targetKey]) return "0.0";
    const base = metrics.value[baseKey][metric];
    const target = metrics.value[targetKey][metric];
    return (((base - target) / base) * 100).toFixed(2);
};

const initHorizonChart = () => {
    const chartDom = document.getElementById('horizonChart');
    if (!chartDom || !metrics.value) return;
    const chart = echarts.init(chartDom, 'dark');

    const horizon = Array.from({length: 168}, (_, i) => i + 1);
    const xgbError = metrics.value.error_by_horizon?.xgb || [];
    const hybridError = metrics.value.error_by_horizon?.hybrid || [];

    chart.setOption({
        backgroundColor: 'transparent',
        tooltip: { trigger: 'axis' },
        legend: { data: ['XGBoost MAE', 'Hybrid V4 MAE'], textStyle: { color: '#94a3b8' } },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: { type: 'category', data: horizon, axisLabel: { color: '#94a3b8' } },
        yAxis: { type: 'value', name: 'MAE (MW)', axisLabel: { color: '#94a3b8' }, splitLine: { lineStyle: { color: '#1e293b' } } },
        series: [
            { name: 'XGBoost MAE', type: 'line', data: xgbError, smooth: true, lineStyle: { color: '#f43f5e' }, itemStyle: { color: '#f43f5e' } },
            { name: 'Hybrid V4 MAE', type: 'line', data: hybridError, smooth: true, lineStyle: { color: '#10b981' }, itemStyle: { color: '#10b981' }, areaStyle: { color: 'rgba(16,185,129,0.1)' } }
        ]
    });
};
</script>

<style scoped>
.evaluation-page {
  padding: 2rem;
}

.eval-dashboard {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.summary-cards {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 1.5rem;
}

.hero-card {
  padding: 2rem;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(30, 41, 59, 0.4) 100%);
}

.hero-label {
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

.hero-value-group {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.main-lift {
  font-size: 3.5rem;
  font-weight: 800;
  letter-spacing: -0.05em;
}

.lift-icon {
  opacity: 0.8;
}

.hero-desc {
  font-size: 0.95rem;
  color: var(--text-muted);
  max-width: 400px;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  margin: 0.5rem 0;
}

.stat-meta {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.diagnostics-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1.5rem;
}

.echart-container {
  height: 400px;
  width: 100%;
}

.params-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1rem;
}

.param-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.9rem;
}

.badge {
  padding: 0.2rem 0.6rem;
  border-radius: 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
}

.badge.primary { background: rgba(99, 102, 241, 0.1); color: #818cf8; }

.loss-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 1rem;
}

.loss-chip {
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border);
  padding: 0.5rem 1rem;
  border-radius: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.loss-chip .seed { font-size: 0.7rem; color: var(--text-muted); }
.loss-chip .val { font-size: 0.9rem; font-weight: 600; font-family: monospace; }

.loading-full {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 50vh;
  gap: 1.5rem;
}

.success { color: var(--success); }
.warning-text { color: var(--warning); }

@media (max-width: 1024px) {
  .summary-cards, .diagnostics-grid {
    grid-template-columns: 1fr;
  }
}
</style>

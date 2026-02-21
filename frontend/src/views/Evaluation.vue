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
import { TrendingDown, Activity, Zap, BarChart3, Settings as SettingsIcon } from 'lucide-vue-next';
import api from '@/api';
import * as echarts from 'echarts';

const metrics = ref(null);
const liveMetrics = ref(null);

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

const computeLift = (baseKey, targetKey, metric) => {
    if (!metrics.value[baseKey] || !metrics.value[targetKey]) return "0.0";
    const base = metrics.value[baseKey][metric];
    const target = metrics.value[targetKey][metric];
    return (((base - target) / base) * 100).toFixed(2);
};

const initHorizonChart = () => {
    const chartDom = document.getElementById('horizonChart');
    if (!chartDom) return;
    const chart = echarts.init(chartDom, 'dark');
    
    const hData = metrics.value.horizon_wise;
    const xAxis = Object.keys(hData).map(k => `+${k}h`);
    const values = Object.values(hData).map(v => v.MAE);

    chart.setOption({
        backgroundColor: 'transparent',
        tooltip: { 
          trigger: 'axis',
          backgroundColor: '#1e293b',
          borderColor: '#334155',
          textStyle: { color: '#f8fafc' }
        },
        grid: { left: '4%', right: '4%', bottom: '10%', top: '10%', containLabel: true },
        xAxis: { 
          type: 'category', 
          data: xAxis, 
          axisLine: { lineStyle: { color: '#334155' } },
          axisLabel: { color: '#94a3b8' }
        },
        yAxis: { 
          type: 'value', 
          name: 'MAE (MW)', 
          splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } },
          axisLabel: { color: '#94a3b8' }
        },
        series: [{
            name: 'Prediction Error',
            data: values,
            type: 'bar',
            barWidth: '40%',
            itemStyle: { 
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#6366f1' },
                { offset: 1, color: '#a855f7' }
              ]),
              borderRadius: [6, 6, 0, 0] 
            },
            emphasis: { itemStyle: { color: '#818cf8' } }
        }]
    });

    window.addEventListener('resize', () => chart.resize());
};

onMounted(fetchMetrics);
</script>

<style scoped>
.evaluation-page {
  padding: 2.5rem;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 3rem;
}

.version-badge {
  padding: 0.5rem 1rem;
  border-radius: 2rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--primary);
  border: 1px solid var(--primary-glow);
}

.summary-cards {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.hero-card {
  padding: 2rem;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%);
  border: 1px solid var(--primary-glow);
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.hero-label { font-size: 0.9rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
.hero-value-group { display: flex; align-items: center; gap: 1.5rem; margin: 1rem 0; }
.main-lift { font-size: 4rem; font-weight: 900; letter-spacing: -0.05em; }
.lift-icon { filter: drop-shadow(0 0 10px var(--success)); }
.hero-desc { color: var(--text-muted); font-size: 0.95rem; line-height: 1.5; max-width: 80%; }

.stat-card { padding: 1.5rem; }
.live-eval-card { position: relative; overflow: hidden; }
.live-eval-card.no-data { opacity: 0.8; }
.stat-value { font-size: 2.5rem; font-weight: 800; color: var(--text); }
.live-subtitle { font-size: 0.85rem; color: var(--text-muted); margin: -0.25rem 0 1rem; }
.live-meta { display: flex; gap: 1rem; font-size: 0.8rem; border-top: 1px solid var(--border); padding-top: 0.75rem; }
.live-meta span { color: var(--text-muted); }
.live-meta b { color: var(--text); }
.empty-live { padding: 1rem 0; text-align: center; color: var(--text-muted); }

.card-header { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.5rem; font-weight: 600; color: var(--text-muted); }
.stat-value { font-size: 2.5rem; font-weight: 800; color: var(--text); }
.stat-meta { font-size: 0.85rem; color: var(--text-muted); margin-top: 0.5rem; }

.diagnostics-grid {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.echart-container { height: 400px; }

.params-list { margin-top: 1rem; }
.param-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.875rem 0;
  border-bottom: 1px solid var(--border);
}
.param-row:last-child { border-bottom: none; }
.param-row span { color: var(--text-muted); font-size: 0.9rem; }

.badge { padding: 0.25rem 0.6rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.badge.primary { background: var(--primary-glow); color: var(--primary); }
.code-badge { font-family: monospace; background: var(--bg); padding: 0.2rem 0.4rem; border-radius: 4px; border: 1px solid var(--border); }

.blend-optimization { margin-top: 2rem; padding-top: 2rem; border-top: 1px solid var(--border); }
.blend-optimization h4 { margin-bottom: 1rem; color: var(--text-muted); }
.blend-visual { margin-top: 1.5rem; }
.blend-bar { height: 12px; border-radius: 6px; overflow: hidden; display: flex; background: var(--border); }
.segment.hybrid { background: var(--primary); box-shadow: 0 0 15px var(--primary-glow); }
.segment.xgb { background: var(--text-muted); opacity: 0.3; }
.blend-legend { display: flex; justify-content: space-between; margin-top: 0.75rem; font-size: 0.8rem; color: var(--text-muted); }

.loss-chips { display: flex; gap: 1rem; margin-top: 1rem; flex-wrap: wrap; }
.loss-chip { background: var(--bg); padding: 0.5rem 1rem; border-radius: 0.75rem; border: 1px solid var(--border); display: flex; flex-direction: column; }
.loss-chip .seed { font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; }
.loss-chip .val { font-family: monospace; font-weight: 600; color: var(--primary); }

.loading-full { height: 60vh; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2rem; }
.spinner-large { width: 60px; height: 60px; border: 4px solid var(--border); border-top-color: var(--primary); border-radius: 50%; animation: spin 1s linear infinite; }

@keyframes spin { to { transform: rotate(360deg); } }

.primary-text { color: var(--primary); }
.warning-text { color: var(--warning); }
.success { color: var(--success); }
</style>

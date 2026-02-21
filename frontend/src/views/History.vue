<template>
  <div class="history fade-in">
    <header>
      <h1 class="text-gradient">Forecast History</h1>
      <p class="text-muted">Review and export previous prediction runs stored in database</p>
    </header>

    <div class="history-container card">
      <table v-if="history.length">
        <thead>
          <tr>
            <th>ID</th>
            <th>Requested At</th>
            <th>Forecast Start</th>
            <th>Peak Demand</th>
            <th>Avg Load</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in history" :key="item.id">
            <td>#{{ item.id }}</td>
            <td>{{ formatFullDate(item.created_at) }}</td>
            <td>{{ formatDate(item.forecast_start) }}</td>
            <td>{{ formatNum(item.peak_load) }} MW</td>
            <td>{{ formatNum(item.avg_load) }} MW</td>
            <td>
              <span class="status-badge" :class="item.status">{{ item.status }}</span>
            </td>
            <td>
              <div class="actions">
                <button @click="downloadCSV(item.id)" title="Download CSV"><Download :size="16" /></button>
                <button @click="deleteRequest(item.id)" title="Delete Entry" class="btn-delete"><Trash2 :size="16" /></button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      
      <div v-else class="empty-state">
        <div class="icon">📁</div>
        <p>No forecasts generated yet.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { Download, Trash2 } from 'lucide-vue-next';
import api from '@/api';
import { format, parseISO } from 'date-fns';

const history = ref([]);

const fetchHistory = async () => {
    try {
        const res = await api.get('/api/history');
        history.value = res.data;
    } catch (err) {
        console.error("Failed to fetch history", err);
    }
};

const deleteRequest = async (id) => {
    if (!confirm(`Are you sure you want to delete forecast #${id}?`)) return;
    try {
        await api.delete(`/api/history/${id}`);
        history.value = history.value.filter(item => item.id !== id);
    } catch (err) {
        alert("Failed to delete forecast.");
    }
};

const formatFullDate = (ds) => format(parseISO(ds), 'MMM do yyyy, HH:mm');
const formatDate = (ds) => format(parseISO(ds), 'MMM do, HH:mm');
const formatNum = (v) => v ? Math.round(v).toLocaleString() : '—';

const downloadCSV = async (id) => {
    try {
        const res = await api.get(`/api/history/${id}`);
        const data = res.data.results;
        
        let csv = "hour_offset,timestamp,predicted_load_mw,xgb_base_mw,dl_residual_mw\n";
        data.forEach(row => {
            csv += `${row.hour_offset},${row.timestamp},${row.predicted_load},${row.xgb_load},${row.dl_residual}\n`;
        });
        
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.setAttribute('href', url);
        a.setAttribute('download', `forecast_${id}_${res.data.request.forecast_start}.csv`);
        a.click();
    } catch (err) {
        alert("Failed to export data.");
    }
};

const viewDetail = (id) => {
    // For now, it just scrolls to top and maybe we can add a modal or route
    alert("Viewing details for request #" + id);
};

onMounted(fetchHistory);
</script>

<style scoped>
header {
  margin-bottom: 2rem;
}

.history-container {
  padding: 0;
  overflow: hidden;
}

table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

th {
  background: rgba(255,255,255,0.05);
  padding: 1rem 1.5rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border);
}

td {
  padding: 1rem 1.5rem;
  font-size: 0.9rem;
  border-bottom: 1px solid var(--border);
}

tr:last-child td { border-bottom: none; }

tr:hover td {
  background: rgba(255,255,255,0.02);
}

.status-badge {
  font-size: 0.75rem;
  padding: 0.25rem 0.6rem;
  border-radius: 1rem;
  font-weight: 600;
  text-transform: capitalize;
}

.status-badge.completed { background: rgba(16, 185, 129, 0.1); color: var(--success); }
.status-badge.failed { background: rgba(244, 63, 94, 0.1); color: var(--accent); }
.status-badge.processing { background: rgba(245, 158, 11, 0.1); color: var(--warning); }

.actions {
  display: flex;
  gap: 0.5rem;
}

.actions button {
  background: var(--surface-hover);
  border: 1px solid var(--border);
  color: var(--text-muted);
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.4rem;
  cursor: pointer;
  transition: all 0.2s;
}

.actions button:hover {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
}

.actions button.btn-delete:hover {
  background: var(--accent);
  border-color: var(--accent);
}

.empty-state {
  padding: 4rem;
  text-align: center;
  color: var(--text-muted);
}

.empty-state .icon { font-size: 3rem; margin-bottom: 1rem; }
</style>

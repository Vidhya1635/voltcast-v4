<template>
  <aside class="sidebar">
    <div class="logo">
      <div class="logo-icon">⚡</div>
      <div class="logo-text">Volt<span>Cast</span></div>
    </div>
    
    <nav class="nav">
      <router-link to="/" class="nav-item">
        <LayoutDashboard :size="20" />
        <span>Forecast</span>
      </router-link>
      <router-link to="/live" class="nav-item live-link">
        <Radio :size="20" />
        <span>Live Mode</span>
      </router-link>
      <router-link to="/history" class="nav-item">
        <HistoryIcon :size="20" />
        <span>History</span>
      </router-link>
      <router-link to="/evaluation" class="nav-item">
        <Activity :size="20" />
        <span>Evaluation</span>
      </router-link>
      <router-link to="/comparison" class="nav-item">
        <BarChart3 :size="20" />
        <span>Model Comparison</span>
      </router-link>
      
      <div class="nav-spacer"></div>
      
      <button @click="$emit('open-settings')" class="nav-item settings-trigger">
        <SettingsIcon :size="20" />
        <span>Settings</span>
      </button>
    </nav>
    
    <div class="status-indicator">
      <div class="status-pill">
        <div class="dot" :class="status"></div>
        <span>{{ getStatusText(status) }}</span>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { 
  LayoutDashboard, History as HistoryIcon, Activity, BarChart3, Radio,
  Settings as SettingsIcon
} from 'lucide-vue-next';
import api from '@/api';

const status = ref('offline'); // 'online', 'warming', 'offline', 'error'

const checkBackend = async () => {
  try {
    const res = await api.get('/api/health', { timeout: 10000 });
    if (res.data.status === 'healthy') {
      status.value = res.data.model_ready ? 'online' : 'warming';
    } else {
      status.value = 'error';
    }
  } catch (err) {
    status.value = 'offline';
  }
};

const getStatusText = (s) => {
    if (s === 'online') return 'Backend: Online';
    if (s === 'warming') return 'Backend: Warming Up...';
    if (s === 'error') return 'Backend: Error';
    return 'Backend: Offline';
};

onMounted(() => {
  checkBackend();
  setInterval(checkBackend, 10000);
});
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  height: 100vh;
  position: sticky;
  top: 0;
}

.logo {
  padding: 2.5rem 2rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.logo-icon {
  font-size: 1.5rem;
  background: var(--primary);
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.75rem;
}

.logo-text {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -0.05em;
  color: var(--text);
}

.logo-text span {
  color: var(--primary);
}

.nav {
  padding: 0 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
}

.nav-spacer {
  flex: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.875rem 1rem;
  color: var(--text-muted);
  text-decoration: none;
  border-radius: 0.75rem;
  transition: all 0.2s;
  font-weight: 500;
  background: none;
  border: none;
  width: 100%;
  cursor: pointer;
}

.nav-item:hover {
  background: var(--surface-hover);
  color: var(--text);
}

.nav-item.router-link-active {
  background: var(--primary);
  color: white;
  box-shadow: 0 4px 12px var(--primary-glow);
}

.status-indicator {
  margin-top: auto;
  padding: 2rem;
  border-top: 1px solid var(--border);
}

.status-pill {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: var(--bg);
  border-radius: 0.75rem;
  font-size: 0.875rem;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
}
.dot.online { background: var(--success); box-shadow: 0 0 8px var(--success); }
.dot.warming { background: var(--warning); box-shadow: 0 0 8px var(--warning); }
.dot.error { background: var(--accent); }

@media (max-width: 768px) {
  .sidebar {
    width: 100%;
    height: auto;
    position: fixed;
    bottom: 0;
    top: auto;
    flex-direction: row;
    z-index: 1000;
    border-right: none;
    border-top: 1px solid var(--border);
    justify-content: space-around;
  }
  
  .logo {
    display: none;
  }
  
  .nav {
    flex-direction: row;
    width: 100%;
    padding: 0;
    gap: 0;
    justify-content: space-evenly;
  }
  
  .nav-item {
    flex-direction: column;
    padding: 0.5rem;
    font-size: 0.7rem;
    gap: 0.25rem;
    border-radius: 0;
  }
  
  .nav-item span {
    display: block;
  }
  
  .nav-spacer, .status-indicator {
    display: none;
  }
}
</style>

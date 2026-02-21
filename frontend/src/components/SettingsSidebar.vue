<template>
  <transition name="slide">
    <div v-if="isOpen" class="settings-sidebar glass">
      <div class="settings-header">
        <div class="header-title">
          <SettingsIcon :size="20" />
          <h3>System Settings</h3>
        </div>
        <button @click="$emit('close')" class="close-btn">
          <X :size="24" />
        </button>
      </div>

      <div class="settings-content">
        <div class="settings-section">
          <h4>Interface Theme</h4>
          <p class="section-desc">Choose your preferred visual style for the platform.</p>
          
          <div class="theme-picker">
            <button 
              @click="setTheme('dark')" 
              :class="['theme-btn', { active: currentTheme === 'dark' }]"
            >
              <Moon :size="24" />
              <span>Dark Mode</span>
              <Check v-if="currentTheme === 'dark'" :size="16" class="check-icon" />
            </button>
            
            <button 
              @click="setTheme('light')" 
              :class="['theme-btn', { active: currentTheme === 'light' }]"
            >
              <Sun :size="24" />
              <span>Light Mode</span>
              <Check v-if="currentTheme === 'light'" :size="16" class="check-icon" />
            </button>
          </div>
        </div>

        <div class="settings-section">
          <h4>Alert Configurations</h4>
          <p class="section-desc">Display threshold for demand-response warnings.</p>
          <div class="input-row">
             <span>Critical Peak: <strong>21,000 MW</strong></span>
          </div>
        </div>
      </div>

      <div class="settings-footer">
        <p>VoltCast Intelligence Engine v4.0.2</p>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { Settings as SettingsIcon, X, Moon, Sun, Check } from 'lucide-vue-next';

defineProps({
  isOpen: Boolean
});

const emit = defineEmits(['close']);

const currentTheme = ref('dark');

const setTheme = (theme) => {
  currentTheme.value = theme;
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('voltcast-theme', theme);
};

onMounted(() => {
  const saved = localStorage.getItem('voltcast-theme') || 'dark';
  setTheme(saved);
});
</script>

<style scoped>
.settings-sidebar {
  position: fixed;
  top: 0;
  right: 0;
  width: var(--settings-width);
  height: 100vh;
  z-index: 1000;
  background: var(--surface);
  border-left: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  box-shadow: -10px 0 30px rgba(0, 0, 0, 0.3);
}

.settings-header {
  padding: 1.5rem;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: var(--primary);
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  transition: color 0.2s;
}

.close-btn:hover {
  color: var(--text);
}

.settings-content {
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
}

.settings-section {
  margin-bottom: 2rem;
}

.settings-section h4 {
  margin-bottom: 0.5rem;
  font-size: 1rem;
}

.section-desc {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 1.25rem;
}

.theme-picker {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.theme-btn {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 0.75rem;
  color: var(--text);
  cursor: pointer;
  position: relative;
  transition: all 0.2s;
}

.theme-btn:hover {
  border-color: var(--primary);
}

.theme-btn.active {
  border-color: var(--primary);
  background: var(--surface-hover);
}

.check-icon {
  position: absolute;
  right: 1rem;
  color: var(--primary);
}

.settings-footer {
  padding: 1.5rem;
  border-top: 1px solid var(--border);
  text-align: center;
  font-size: 0.75rem;
  color: var(--text-muted);
}

/* Transitions */
.slide-enter-active, .slide-leave-active {
  transition: transform 0.3s ease;
}
.slide-enter-from, .slide-leave-to {
  transform: translateX(100%);
}
</style>

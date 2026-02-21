<template>
  <div class="app-layout">
    <Sidebar @open-settings="isSettingsOpen = true" />
    <main class="content-area">
      <router-view></router-view>
    </main>
    <SettingsSidebar :isOpen="isSettingsOpen" @close="isSettingsOpen = false" />
  </div>
</template>

<script setup>
import { ref } from 'vue';
import Sidebar from './components/Sidebar.vue';
import SettingsSidebar from './components/SettingsSidebar.vue';

const isSettingsOpen = ref(false);
</script>

<style>
.app-layout {
  display: flex;
  width: 100%;
}

.content-area {
  flex: 1;
  min-height: 100vh;
  background: var(--bg);
  overflow-y: auto;
}

@media (max-width: 768px) {
  .app-layout {
    flex-direction: column;
  }
  
  .content-area {
    padding-bottom: 5rem;
  }
}
</style>

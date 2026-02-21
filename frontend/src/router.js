import { createRouter, createWebHistory } from 'vue-router';
import Dashboard from './views/Dashboard.vue';
import LiveDashboard from './views/LiveDashboard.vue';
import History from './views/History.vue';
import Evaluation from './views/Evaluation.vue';
import ModelComparison from './views/ModelComparison.vue';

const routes = [
    { path: '/', name: 'Dashboard', component: Dashboard },
    { path: '/live', name: 'LiveMode', component: LiveDashboard },
    { path: '/history', name: 'History', component: History },
    { path: '/evaluation', name: 'Evaluation', component: Evaluation },
    { path: '/comparison', name: 'Comparison', component: ModelComparison },
];

const router = createRouter({
    history: createWebHistory(),
    routes,
});

export default router;

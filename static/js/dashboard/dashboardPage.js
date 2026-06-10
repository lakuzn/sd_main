// js/dashboard/dashboardPage.js
import { initDashboardFilters } from './dashboardFilters.js';
import { initSocketDashboard } from './dashboardSocket.js';

let socket = null;

export function initDashboardPage() {
    initSocketDashboard();
    initDashboardFilters();
}
// js/dashboard/dashboardFilters.js
import { filtersState, getStateParams, resetState } from './filtersState.js';
import { updateCardsContainer } from './filterUtils.js';
import { initCategoryFilter } from './filterCategory.js';
import { initExecutorFilter } from './filterExecutor.js';
import { initApplicantFilter } from './filterApplicant.js';
import { initHostNameFilter } from './filterHostName.js';
import { initResetFilter } from './filterReset.js';
import { initExportFilter } from './filterExport.js';

export async function initDashboardFilters() {
    const bar = document.getElementById('dashboardFilters');
    if (!bar) return;

    const descriptionEl = document.querySelector('.content__description');
    const originalDescription = descriptionEl?.textContent || '';

    async function applyFilters() {
        const params = getStateParams();
        const hasFilters = params.toString().length > 0;

        const pagination = document.querySelector('.pagination');
        if (pagination) pagination.style.display = 'none';

        try {
            const r = await fetch('/filter?' + params.toString());
            if (!r.ok) return;
            const data = await r.json();

            updateCardsContainer(data.html, data.count, hasFilters, originalDescription);
        } catch (e) {
            console.error('Ошибка фильтрации дашборда:', e);
        }
    }

    // Инициализация всех фильтров
    await initCategoryFilter(applyFilters);
    await initExecutorFilter(applyFilters);
    initApplicantFilter(applyFilters);
    initHostNameFilter(applyFilters);
    initResetFilter();
    initExportFilter();
}
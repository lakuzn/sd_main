// js/dashboard/dashboardFilters.js
import { filtersState, getStateParams, hasActiveFilters, resetState } from './filtersState.js';
import { updateCardsContainer } from './filterUtils.js';
import { initCategoryFilter } from './filterCategory.js';
import { initExecutorFilter } from './filterExecutor.js';
import { initApplicantFilter } from './filterApplicant.js';
import { initHostNameFilter } from './filterHostName.js';

export async function initDashboardFilters() {
    const bar = document.getElementById('dashboardFilters');
    if (!bar) return;

    const descriptionEl = document.querySelector('.content__description');
    const originalDescription = descriptionEl?.textContent || '';
    const resetBtn = document.getElementById('filterReset');

    let categoryFilter = null;
    let executorFilter = null;
    let applicantFilter = null;
    let hostNameFilter = null;

    function updateResetButtonVisibility() {
        if (resetBtn) {
            resetBtn.style.display = hasActiveFilters() ? 'flex' : 'none';
        }
    }

    async function applyFilters() {
        const params = getStateParams();
        const hasFilters = hasActiveFilters();

        const pagination = document.querySelector('.pagination');
        if (pagination) pagination.style.display = 'none';

        try {
            const r = await fetch('/filter?' + params.toString());
            if (!r.ok) return;
            const data = await r.json();

            updateCardsContainer(data.html, data.count, hasFilters, originalDescription);
            updateResetButtonVisibility();
        } catch (e) {
            console.error('Ошибка фильтрации дашборда:', e);
        }
    }

    function resetAllFilters() {
        resetState();

        categoryFilter?.reset();
        executorFilter?.reset();
        applicantFilter?.reset();
        hostNameFilter?.reset();

        applyFilters();
    }

    // Инициализация всех фильтров
    categoryFilter = await initCategoryFilter(applyFilters);
    executorFilter = await initExecutorFilter(applyFilters);
    applicantFilter = await initApplicantFilter(applyFilters);
    hostNameFilter = initHostNameFilter(applyFilters);

    // Инициализация кнопки сброса
    if (resetBtn) {
        resetBtn.style.display = 'none';
        resetBtn.addEventListener('click', resetAllFilters);
    }

    updateResetButtonVisibility();
}
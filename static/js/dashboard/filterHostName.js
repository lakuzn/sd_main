// js/dashboard/filterHostName.js
import { filtersState, updateState } from './filtersState.js';

export function initHostNameFilter(applyFilters) {
    const input = document.getElementById('filterHostName');
    if (!input) return;

    let timer = null;
    input.addEventListener('input', () => {
        clearTimeout(timer);
        timer = setTimeout(() => {
            updateState('host_name', input.value.trim());
            applyFilters();
        }, 300);
    });
}
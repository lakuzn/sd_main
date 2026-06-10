// js/dashboard/filterExecutor.js
import { createDropdown } from '../common/dropdown.js';
import { filtersState, updateState } from './filtersState.js';

export async function initExecutorFilter(applyFilters) {
    const container = document.getElementById('filterExecutor');
    if (!container) return null;

    let options = { executors: [] };
    try {
        const r = await fetch('/api/dashboard/filter-options');
        if (r.ok) options = await r.json();
    } catch (e) { /* fallback */ }

    return createDropdown({
        button: 'filterExecutor-button',
        list: 'filterExecutor',
        options: [{ id: '', name: 'Все исполнители' }, ...options.executors],
        initialValue: '',
        displayKey: 'name',
        valueKey: 'id',
        returnObject: true,
        listItemClass: 'filters__dropdown-item',
        placeholder: 'Все исполнители',
        onSelect: (val) => {
            updateState('executor_id', val.id || '');
            applyFilters();
        }
    });
}
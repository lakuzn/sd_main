// js/dashboard/filterCategory.js
import { createDropdown } from '../common/dropdown.js';
import { filtersState, updateState } from './filtersState.js';

export async function initCategoryFilter(applyFilters) {
    const container = document.getElementById('filterCategory');
    if (!container) return null;

    let options = { categories: [] };
    try {
        const r = await fetch('/api/dashboard/filter-options');
        if (r.ok) options = await r.json();
    } catch (e) { /* fallback */ }

    return createDropdown({
        button: 'filterCategory-button',
        list: 'filterCategory',
        options: [{ id: '', name: 'Все категории' }, ...options.categories],
        initialValue: '',
        displayKey: 'name',
        valueKey: 'id',
        returnObject: true,
        listItemClass: 'filters__dropdown-item',
        placeholder: 'Все категории',
        onSelect: (val) => {
            updateState('category_id', val.id || '');
            applyFilters();
        }
    });
}
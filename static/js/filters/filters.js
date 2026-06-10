// js/filters/filters.js
import { initDropdownFilters } from './dropdownFilters.js';
import { fetchFilterOptions } from '../api.js';

let currentFilters = {
    category: null,
    priority: null,
    status: null
};

function applyFilters() {
    const cards = document.querySelectorAll('.content__card');
    let visibleCount = 0;

    cards.forEach(card => {
        let visible = true;

        if (currentFilters.category) {
            const catEl = card.querySelector('.card__category');
            if (!catEl || catEl.textContent.trim() !== currentFilters.category) visible = false;
        }

        if (visible && currentFilters.priority) {
            const prioEl = card.querySelector('.ticket__priority');
            if (!prioEl || prioEl.textContent.trim() !== currentFilters.priority) visible = false;
        }

        if (visible && currentFilters.status) {
            const statusEl = card.querySelector('.ticket__status');
            if (!statusEl || statusEl.textContent.trim() !== currentFilters.status) visible = false;
        }

        card.style.display = visible ? '' : 'none';
        if (visible) visibleCount++;
    });

    const noResultsEl = document.getElementById('no-results');
    if (noResultsEl) {
        noResultsEl.classList.toggle('hidden', visibleCount > 0);
    }
}

export async function initFilters() {
    const optionsData = await fetchFilterOptions();
    if (!optionsData) return;

    const categoryOptions = [...optionsData.categories];
    const priorityOptions = [...optionsData.priorities];
    const statusOptions = [...optionsData.statuses];

    initDropdownFilters('filterCategory', categoryOptions, value => {
        currentFilters.category = value === 'Все' ? null : value;
        applyFilters();
    }, 'Все категории', true);

    initDropdownFilters('filterPriority', priorityOptions, value => {
        currentFilters.priority = value === 'Все' ? null : value;
        applyFilters();
    }, 'Все приоритеты', true);

    initDropdownFilters('filterStatus', statusOptions, value => {
        currentFilters.status = value === 'Все' ? null : value;
        applyFilters();
    }, 'Все статусы', true);
}
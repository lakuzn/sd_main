import { initDropdownFilters } from "./dropdownFilters.js";
import { fetchFilterOptions } from "./api.js";

let currentFilters = {
    category: null,
    priority: null,
    status: null
}

function applyFilters() {
    const cards = document.querySelectorAll('.content__card');

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
    });

    const hasVisible = Array.from(cards).some(card => card.style.display !== 'none');
    const noResultsEl = document.getElementById('no-results');
    if (noResultsEl) {
        noResultsEl.classList.toggle('hidden', hasVisible);
    }
}

export async function initFilters() {
    const optionsData = await fetchFilterOptions();

    const categoryOptions = ['Все категории', ...optionsData.categories];
    const priorityOptions = ['Все приоритеты', ...optionsData.priorities];
    const statusOptions = ['Все статусы', ...optionsData.statuses];

    initDropdownFilters('filterCategory', categoryOptions, value => {
        currentFilters.category = value === 'Все категории' ? null : value;
        applyFilters();
    }, 'Все категории', true);

    initDropdownFilters('filterPriority', priorityOptions, value => {
        currentFilters.priority = value === 'Все приоритеты' ? null : value;
        applyFilters();
    }, 'Все приоритеты', true);

    initDropdownFilters('filterStatus', statusOptions, value => {
        currentFilters.status = value === 'Все статусы' ? null : value;
        applyFilters();
    }, 'Все статусы', true);
}
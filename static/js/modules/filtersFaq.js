import { fetchFilterOptions } from "../api/api.js";
import { initDropdownFilters } from "./dropdownFilters.js";

let currentFilter = {
    category: null
}

function applyFaqFilters() {
    const faqGroups = document.querySelectorAll('.faqs-group');

    faqGroups.forEach(group => {
        const groupCategory = group.querySelector('.faqs-group__category')?.textContent.trim();

        if (!currentFilter.category || currentFilter.category === 'Все категории') {
            group.style.display = 'flex';
        } else {
            group.style.display = (groupCategory === currentFilter.category) ? 'flex' : 'none';
        }
    });
}

export async function initFiltersFaq() {
    const optionsData = await fetchFilterOptions();

    const categoryOptions = ['Все категории', ...optionsData.categories];

    initDropdownFilters(
        'filterCategory',
        categoryOptions,
        (selectedValue) => {
            currentFilter.category = selectedValue;
            applyFaqFilters();
        },
        'Все категории',
        true,
        null
    );

    applyFaqFilters();
}

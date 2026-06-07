// js/forms/createTicket.js
import { initDropdownFilters } from '../filters/dropdownFilters.js';
import { fetchFilterOptions } from '../api/api.js';
import { initCreateTicketFormFileUpload } from './fileUpload.js';

export async function initCreateTicketForm() {
    const options = await fetchFilterOptions();
    if (!options) return;

    const categoryDD = initDropdownFilters(
        'ticketCategory',
        options.categories,
        (value) => {
            const categoryInput = document.getElementById('category');
            if (categoryInput) categoryInput.value = value;
        },
        'Выберите категорию'
    );

    const priorityDD = initDropdownFilters(
        'ticketPriority',
        options.priorities,
        (value) => {
            const priorityInput = document.getElementById('priority');
            if (priorityInput) priorityInput.value = value;
        },
        'Выберите приоритет'
    );

    initCreateTicketFormFileUpload();
}
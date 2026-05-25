import { fetchFilterOptions } from "./api.js";
import { initDropdownFilters } from "./dropdownFilters.js";

export async function initEditTicket() {

    const currentCategory = window.currentTicket?.category || null;
    const currentPriority = window.currentTicket?.priority || null;

    const optionsData = await fetchFilterOptions();

    const categoryOptions = [...optionsData.categories];
    const priorityOptions = [...optionsData.priorities];
    initDropdownFilters(
        'filterCategory',
        categoryOptions,
        (newCategory) => {
            if (newCategory === currentCategory) return;
            saveTicketField('category', newCategory);
        },
        'Все категории',
        false,
        currentCategory
    );

    initDropdownFilters(
        'filterPriority',
        priorityOptions,
        (newPriority) => {
            if (newPriority === currentPriority) return;
            saveTicketField('priority', newPriority);
        },
        'Все приоритеты',
        false,
        currentPriority
    );
}

async function saveTicketField(field, value) {
    const ticketId = window.currentTicket?.id;

    if (!ticketId) return;

    try {
        const response = await fetch(`/edit_ticket/${ticketId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ [field]: value })
        });

        if (!response.ok) {
            throw new Error('Ошибка сохранения');
        }
    } catch (error) {
        console.error('Ошибка при сохранении:', error);
    }
}
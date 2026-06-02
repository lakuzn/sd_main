import { initDropdownFilters } from "./dropdownFilters.js";
import { fetchFilterOptions } from "../api/api.js";
import { initFileUpload } from "./fileUpload.js";

export async function initCreateTicketForm() {
    const options = await fetchFilterOptions();

    const categoryDD = initDropdownFilters(
        'ticketCategory',
        options.categories,
        (value) => document.getElementById('category').value = value,
        'Выберите категорию'
    );

    const priorityDD = initDropdownFilters(
        'ticketPriority',
        options.priorities,
        (value) => document.getElementById('priority').value = value,
        'Выберите приоритет'
    );

    initFileUpload();
}
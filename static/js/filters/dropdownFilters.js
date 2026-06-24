// js/filters/dropdownFilters.js
import { createDropdown } from '../common/dropdown.js';

/**
 * Инициализирует дропдаун для фильтров (со стилями filters__dropdown)
 * @param {string} listId - ID контейнера списка
 * @param {Array} options - массив опций (строки)
 * @param {Function} onSelect - колбэк при выборе
 * @param {string} placeholder - текст-заглушка
 * @param {string|null} initialValue - начальное значение
 */
export function initDropdownFilters(listId, options, onSelect, placeholder = 'Выберите...', initialValue = 'Все') {
    const list = document.getElementById(listId);
    if (!list) return null;

    const wrapper = list.parentElement;
    const button = wrapper.querySelector('.filters__dropdown-button');
    if (!button) return null;

    // Подготавливаем опции
    let finalOptions = [initialValue, ...options];

    return createDropdown({
        button: button,
        list: list,
        options: finalOptions,
        placeholder: placeholder,
        initialValue: initialValue,
        onSelect: (value) => {
            if (onSelect) onSelect(value);
        },
        listItemClass: 'filters__dropdown-item',
        closeOnSelect: true
    });
}
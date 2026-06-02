// js/ticket/priorityManager.js
import { createDropdown } from '../common/dropdown.js';

/**
 * Инициализирует дропдаун приоритета
 * @param {Object} config
 * @param {string|HTMLElement} config.buttonId - ID кнопки или элемент
 * @param {string|HTMLElement} config.listId - ID списка или элемент
 * @param {Array} config.priorities - массив приоритетов (строки)
 * @param {string|null} config.initialValue - начальное значение
 * @param {Function} config.onChange - колбэк при выборе (получает выбранную строку)
 * @returns {Object} API дропдауна
 */
export function initPriorityDropdown({ buttonId, listId, priorities, initialValue, onChange }) {
    if (!priorities || priorities.length === 0) {
        console.warn('priorityManager: priorities list is empty');
        return null;
    }

    // Добавляем опцию "Без приоритета", если её нет
    const options = priorities.includes('Без приоритета') 
        ? priorities 
        : ['Без приоритета', ...priorities];

    // Определяем начальное значение: если initialValue есть в списке, используем его, иначе "Без приоритета"
    let initial = initialValue;
    if (!initial || !options.includes(initial)) {
        initial = 'Без приоритета';
    }

    return createDropdown({
        button: buttonId,
        list: listId,
        options: options,
        placeholder: 'Без приоритета',
        initialValue: initial,
        onSelect: (selectedValue) => {
            if (onChange) onChange(selectedValue);
        },
        wrapperClass: 'dropdown',      // класс обёртки
        listItemClass: 'dropdown-item',
        closeOnSelect: true
    });
}

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

    const options = priorities.includes('Без приоритета')
        ? priorities
        : ['Без приоритета', ...priorities];

    let initial = initialValue;
    if (!initial || !options.includes(initial)) {
        initial = 'Без приоритета';
    }

    const button = document.getElementById(buttonId);
    if (!button) return null;

    // Функция обновления классов кнопки
    const updateButtonClass = (priority) => {
        // Удаляем все классы, связанные с приоритетом
        button.classList.remove(
            'ticket__priority--high',
            'ticket__priority--medium',
            'ticket__priority--low',
            'ticket__priority--unselected'
        );
        // Добавляем новые классы
        const newClasses = getPriorityButtonClass(priority).split(/\s+/);
        button.classList.add(...newClasses);
    };

    // Устанавливаем начальный класс
    updateButtonClass(initial);

    const dropdown = createDropdown({
        button: buttonId,
        list: listId,
        options: options,
        placeholder: 'Без приоритета',
        initialValue: initial,
        onSelect: (selectedValue) => {
            updateButtonClass(selectedValue);
            if (onChange) onChange(selectedValue);
        },
        onUpdate: (selectedValue) => {
            updateButtonClass(selectedValue);
        },
        wrapperClass: 'dropdown',
        listItemClass: 'dropdown-item',
        closeOnSelect: true
    });

    // Переопределяем setValue, чтобы обновлять класс при программной установке
    const originalSetValue = dropdown.setValue;
    dropdown.setValue = (val) => {
        originalSetValue(val);
        const currentVal = dropdown.getValue();
        updateButtonClass(currentVal);
    };

    return dropdown;
}

/**
 * Возвращает CSS-класс для кнопки приоритета
 * @param {string} priority
 * @returns {string}
 */
function getPriorityButtonClass(priority) {
    switch (priority) {
        case 'Высокий':
            return 'ticket__priority--high';
        case 'Средний':
            return 'ticket__priority--medium';
        case 'Низкий':
            return 'ticket__priority--low';
        default:
            return 'ticket__priority--unselected';
    }
}
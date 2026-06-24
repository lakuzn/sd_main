// js/ticket/categoriesManager.js
import { createCategoryCheckboxes } from './categoryCheckboxes.js';
import { escapeHtml } from '../common/utils.js';

/**
 * Управляет категориями: чекбоксы + отображение выбранных
 * @param {Object} config
 * @param {string} config.checkboxContainerId - ID контейнера для чекбоксов
 * @param {string|HTMLElement} config.displayContainer - элемент или селектор для отображения выбранных
 * @param {Array} config.categories - массив категорий [{ id, name }]
 * @param {Array} config.initialSelectedIds - начальные выбранные ID
 * @param {Function} config.onChange - колбэк при изменении (получает массив ID)
 * @returns {Object} API { getValue, setValue, reset, getOriginalValue, updateDisplay }
 */
export function initCategoriesManager({
    checkboxContainerId,
    displayContainer,
    categories,
    initialSelectedIds = [],
    onChange
}) {
    // Получаем элемент для отображения
    const displayEl = typeof displayContainer === 'string'
        ? document.querySelector(displayContainer)
        : displayContainer;

    // Функция обновления отображения выбранных категорий
    function updateDisplay(selectedIds) {
        if (!displayEl) return;

        if (!selectedIds.length) {
            displayEl.innerHTML = `
                <div class="categories-item">
                    <p class="categories-item__label">Не указаны</p>
                </div>
            `;
            return;
        }

        displayEl.innerHTML = '';
        selectedIds.forEach(id => {
            const category = categories.find(cat => cat.id === id);
            if (category) {
                const item = document.createElement('div');
                item.setAttribute('id', id);
                item.className = 'categories-item';
                item.innerHTML = `<p class="categories-item__label">${escapeHtml(category.name)}</p>`;
                displayEl.appendChild(item);
            }
        });
    }

    // Создаём чекбоксы
    const checkboxes = createCategoryCheckboxes(
        checkboxContainerId,
        categories,
        initialSelectedIds,
        (newIds) => {
            updateDisplay(newIds);
            if (onChange) onChange(newIds);
        }
    );

    if (!checkboxes) return null;

    // Начальное отображение
    updateDisplay(initialSelectedIds);

    return {
        getValue: () => checkboxes.getValue(),
        setValue: (newIds) => {
            checkboxes.setValue(newIds);
            updateDisplay(newIds);
        },
        reset: () => {
            checkboxes.reset();
            updateDisplay(checkboxes.getValue());
        },
        getOriginalValue: () => checkboxes.getOriginalValue(),
        // Дополнительно: обновить отображение без изменения значений (если нужно)
        updateDisplay: () => updateDisplay(checkboxes.getValue())
    };
}

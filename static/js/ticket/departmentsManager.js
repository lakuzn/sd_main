// js/ticket/departmentsManager.js
import { createCategoryCheckboxes } from './categoryCheckboxes.js';
import { escapeHtml } from '../common/utils.js';

/**
 * Управление отделами: чекбоксы, отображение выбранных, поиск, взаимное исключение с исполнителями
 * @param {Object} config
 * @param {string} config.checkboxContainerId - ID контейнера для чекбоксов отделов
 * @param {string|HTMLElement} config.displayContainer - элемент для отображения выбранных отделов
 * @param {Array} config.departments - массив отделов [{ id, name }]
 * @param {Array} config.initialSelectedIds - начальные выбранные ID
 * @param {Function} config.onChange - колбэк при изменении (получает массив ID)
 * @param {boolean} [config.enableSearch=true] - включать поиск
 * @param {string} [config.searchInputId='deptSearch'] - ID поля поиска
 * @param {Function} [config.onMutualExclusion] - колбэк для сброса исполнителей (вызывается при выборе отдела)
 * @returns {Object} API { getValue, setValue, reset, getOriginalValue, updateDisplay }
 */
export function initDepartmentsManager({
    checkboxContainerId,
    displayContainer,
    departments,
    initialSelectedIds = [],
    onChange,
    enableSearch = true,
    searchInputId = 'deptSearch',
    onMutualExclusion
}) {
    const displayEl = typeof displayContainer === 'string'
        ? document.querySelector(displayContainer)
        : displayContainer;

    if (!displayEl) {
        console.error('departmentsManager: displayContainer not found');
        return null;
    }

    let currentSelected = [...initialSelectedIds];
    const originalSelected = [...initialSelectedIds];

    // Обновление отображения выбранных отделов
    function updateDisplay(selectedIds = currentSelected) {
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
            const dept = departments.find(d => d.id === id);
            if (dept) {
                const item = document.createElement('div');
                item.setAttribute('id', id);
                item.className = 'categories-item';
                item.innerHTML = `<p class="categories-item__label">${escapeHtml(dept.name)}</p>`;
                displayEl.appendChild(item);
            }
        });
    }

    // Создаём чекбоксы отделов (переиспользуем фабрику из categoryCheckboxes.js)
    const checkboxes = createCategoryCheckboxes(
        checkboxContainerId,
        departments,
        currentSelected,
        (newIds) => {
            // Взаимное исключение: если выбран хотя бы один отдел → сбросить исполнителей
            if (newIds.length > 0 && onMutualExclusion) {
                onMutualExclusion();
            }
            currentSelected = newIds;
            updateDisplay(currentSelected);
            if (onChange) onChange([...currentSelected]);
        }
    );

    if (!checkboxes) return null;

    // Поиск по отделам
    function initSearch() {
        if (!enableSearch) return;
        const searchInput = document.getElementById(searchInputId);
        if (!searchInput) return;

        const dropdownItems = document.querySelectorAll(`#${checkboxContainerId} .dropdown-item`);
        searchInput.addEventListener('input', function (e) {
            const term = e.target.value.toLowerCase().trim();
            dropdownItems.forEach(item => {
                const label = item.querySelector('.ticket-category__select');
                if (!label) return;
                const text = label.textContent.toLowerCase();
                item.style.display = (term === '' || text.includes(term)) ? '' : 'none';
            });
        });
    }

    initSearch();
    updateDisplay(initialSelectedIds);

    return {
        getValue: () => checkboxes.getValue(),
        setValue: (newIds) => {
            checkboxes.setValue(newIds);
            currentSelected = newIds;
            updateDisplay(currentSelected);
        },
        reset: () => {
            checkboxes.reset();
            currentSelected = checkboxes.getValue();
            updateDisplay(currentSelected);
        },
        getOriginalValue: () => checkboxes.getOriginalValue(),
        updateDisplay: () => updateDisplay(currentSelected)
    };
}

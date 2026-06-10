// js/ticket/executorsManager.js

import { escapeHtml } from '../common/utils.js';

/**
 * Управление исполнителями: отображение выбранных, выбор из дропдауна, поиск, подсветка
 * @param {Object} config
 * @param {HTMLElement} config.displayContainer - контейнер для отображения выбранных (.ticket-executors)
 * @param {string} config.dropdownListId - ID списка исполнителей в дропдауне (например, 'dropdownTicketExecutorList')
 * @param {Array} config.initialExecutorIds - начальные ID выбранных исполнителей
 * @param {Function} config.onChange - колбэк при изменении (получает массив ID)
 * @param {boolean} [config.enableSearch=true] - включать поиск по исполнителям
 * @param {string} [config.searchInputId='executorSearch'] - ID поля поиска
 * @param {Function} [config.onExecutorDataRequest] - опционально: получить данные исполнителя по ID (если нет в DOM)
 * @returns {Object} API { getValue, setValue, reset, updateDisplay, updateDropdownSelection, getOriginalValue }
 */
export function initExecutorsManager(config) {
    const {
        displayContainer,
        dropdownListId,
        initialExecutorIds = [],
        onChange,
        enableSearch = true,
        searchInputId = 'executorSearch',
        onExecutorDataRequest
    } = config;

    if (!displayContainer) {
        console.error('executorsManager: displayContainer is required');
        return null;
    }

    let selectedExecutors = [...initialExecutorIds];
    const originalExecutors = [...initialExecutorIds];

    // ========== Получение данных исполнителя из DOM ==========
    function getExecutorData(executorId) {
        // Если передан кастомный метод получения данных
        if (onExecutorDataRequest) {
            return onExecutorDataRequest(executorId);
        }

        // Стандартный способ: ищем элемент в дропдауне
        const executorEl = document.querySelector(`#${dropdownListId} .js-executor-item[id="${executorId}"]`);
        if (!executorEl) return null;

        const dropdownItem = executorEl.closest('.dropdown-item');
        if (!dropdownItem) return null;

        const fullName = dropdownItem.querySelector('.ticket-person__label')?.textContent || '';
        const nameParts = fullName.trim().split(/\s+/);
        const initials = (nameParts[0]?.[0] || '') + (nameParts[1]?.[0] || '');

        return {
            id: executorId,
            full_name: fullName,
            initials: initials.toUpperCase()
        };
    }

    // ========== Рендер одного исполнителя ==========
    function renderExecutorItem(executor) {
        return `
            <div id="${executor.id}" class="ticket-person" data-executor-id="${executor.id}">
                <span class="ticket-person__img ticket-person__img--executor">
                    ${executor.initials || '?'}
                </span>
                <p class="ticket-person__label">
                    ${escapeHtml(executor.full_name)}
                </p>
                <button class="remove-executor" data-id="${executor.id}" 
                        style="margin-left: auto; background: none; border: none; cursor: pointer;"
                        aria-label="Удалить исполнителя">✕</button>
            </div>
        `;
    }

    // ========== Обновление отображения выбранных исполнителей ==========
    function updateDisplay() {
        if (!displayContainer) return;

        if (!selectedExecutors.length) {
            displayContainer.innerHTML = '<p class="ticket-person__label">Исполнитель не назначен</p>';
            return;
        }

        displayContainer.innerHTML = '';
        selectedExecutors.forEach(id => {
            const executor = getExecutorData(id);
            if (executor) {
                displayContainer.insertAdjacentHTML('beforeend', renderExecutorItem(executor));
            } else {
                // fallback: показываем заглушку
                displayContainer.insertAdjacentHTML('beforeend', `
                    <div class="ticket-person" data-executor-id="${id}">
                        <span class="ticket-person__img ticket-person__img--executor">?</span>
                        <p class="ticket-person__label">Исполнитель #${id}</p>
                        <button class="remove-executor" data-id="${id}" ...>✕</button>
                    </div>
                `);
            }
        });

        // Навесить обработчики на кнопки удаления
        displayContainer.querySelectorAll('.remove-executor').forEach(btn => {
            btn.removeEventListener('click', handleRemoveExecutor);
            btn.addEventListener('click', handleRemoveExecutor);
        });
    }

    function handleRemoveExecutor(e) {
        e.stopPropagation();
        const id = parseInt(e.currentTarget.dataset.id);
        if (isNaN(id)) return;
        selectedExecutors = selectedExecutors.filter(execId => execId !== id);
        updateDisplay();
        updateDropdownSelection();
        if (onChange) onChange([...selectedExecutors]);
    }

    // ========== Подсветка выбранных в дропдауне ==========
    function updateDropdownSelection() {
        const dropdownItems = document.querySelectorAll(`#${dropdownListId} .dropdown-item`);
        dropdownItems.forEach(item => {
            const person = item.querySelector('.ticket-person');
            if (!person) return;
            const execId = parseInt(item.querySelector('.js-executor-item')?.id);
            if (!isNaN(execId)) {
                if (selectedExecutors.includes(execId)) {
                    person.classList.add('selected');
                } else {
                    person.classList.remove('selected');
                }
            }
        });
    }

    // ========== Поиск по исполнителям ==========
    function initSearch() {
        if (!enableSearch) return;

        const searchInput = document.getElementById(searchInputId);
        if (!searchInput) return;

        const executorItems = document.querySelectorAll(`#${dropdownListId} .js-executor-item`);
        if (!executorItems.length) return;

        searchInput.addEventListener('input', function (e) {
            const searchTerm = e.target.value.toLowerCase().trim();
            executorItems.forEach(item => {
                const label = item.querySelector('.ticket-person__label');
                const userName = label ? label.textContent.toLowerCase() : '';
                const dropdownItem = item.closest('.dropdown-item');
                if (dropdownItem) {
                    dropdownItem.style.display = userName.includes(searchTerm) ? '' : 'none';
                }
            });
        });
    }

    // ========== Обработка кликов по элементам дропдауна ==========
    function initDropdownClickHandlers() {
        const executorItemsList = document.querySelectorAll(`#${dropdownListId} .js-executor-item`);
        executorItemsList.forEach(item => {
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                const execId = parseInt(item.id);
                if (isNaN(execId)) return;

                const index = selectedExecutors.indexOf(execId);
                if (index !== -1) {
                    selectedExecutors.splice(index, 1);
                } else {
                    selectedExecutors.push(execId);
                }

                updateDisplay();
                updateDropdownSelection();
                if (onChange) onChange([...selectedExecutors]);
            });
        });
    }

    // ========== Публичное API ==========
    function getValue() {
        return [...selectedExecutors];
    }

    function setValue(newIds) {
        selectedExecutors = [...newIds];
        updateDisplay();
        updateDropdownSelection();
        if (onChange) onChange([...selectedExecutors]);
    }

    function reset() {
        selectedExecutors = [...originalExecutors];
        updateDisplay();
        updateDropdownSelection();
        if (onChange) onChange([...selectedExecutors]);
    }

    function getOriginalValue() {
        return [...originalExecutors];
    }

    // Инициализация
    function init() {
        updateDisplay();
        updateDropdownSelection();
        initDropdownClickHandlers();
        initSearch();
    }

    init();

    return {
        getValue,
        setValue,
        reset,
        updateDisplay,
        updateDropdownSelection,
        getOriginalValue
    };
}

// js/dashboard/filterExecutor.js
import { createDropdown } from '../common/dropdown.js';
import { filtersState, updateState } from './filtersState.js';
import { escapeHtml } from '../common/utils.js';

export async function initExecutorFilter(applyFilters) {
    const container = document.getElementById('filterExecutor');
    if (!container) return null;

    let executorsList = [];
    try {
        const r = await fetch('/api/dashboard/filter-options');
        if (r.ok) {
            const data = await r.json();
            executorsList = data.executors || [];
        }
    } catch (e) {
        console.error('Ошибка загрузки исполнителей:', e);
    }

    // Создаём кастомный выпадающий список с поиском
    const button = document.getElementById('filterExecutor-button');
    const dropdownContainer = document.getElementById('filterExecutor');
    const searchInput = dropdownContainer?.querySelector('#executorSearchInFilter');

    if (!button || !dropdownContainer) return null;

    let currentExecutorId = '';
    let currentExecutorName = 'Все исполнители';

    // Функция обновления отображения выбранного исполнителя на кнопке
    function updateButtonDisplay(name) {
        button.textContent = name;
        button.classList.toggle('filters__dropdown-button--active', name !== 'Все исполнители');
    }

    // Функция подсветки выбранного элемента в списке
    function updateSelectedInList(selectedId) {
        const items = dropdownContainer.querySelectorAll('.dropdown-item');
        items.forEach(item => {
            const person = item.querySelector('.ticket-person');
            const execId = parseInt(item.querySelector('.js-executor-item')?.id);

            execId === selectedId
                ? person.classList.add('selected')
                : person.classList.remove('selected');
        });
    }

    // Функция рендеринга списка исполнителей
    function renderExecutorList(executors) {
        const listContainer = dropdownContainer.querySelector('.dropdown-list');
        if (!listContainer) return;

        listContainer.innerHTML = '';

        if (!executors.length) {
            listContainer.innerHTML = '<p class="dropdown-header__subtitle">Исполнители не найдены</p>';
            return;
        }

        executors.forEach(executor => {
            const fullName = executor.name;
            const nameParts = fullName.trim().split(/\s+/);
            const initials = (nameParts[0]?.[0] || '') + (nameParts[1]?.[0] || '');
            const department = executor.department;
            const position = executor.position;
            const phone = executor.phone;
            const email = executor.email;

            const item = document.createElement('div');
            item.className = 'dropdown-item';
            item.innerHTML = `
                <div id="${executor.id}" class="ticket-person button js-executor-item">
                    <span class="ticket-person__img ticket-person__img--executor">
                        ${initials.toUpperCase() || '?'}
                    </span>
                    <div class="ticket-person__info">
                        <p class="ticket-person__label">${escapeHtml(fullName)}</p>
                        <p class="ticket-person__post">${escapeHtml(position)}</p>
                        <p class="ticket-person__department icon--16 icon__department--before">${escapeHtml(department)}</p>
                        <p class="ticket-person__phone icon--16 icon__phone--before">${escapeHtml(phone)}</p>
                        <p class="ticket-person__email icon--16 icon__email--before">${escapeHtml(email)}</p>
                    </div>
                </div>
            `;

            item.addEventListener('click', (e) => {
                e.stopPropagation();
                const execId = executor.id;

                if (currentExecutorId === execId) {
                    // Сброс выбора
                    currentExecutorId = '';
                    currentExecutorName = 'Все исполнители';
                    updateButtonDisplay('Все исполнители');
                    updateSelectedInList(null);
                    updateState('executor_id', '');
                } else {
                    // Выбор нового исполнителя
                    currentExecutorId = execId;
                    currentExecutorName = fullName;
                    updateButtonDisplay(fullName);
                    updateSelectedInList(execId);
                    updateState('executor_id', execId);
                }
                applyFilters();
                closeDropdown();
            });

            listContainer.appendChild(item);
        });

        // Восстанавливаем выделение после рендера
        if (currentExecutorId) {
            updateSelectedInList(currentExecutorId);
        }
    }

    // Поиск по исполнителям
    function initSearch() {
        if (!searchInput) return;

        searchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase().trim();
            const items = dropdownContainer.querySelectorAll('.dropdown-item');

            items.forEach(item => {
                const label = item.querySelector('.ticket-person__label');
                const userName = label ? label.textContent.toLowerCase() : '';
                if (searchTerm === '' || userName.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }

    // Управление открытием/закрытием дропдауна
    function openDropdown() {
        document.querySelectorAll('.dropdown').forEach(d => {
            if (d !== dropdownContainer) d.style.display = 'none';
        });
        dropdownContainer.style.display = 'flex';
        button.setAttribute('aria-expanded', 'true');
        // Сбрасываем поиск при открытии
        if (searchInput) {
            searchInput.value = '';
            // Перерисовываем список, чтобы показать всех
            renderExecutorList(executorsList);
        }
    }

    function closeDropdown() {
        dropdownContainer.style.display = 'none';
        button.setAttribute('aria-expanded', 'false');
    }

    function toggleDropdown(e) {
        e.stopPropagation();
        const isOpen = dropdownContainer.style.display === 'flex';
        isOpen ? closeDropdown() : openDropdown();
    }

    button.addEventListener('click', toggleDropdown);
    button.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            toggleDropdown(e);
        }
        if (e.key === 'Escape') closeDropdown();
    });

    document.addEventListener('click', (e) => {
        if (!dropdownContainer.contains(e.target) && e.target !== button) {
            closeDropdown();
        }
    });

    // Инициализация
    updateButtonDisplay('Все исполнители');
    renderExecutorList(executorsList);
    initSearch();

    return {
        getValue: () => currentExecutorId,
        reset: () => {
            if (currentExecutorId !== '') {
                currentExecutorId = '';
                currentExecutorName = 'Все исполнители';
                updateButtonDisplay('Все исполнители');
                updateSelectedInList(null);
                updateState('executor_id', '');
                applyFilters();
            }
        }
    };
}
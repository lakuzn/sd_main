// js/dashboard/filterApplicant.js
import { escapeHtml } from '../common/utils.js';
import { filtersState, updateState } from './filtersState.js';

export async function initApplicantFilter(applyFilters) {
    const container = document.getElementById('filterApplicant');
    if (!container) return null;

    let applicantsList = [];
    try {
        const r = await fetch('/api/users/all');
        if (r.ok) {
            const data = await r.json();
            applicantsList = data || [];
        }
    } catch (e) {
        console.error('Ошибка загрузки заявителей:', e);
    }

    const button = document.getElementById('filterApplicant');
    const dropdownContainer = document.getElementById('filterApplicantList');
    const searchInput = dropdownContainer?.querySelector('#applicantSearchInFilter');

    if (!button || !dropdownContainer) return null;

    let currentApplicantId = '';
    let currentApplicantName = 'Все заявители';

    // Функция обновления отображения выбранного заявителя на кнопке
    function updateButtonDisplay(name) {
        button.textContent = name;
        button.classList.toggle('filters__dropdown-button--active', name !== 'Все заявители');
    }

    // Функция подсветки выбранного элемента в списке
    function updateSelectedInList(selectedId) {
        const items = dropdownContainer.querySelectorAll('.dropdown-item');
        items.forEach(item => {
            const person = item.querySelector('.ticket-person');
            const applicantId = parseInt(item.querySelector('.ticket-person')?.id);

            applicantId === selectedId
                ? person.classList.add('selected')
                : person.classList.remove('selected');
        });
    }

    // Функция рендеринга списка заявителей
    function renderApplicantList(applicants) {
        const listContainer = dropdownContainer.querySelector('.dropdown-list');
        if (!listContainer) return;

        listContainer.innerHTML = '';

        if (!applicants.length) {
            listContainer.innerHTML = '<p class="dropdown-header__subtitle">Заявители не найдены</p>';
            return;
        }

        applicants.forEach(applicant => {
            const fullName = applicant.full_name;
            const nameParts = fullName.trim().split(/\s+/);
            const initials = (nameParts[0]?.[0] || '') + (nameParts[1]?.[0] || '');
            const department = applicant.department;
            const position = applicant.position;
            const phone = applicant.phone;
            const email = applicant.email;

            const item = document.createElement('div');
            item.className = 'dropdown-item';
            item.innerHTML = `
                <div id="${applicant.id}" class="ticket-person button">
                    <span class="ticket-person__img ticket-person__img--sender">
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
                const applicantId = applicant.id;
                const applicantName = fullName;

                if (currentApplicantId === applicantId) {
                    // Сброс выбора
                    currentApplicantId = '';
                    currentApplicantName = 'Все заявители';
                    updateButtonDisplay('Все заявители');
                    updateSelectedInList(null);
                    updateState('applicant_id', '');
                } else {
                    // Выбор нового заявителя
                    currentApplicantId = applicantId;
                    currentApplicantName = applicantName;
                    updateButtonDisplay(applicantName);
                    updateSelectedInList(applicantId);
                    updateState('applicant_id', applicantId);
                }
                applyFilters();
                closeDropdown();
            });

            listContainer.appendChild(item);
        });

        // Восстанавливаем выделение после рендера
        if (currentApplicantId) {
            updateSelectedInList(currentApplicantId);
        }
    }

    // Поиск по заявителям
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
            renderApplicantList(applicantsList);
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
    updateButtonDisplay('Все заявители');
    renderApplicantList(applicantsList);
    initSearch();

    return {
        getValue: () => currentApplicantId,
        reset: () => {
            if (currentApplicantId !== '') {
                currentApplicantId = '';
                currentApplicantName = 'Все заявители';
                updateButtonDisplay('Все заявители');
                updateSelectedInList(null);
                updateState('applicant_id', '');
                applyFilters();
            }
        }
    };
}
// js/dashboard/filterApplicant.js
import { escapeHtml } from '../common/utils.js';
import { filtersState, updateState } from './filtersState.js';

export function initApplicantFilter(applyFilters) {
    const input = document.getElementById('filterApplicant');
    const listWrap = document.getElementById('filterApplicantList');
    if (!input || !listWrap) return;

    const list = listWrap.querySelector('.dropdown-list');
    let timer = null;

    function renderUsers(users) {
        list.innerHTML = '';
        if (!users.length) {
            list.innerHTML = '<p class="dropdown-header__subtitle">Ничего не найдено</p>';
            listWrap.style.display = 'flex';
            return;
        }
        users.forEach((u) => {
            const item = document.createElement('div');
            item.className = 'dropdown-item';
            item.innerHTML = `
                <div class="ticket-person button">
                    <div class="ticket-person__info">
                        <p class="ticket-person__label">${escapeHtml(u.full_name)}</p>
                        <p class="ticket-person__post">${escapeHtml(u.position || '')}</p>
                        <p class="ticket-person__department icon--16 icon__department--before">${escapeHtml(u.department || '')}</p>
                    </div>
                </div>
            `;
            item.addEventListener('click', () => {
                updateState('applicant_id', u.id);
                input.value = u.full_name;
                listWrap.style.display = 'none';
                applyFilters();
            });
            list.appendChild(item);
        });
        listWrap.style.display = 'flex';
    }

    input.addEventListener('input', () => {
        clearTimeout(timer);
        const term = input.value.trim();

        if (filtersState.applicant_id) {
            updateState('applicant_id', '');
            applyFilters();
        }

        if (!term) {
            listWrap.style.display = 'none';
            list.innerHTML = '';
            return;
        }

        timer = setTimeout(() => {
            fetch('/api/users/search?q=' + encodeURIComponent(term))
                .then(r => r.json())
                .then(renderUsers)
                .catch(() => { });
        }, 250);
    });

    document.addEventListener('click', (e) => {
        if (!listWrap.contains(e.target) && e.target !== input) {
            listWrap.style.display = 'none';
        }
    });
}
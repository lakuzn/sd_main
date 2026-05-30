import { fetchReadNotifications } from "./api.js";

export function initDropdownNotification() {
    const button = document.querySelector('.notifications-button');
    const dropdownMenu = document.querySelector('.notifications-dropdown');
    const readAllButton = document.querySelector('.dropdown-header__button');

    if (!button || !dropdownMenu) return;

    dropdownMenu.style.display = 'none';
    button.setAttribute('aria-expanded', 'false');
    button.setAttribute('aria-haspopup', 'true');
    dropdownMenu.setAttribute('aria-label', 'Уведомления');

    document.querySelectorAll('.dropdown-item').forEach((item) =>
        item.setAttribute('role', 'menuitem'));

    function toggleDropdown(event) {
        event.stopPropagation();
        const isOpen = dropdownMenu.style.display === 'flex';
        isOpen ? closeDropdown() : openDropdown();
    }

    function openDropdown() {
        document.querySelectorAll('.dropdown').forEach(d => {
            if (d !== dropdownMenu) d.style.display = 'none';
        });

        dropdownMenu.style.display = 'flex';
        button.setAttribute('aria-expanded', 'true');
    }

    function closeDropdown() {
        dropdownMenu.style.display = 'none';
        button.setAttribute('aria-expanded', 'false');
    }

    button.addEventListener('click', toggleDropdown);

    button.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === '') {
            e.preventDefault();
            toggleDropdown(e);
        }
        if (e.key === 'Escape') closeDropdown();
    });

    document.addEventListener('click', function (e) {
        if (!dropdownMenu.contains(e.target) && !button.contains(e.target))
            closeDropdown();
    });

    // Клик по отдельному уведомлению — прочитать + скрыть + уменьшить бейдж
    const badge = document.querySelector('.notifications__button-badge');

    dropdownMenu.querySelectorAll('.dropdown-item__content').forEach(item => {
        item.addEventListener('click', async (e) => {
            const notifId = item.dataset.notifId;
            if (!notifId || item.classList.contains('_read')) return;

            // Помечаем как прочитанное на бэкенде
            try {
                await fetch(`/api/notifications/${notifId}/read`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': document.querySelector('meta[name="csrf_token"]')?.getAttribute('content') || ''
                    }
                });
            } catch (err) {
                console.error('Ошибка отметки уведомления:', err);
            }

            item.classList.add('_read');
            item.classList.remove('dropdown-item__content--unchecked');

            // Скрываем элемент списка
            const listItem = item.closest('.dropdown-item');
            if (listItem) listItem.style.display = 'none';

            // Уменьшаем счётчик
            if (badge) {
                const current = parseInt(badge.textContent || '0');
                const newVal = Math.max(0, current - 1);
                badge.textContent = newVal;
                badge.style.display = newVal > 0 ? 'flex' : 'none';
            }
        });
    });

    // Кнопка "Прочитать все"
    if (readAllButton) {
        const unreadItems = dropdownMenu.querySelectorAll('.dropdown-item__content--unchecked');

        readAllButton.addEventListener('click', () => {
            fetchReadNotifications(readAllButton, badge, unreadItems);
            closeDropdown();
        });
    }

    // Подключаемся к персональной комнате для получения уведомлений в реальном времени
    if (typeof io !== 'undefined' && window.currentUserId) {
        const notifSocket = io();
        notifSocket.on('connect', () => {
            notifSocket.emit('join_user_room');
        });

        notifSocket.on('new_notification', (data) => {
            addNotificationToDropdown(data, badge, dropdownMenu);
        });
    }
}

function addNotificationToDropdown(notif, badge, dropdownMenu) {
    const list = dropdownMenu.querySelector('.dropdown-list');
    if (!list) return;

    // Убираем заглушку "Нет уведомлений"
    const empty = list.querySelector('.dropdown-item p');
    if (empty && !empty.closest('a')) {
        empty.closest('.dropdown-item')?.remove();
    }

    const ticketUrl = notif.ticket_id ? `/ticket/${notif.ticket_id}` : '#';

    const li = document.createElement('li');
    li.className = 'dropdown-item';
    li.setAttribute('role', 'menuitem');
    li.innerHTML = `
        <a href="${ticketUrl}"
            data-notif-id="${notif.id}"
            class="button dropdown-item__content dropdown-item__content--unchecked">
            <p class="dropdown-item__title">
                ${notif.ticket_id ? `По заявке №${notif.ticket_id}` : 'Системное уведомление'}
            </p>
            <p class="dropdown-item__description">${notif.message}</p>
            <time class="dropdown-item__time">${notif.created_at}</time>
        </a>`;

    list.prepend(li);

    // Вешаем обработчик на новый элемент
    const contentEl = li.querySelector('.dropdown-item__content');
    contentEl.addEventListener('click', async () => {
        if (contentEl.classList.contains('_read')) return;
        try {
            await fetch(`/api/notifications/${notif.id}/read`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('meta[name="csrf_token"]')?.getAttribute('content') || ''
                }
            });
        } catch (err) { /* ignore */ }
        contentEl.classList.add('_read');
        contentEl.classList.remove('dropdown-item__content--unchecked');
        li.style.display = 'none';

        if (badge) {
            const current = parseInt(badge.textContent || '0');
            const newVal = Math.max(0, current - 1);
            badge.textContent = newVal;
            badge.style.display = newVal > 0 ? 'flex' : 'none';
        }
    });

    // Обновляем бейдж
    if (badge) {
        const current = parseInt(badge.textContent || '0');
        badge.textContent = current + 1;
        badge.style.display = 'flex';
    }
}

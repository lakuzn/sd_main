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

    const badge = document.querySelector('.notifications__button-badge');

    function getCSRF() {
        return document.querySelector('meta[name="csrf_token"]')?.getAttribute('content') || '';
    }

    function decreaseBadge() {
        if (!badge) return;
        const current = parseInt(badge.textContent || '0');
        const newVal = Math.max(0, current - 1);
        badge.textContent = newVal;
        badge.style.display = newVal > 0 ? 'flex' : 'none';
    }

    // Клик по уведомлению: помечаем прочитанным, скрываем, уменьшаем счётчик,
    // и только потом переходим на заявку
    function attachItemHandler(contentEl) {
        contentEl.addEventListener('click', async (e) => {
            if (contentEl.dataset.read === '1') return;

            const notifId = contentEl.dataset.notifId;
            const href = contentEl.getAttribute('href');
            const isUnread = contentEl.classList.contains('dropdown-item__content--unchecked');

            // Прерываем мгновенный переход, чтобы успеть отметить прочтение
            if (notifId && isUnread) {
                e.preventDefault();

                try {
                    await fetch(`/api/notifications/${notifId}/read`, {
                        method: 'POST',
                        headers: { 'X-CSRFToken': getCSRF() }
                    });
                } catch (err) {
                    console.error('Ошибка отметки уведомления:', err);
                }

                contentEl.dataset.read = '1';
                contentEl.classList.remove('dropdown-item__content--unchecked');

                const listItem = contentEl.closest('.dropdown-item');
                if (listItem) listItem.style.display = 'none';

                decreaseBadge();

                // Переходим на заявку (если ссылка валидная)
                if (href && href !== '#') {
                    window.location.href = href;
                }
            }
        });
    }

    dropdownMenu.querySelectorAll('.dropdown-item__content').forEach(attachItemHandler);

    if (readAllButton) {
        const unreadItems = dropdownMenu.querySelectorAll('.dropdown-item__content--unchecked');

        readAllButton.addEventListener('click', () => {
            fetchReadNotifications(readAllButton, badge, unreadItems);
            closeDropdown();
        });
    }

    // Реальное время: получаем уведомления через socket без перезагрузки
    if (typeof io !== 'undefined' && window.currentUserId) {
        const notifSocket = io();
        notifSocket.on('connect', () => {
            notifSocket.emit('join_user_room');
        });

        notifSocket.on('new_notification', (data) => {
            addNotificationToDropdown(data);
        });
    }

    function addNotificationToDropdown(notif) {
        const list = dropdownMenu.querySelector('.dropdown-list');
        if (!list) return;

        // Убираем заглушку "Нет новых уведомлений"
        const placeholder = Array.from(list.querySelectorAll('.dropdown-item')).find(
            li => !li.querySelector('a') && li.textContent.includes('Нет новых')
        );
        if (placeholder) placeholder.remove();

        const ticketUrl = notif.ticket_id ? `/tickets/${notif.ticket_id}` : '#';

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

        attachItemHandler(li.querySelector('.dropdown-item__content'));

        if (badge) {
            const current = parseInt(badge.textContent || '0');
            badge.textContent = current + 1;
            badge.style.display = 'flex';
        }
    }
}

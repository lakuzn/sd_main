// js/notifications/dropdownNotification.js
import { getCSRFToken, escapeHtml } from '../common/utils.js';
import { initDropdownToggle } from '../common/dropdown.js';
import { fetchReadNotifications } from '../api/api.js';
import { initDesktopNotifications, showDesktopNotification } from './desktopNotifications.js';

export function initDropdownNotification() {
    const button = document.getElementById('dropdownNotificationsButton');
    const dropdownMenu = document.getElementById('dropdownNotificationsList');

    if (!button || !dropdownMenu) return;

    // Разрешение на десктоп-уведомления (Центр уведомлений Windows)
    initDesktopNotifications();

    // Используем универсальный дропдаун
    const dropdown = initDropdownToggle('dropdownNotificationsButton', 'dropdownNotificationsList');
    // Если нужен доступ к методам open/close, то они есть в возвращаемом объекте

    // Настройка ARIA-атрибутов
    button.setAttribute('aria-haspopup', 'true');
    dropdownMenu.setAttribute('aria-label', 'Уведомления');

    document.querySelectorAll('.dropdown-item').forEach((item) =>
        item.setAttribute('role', 'menuitem'));

    const badge = document.querySelector('.notifications__button-badge');

    function decreaseBadge() {
        if (!badge) return;
        const current = parseInt(badge.textContent || '0');
        const newVal = Math.max(0, current - 1);
        badge.textContent = newVal;
        badge.style.display = newVal > 0 ? 'flex' : 'none';
    }

    // Клик по уведомлению
    function attachItemHandler(contentEl) {
        contentEl.addEventListener('click', async (e) => {
            if (contentEl.dataset.read === '1') return;

            const notifId = contentEl.dataset.notifId;
            const href = contentEl.getAttribute('href');
            const isUnread = contentEl.classList.contains('dropdown-item__content--unchecked');

            if (notifId && isUnread) {
                e.preventDefault();

                try {
                    await fetch(`/api/notifications/${notifId}/read`, {
                        method: 'POST',
                        headers: { 'X-CSRFToken': getCSRFToken() }
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

    const readAllButton = document.querySelector('.dropdown-header__button');
    if (readAllButton) {
        const unreadItems = dropdownMenu.querySelectorAll('.dropdown-item__content--unchecked');
        readAllButton.addEventListener('click', () => {
            fetchReadNotifications(readAllButton, badge, unreadItems);
            dropdown?.close?.(); // закрыть дропдаун после нажатия
        });
    }

    // Socket для реального времени
    if (typeof io !== 'undefined' && window.currentUserId) {
        const notifSocket = io();
        notifSocket.on('connect', () => {
            notifSocket.emit('join_user_room');
        });

        notifSocket.on('new_notification', (data) => {
            addNotificationToDropdown(data);
            // Важные уведомления дублируем на рабочий стол (Windows/браузер)
            showDesktopNotification(data);
        });
    }

    function addNotificationToDropdown(notif) {
        const list = dropdownMenu.querySelector('.dropdown-list');
        if (!list) return;

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
                <p class="dropdown-item__description">${escapeHtml(notif.message)}</p>
                <time class="dropdown-item__time">${escapeHtml(notif.created_at)}</time>
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
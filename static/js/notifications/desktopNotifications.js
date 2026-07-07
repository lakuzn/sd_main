// js/notifications/desktopNotifications.js
//
// Десктоп-уведомления через стандартный Web Notifications API браузера.
// В Chrome/Edge такие уведомления показываются системным «Центром уведомлений»
// Windows — то есть важные события ServiceDesk доходят до пользователя, даже
// если вкладка свёрнута или скрыта. Ничего устанавливать на клиент не нужно,
// интернет не требуется — всё работает во внутренней сети.

let permissionRequested = false;

/**
 * Один раз аккуратно запрашивает у пользователя разрешение на уведомления.
 * Если пользователь уже разрешил или запретил — повторно не беспокоим.
 */
export function initDesktopNotifications() {
    if (!('Notification' in window)) return; // браузер не поддерживает

    if (Notification.permission === 'default' && !permissionRequested) {
        permissionRequested = true;
        try {
            Notification.requestPermission().catch(() => { });
        } catch (e) {
            // Старые браузеры используют колбэк-версию — не критично, пропускаем
        }
    }
}

/**
 * Показывает системное уведомление для ВАЖНОГО события (notif.important).
 * Обычные уведомления на рабочий стол не выводим, чтобы не спамить.
 * @param {Object} notif - данные уведомления из сокета (то же, что to_dict)
 */
export function showDesktopNotification(notif) {
    if (!('Notification' in window)) return;
    if (Notification.permission !== 'granted') return;
    if (!notif || !notif.important) return;

    const title = notif.ticket_id ? `Заявка №${notif.ticket_id}` : 'ServiceDesk';
    const options = {
        body: notif.message || '',
        // tag не даёт задвоить одно и то же уведомление при переподключении сокета
        tag: `sd-notif-${notif.id}`,
    };

    try {
        const notification = new Notification(title, options);
        notification.onclick = () => {
            window.focus();
            if (notif.ticket_id) {
                window.location.href = `/tickets/${notif.ticket_id}`;
            }
            notification.close();
        };
    } catch (e) {
        // Некоторые сборки браузеров требуют Service Worker для уведомлений —
        // молча игнорируем: уведомление внутри приложения всё равно показано.
    }
}

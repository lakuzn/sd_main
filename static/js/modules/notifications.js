// document.addEventListener("DOMContentLoaded", function () {
//     const bellIcon = document.getElementById('bell-icon');
//     const dropdown = document.getElementById('notif-dropdown');
    
//     // Открытие/закрытие меню по клику
//     bellIcon.addEventListener('click', () => {
//         dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
//     });

//     // Загружаем уведомления при старте
//     fetchNotifications();
//     // Если подключен SocketIO - слушаем новые уведомления в реальном времени!
//     if (typeof io !== 'undefined') {
//         const socket = io();
//         // При подключении, говорим бэкенду закинуть нас в персональную комнату
//         socket.emit('join_user_room', { user_id: "{{ current_user.id }}" }); 

//         socket.on('new_notification', function(data) {
//             // Добавляем уведомление в список и увеличиваем счетчик без перезагрузки
//             addNotificationToUI(data);
//             updateBadgeCount(1);
//         });
//     }
// });

// async function fetchNotifications() {
//     try {
//         const res = await fetch('/api/notifications');
//         const notifications = await res.json();
        
//         const list = document.getElementById('notif-list');
//         list.innerHTML = ''; // Очищаем
        
//         if (notifications.length === 0) {
//             list.innerHTML = '<div style="padding: 15px; text-align: center; color: #888; font-size: 0.9em;">Нет новых уведомлений</div>';
//             updateBadgeCount(0, true);
//             return;
//         }

// updateBadgeCount(notifications.length, true);
//         notifications.forEach(notif => addNotificationToUI(notif, false));

//     } catch (e) {
//         console.error("Ошибка загрузки уведомлений", e);
//     }
// }

// function addNotificationToUI(notif, prepend=true) {
//     const list = document.getElementById('notif-list');
//     // Убираем заглушку "Нет уведомлений" если она там есть
//     if (list.innerHTML.includes("Нет новых уведомлений")) list.innerHTML = '';

//     const item = 
// document.createElement('div');
//     item.id = `notif-${notif.id}`;
//     item.style.cssText = "padding: 12px; border-bottom: 1px solid #eee; font-size: 0.9em; cursor: pointer; transition: background 0.2s;";
//     item.onmouseover = () => item.style.background = "#f8f9fa";
//     item.onmouseout = () => item.style.background = "white";
    
//     // При клике: переходим к заявке и помечаем прочитанным
//     item.onclick = async () => {
//         await fetch(`/api/notifications/${notif.id}/read`, { method: 'POST' });
//         window.location.href = `/tickets/ticket/${notif.ticket_id}`;
//     };

//     item.innerHTML = `
//         <div style="color: #212529; margin-bottom: 4px;">${notif.message}</div>
//         <div style="color: #6c757d; font-size: 0.8em;">${notif.created_at}</div>
//     `;

//     if (prepend) list.prepend(item);
//     else list.appendChild(item);
// }

// function updateBadgeCount(count, absolute=false) {
//     const badge = document.getElementById('notif-badge');
//     let current = parseInt(badge.innerText || "0");
//     let newVal = absolute ? count : current + count;
    
//     badge.innerText = newVal;
//     badge.style.display = newVal > 0 ? 'inline-block' : 'none';
// }

// async function markAllAsRead() {
//     await fetch('/api/notifications/read-all', { method: 'POST' });
//     fetchNotifications(); // Перезагружаем интерфейс
// }

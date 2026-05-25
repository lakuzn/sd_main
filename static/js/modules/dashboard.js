let socket = null;

export function initSocketDashboardTickets() {
    socket = io();

    socket.on('connect', () => {
        socket.emit('join_dashboard');
    });

    // Обработка новых заявок
    socket.on('ticket_created', (data) => {
        var ticket = data.ticket;

        if (isRelevantForCurrentDashboard(ticket))
            addTicketCard(ticket);

        // showNotification('Новая заявка #' + ticket.id, 'info');
    });

    // Обработка обновлений заявок
    socket.on('ticket_updated', function (data) {
        var ticket = data.ticket;
        var oldStatus = data.changed_fields.old_status;
        updateOrRemoveTicketCard(ticket, oldStatus);
    });

    // Функция определения релевантности для текущего дашборда
    function isRelevantForCurrentDashboard(ticket) {
        const userId = window.currentUserId;
        const role = window.currentUserRole;

        if (role === 'user')
            return ticket.applicant_id === userId && ticket.status !== 'Решена';

        if (role === 'executor')
            return ticket.executor_ids.includes(userId) &&
                ['В работе', 'Ожидает ответа'].includes(ticket.status);

        if (role === 'classifier')
            return ['Новая', 'В обработке'].includes(ticket.status);

        if (role === 'admin')
            return ticket.status !== 'Решена';

        return false;
    }

    async function addTicketCard(ticket) {
        try {
            const response = await fetch(`/tickets/card/${ticket.id}`);
            const data = await response.json();

            const container = document.querySelector('.content__cards');

            if (container)
                container.insertAdjacentHTML('afterbegin', data.html);
        } catch (e) {
            return e;
        }
    }
}

function updateOrRemoveTicketCard(ticket, oldStatus) {
    var card = document.querySelector(`.card[data-ticket-id="${ticket.id}"]`);
    var shouldBeVisible = isRelevantForCurrentDashboard(ticket);
    if (card) {
        if (!shouldBeVisible) {
            card.remove();
            showNotification(`Заявка #${ticket.id} перемещена`, 'warning');
        } else {
            // обновляем содержимое карточки
            card.querySelector('.card__status').innerText = ticket.status;
            // ... обновить другие поля
        }
    } else if (shouldBeVisible) {
        addTicketCard(ticket);
        showNotification(`Заявка #${ticket.id} появилась на дашборде`, 'info');
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>]/g, function (m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}

function showNotification(message, type) {
    // Ваша реализация тоста или уведомления
    console.log(message, type);
}
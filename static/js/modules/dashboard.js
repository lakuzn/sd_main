let socket = null;

export function initSocketDashboardTickets() {
    socket = io();

    socket.on('connect', () => {
        socket.emit('join_dashboard');
    });

    socket.on('ticket_created', (data) => {
        var ticket = data.ticket;

        if (isRelevantForCurrentDashboard(ticket))
            addTicketCard(ticket);
    });

    socket.on('ticket_updated', function (data) {
        var ticket = data.ticket;
        var changedFields = data.changed_fields || {};
        var oldStatus = changedFields.old_status;

        updateOrRemoveTicketCard(ticket, oldStatus);

        // Индикатор нового сообщения на карточке
        if (changedFields.new_message) {
            markCardHasNewMessage(ticket.id);
        }
    });
}

function isRelevantForCurrentDashboard(ticket) {
    const userId = Number(window.currentUserId);
    const role = window.currentUserRole;

    if (role === 'user')
        return ticket.applicant_id === userId && ticket.status !== 'Решена';

    if (role === 'executor')
        return Array.isArray(ticket.executor_ids) &&
            ticket.executor_ids.includes(userId) &&
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

function updateOrRemoveTicketCard(ticket, oldStatus) {
    var card = document.querySelector(`[id="ticket-card-${ticket.id}"]`);
    var shouldBeVisible = isRelevantForCurrentDashboard(ticket);
    if (card) {
        if (!shouldBeVisible) {
            card.remove();
        } else {
            const statusEl = card.querySelector('.ticket__status');
            if (statusEl) statusEl.textContent = ticket.status;
        }
    } else if (shouldBeVisible) {
        addTicketCard(ticket);
    }
}

function markCardHasNewMessage(ticketId) {
    const card = document.querySelector(`[id="ticket-card-${ticketId}"]`);
    if (!card) return;

    let badge = card.querySelector('.card__new-message');
    if (!badge) {
        badge = document.createElement('span');
        badge.className = 'card__new-message';
        badge.title = 'Есть новые сообщения';

        const header = card.querySelector('.card__header');
        if (header) header.appendChild(badge);
    }
    badge.style.display = 'inline-block';
}

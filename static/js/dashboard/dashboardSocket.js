// js/dashboard/dashboardSocket.js
let socket = null;

export function initSocketDashboard() {
    socket = io();

    socket.on('connect', () => {
        socket.emit('join_dashboard');
    });

    socket.on('ticket_created', (data) => {
        const ticket = data.ticket;
        if (isRelevantForCurrentDashboard(ticket)) {
            addTicketCard(ticket);
        }
    });

    socket.on('ticket_updated', (data) => {
        const ticket = data.ticket;
        const changedFields = data.changed_fields || {};
        const oldStatus = changedFields.old_status;

        updateOrRemoveTicketCard(ticket, oldStatus);

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

    if (role === 'executor') {
        const deptId = window.currentUserDepartmentId;
        return ticket.status !== 'Решена' && (
            (deptId && Array.isArray(ticket.department_ids) && ticket.department_ids.includes(deptId)) ||
            (Array.isArray(ticket.executor_ids) && ticket.executor_ids.includes(userId))
        );
    }

    if (role === 'classifier') {
        const deptId = window.currentUserDepartmentId;
        return ticket.status !== 'Решена' && (
            (deptId && Array.isArray(ticket.department_ids) && ticket.department_ids.includes(deptId)) ||
            (Array.isArray(ticket.department_ids) && ticket.department_ids.length === 0) ||
            (Array.isArray(ticket.executor_ids) && ticket.executor_ids.includes(userId))
        );
    }

    if (role === 'head') {
        const deptId = window.currentUserDepartmentId;
        return ticket.status !== 'Решена' && (
            (deptId && Array.isArray(ticket.department_ids) && ticket.department_ids.includes(deptId)) ||
            (Array.isArray(ticket.executor_ids) && ticket.executor_ids.includes(userId))
        );
    }

    if (role === 'admin')
        return ticket.status !== 'Решена';

    return false;
}

async function addTicketCard(ticket) {
    if (document.querySelector(`[id="ticket-card-${ticket.id}"]`)) return;

    try {
        const response = await fetch(`/tickets/card/${ticket.id}`);
        const data = await response.json();

        const container = document.querySelector('.content__cards');
        if (container) {
            container.insertAdjacentHTML('afterbegin', data.html);
            reorderCards();
        }
    } catch (e) {
        console.error('Ошибка добавления карточки:', e);
    }
}

function updateOrRemoveTicketCard(ticket, oldStatus) {
    const card = document.querySelector(`[id="ticket-card-${ticket.id}"]`);
    const shouldBeVisible = isRelevantForCurrentDashboard(ticket);

    if (card) {
        if (!shouldBeVisible) {
            card.remove();
        } else {
            const statusEl = card.querySelector('.ticket__status');
            if (statusEl) statusEl.textContent = ticket.status;

            const cardLink = card.querySelector('.content__card');
            if (cardLink) {
                cardLink.classList.toggle('content__card--review', ticket.status === 'Требует проверки');
            }
            reorderCards();
        }
    } else if (shouldBeVisible) {
        addTicketCard(ticket);
    }
}

function reorderCards() {
    const container = document.querySelector('.content__cards');
    if (!container) return;

    const items = Array.from(container.querySelectorAll('.content__card-item'));
    items
        .filter(item => item.querySelector('.content__card--overdue'))
        .reverse()
        .forEach(item => container.insertBefore(item, container.firstChild));
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
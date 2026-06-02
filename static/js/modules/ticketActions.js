import { fetchChangeTicketStatus, fetchCloneTicket, fetchDeleteTicket } from "../api/api.js";
import { initComments } from "../chat/chat.js";

export function initTicketActions() {
    const reopenCardButtons = document.querySelectorAll('.js-reopen-card-btn');
    reopenCardButtons.forEach(button => {
        button.addEventListener('click', () => {
            const ticketId = button.dataset.ticketId;
            showConfirmModal({
                title: 'Создать похожую?',
                message: 'Будет создана новая заявка с сохранением описания и категорий.',
                confirmText: 'Да, создать заявку',
                cancelText: 'Отмена',
                onConfirm: async () => {
                    const result = await fetchCloneTicket(ticketId, button);
                    if (result && result.ticket_id) {
                        // Переходим на дашборд, где появится новая заявка
                        window.location.href = '/';
                    }
                }
            });
        });
    });

    const buttonResolved = document.getElementById('buttonResolved');
    const buttonUnResolved = document.getElementById('buttonUnResolved');

    if (buttonResolved) {
        buttonResolved.addEventListener('click', () => {
            showConfirmModal({
                title: 'Закрыть заявку?',
                message: 'После закрытия заявка перейдет в статус "Решена".',
                confirmText: 'Да, закрыть заявку',
                cancelText: 'Отмена',
                onConfirm: async () => {
                    const newStatus = await fetchChangeTicketStatus('Решена', buttonResolved);
                    if (newStatus == 'Решена') {
                        setResolvedMode();
                    }
                }
            });
        });
    }

    if (buttonUnResolved) {
        buttonUnResolved.addEventListener('click', () => {
            const ticketId = window.currentTicket?.id;
            showConfirmModal({
                title: 'Создать похожую?',
                message: 'Будет создана новая заявка с сохранением описания и категорий.',
                confirmText: 'Да, создать заявку',
                cancelText: 'Отмена',
                onConfirm: async () => {
                    const result = await fetchCloneTicket(ticketId, buttonUnResolved);
                    if (result && result.ticket_id) {
                        // Переходим на дашборд
                        window.location.href = '/';
                    }
                }
            });
        });
    }

    const buttonDeleteTicket = document.getElementById('buttonDeleteTicket');
    if (buttonDeleteTicket) {
        const modal = document.getElementById('modalDeleteTicket');

        buttonDeleteTicket.addEventListener('click', () => {
            if (modal) modal.style.display = 'flex';
        });

        if (modal) {
            const overlay = modal.querySelector('.modal__overlay');
            const cancelBtn = modal.querySelector('.modal__cancel');
            const closeBtn = modal.querySelector('.modal__close');
            const confirmBtn = modal.querySelector('.modal__confirm');

            const closeModal = () => modal.style.display = 'none';

            if (overlay) overlay.addEventListener('click', closeModal);
            if (cancelBtn) cancelBtn.addEventListener('click', closeModal);
            if (closeBtn) closeBtn.addEventListener('click', closeModal);

            if (confirmBtn) {
                confirmBtn.addEventListener('click', async () => {
                    const ticketId = window.currentTicket?.id;
                    const result = await fetchDeleteTicket(ticketId, confirmBtn);
                    if (result && result.status === 'success') {
                        window.location.href = '/';
                    } else {
                        closeModal();
                    }
                });
            }
        }
    }

    const ticketId = window.currentTicket?.id || 1;
    if (!ticketId) return;

    const buttonInvite = document.getElementById('buttonInvite');
    if (buttonInvite)
        buttonInvite.addEventListener('click', () => {
            showInviteModal(ticketId);
        });

    const buttonAddComment = document.getElementById('buttonAddComment');
    if (buttonAddComment)
        buttonAddComment.addEventListener('click', () => {
            showAddCommentModal(ticketId);
        });

    const buttonSeeComments = document.getElementById('buttonSeeComments');
    if (buttonSeeComments)
        buttonSeeComments.addEventListener('click', () => {
            showAddCommentModal(ticketId);
        });
}

export function initTicketInterface() {
    const currentStatus = window.currentTicket?.status;
    currentStatus === 'Решена' ? setResolvedMode() : setActiveMode();
}

export function setResolvedMode() {
    const resolveBlock = document.getElementById('resolve-block');
    const resolvedBanner = document.getElementById('resolved-banner');
    const chatForm = document.getElementById('chat-form')

    if (resolveBlock) resolveBlock.style.display = 'none';
    if (resolvedBanner) resolvedBanner.style.display = 'block';
    if (chatForm) chatForm.style.display = 'none';
}

export function setActiveMode() {
    const resolveBlock = document.getElementById('resolve-block');
    const resolvedBanner = document.getElementById('resolved-banner');
    const chatForm = document.getElementById('chat-form')

    if (resolveBlock) resolveBlock.style.display = 'block';
    if (resolvedBanner) resolvedBanner.style.display = 'none';
    if (chatForm) chatForm.style.display = 'block';
}

export function showConfirmModal({ title, message, confirmText, cancelText, onConfirm }) {
    const modal = document.createElement('div');

    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal__overlay"></div>
        <div class="modal__content">
            <div class="modal__header">
                <h3 class="modal__title h3">${title}</h3>
                <button type="button" aria-label="Закрыть окно" class="button button--solid modal__close">
                    <span class="sr-only">Закрыть</span>
                    ⤫
                </button>
            </div>
            <p class="modal__message">${message}</p>

            <div class="modal__actions">
                <button type="button" class="button button--outline button--md modal__cancel">${cancelText}</button>
                <button type="button" class="button button--solid--primary button--md modal__confirm">${confirmText}</button>
            </div>
        </div>
        `;

    document.body.appendChild(modal);

    const overlay = modal.querySelector('.modal__overlay');
    const cancelButton = modal.querySelector('.modal__cancel');
    const closeButton = modal.querySelector('.modal__close');
    const confirmButton = modal.querySelector('.modal__confirm');

    const closeModal = () => modal.remove();

    overlay.addEventListener('click', closeModal);
    cancelButton.addEventListener('click', closeModal);
    closeButton.addEventListener('click', closeModal);

    confirmButton.addEventListener('click', () => {
        onConfirm();
        closeModal();
    })
}

export function showInviteModal(ticketId) {
    const csrfToken = document.querySelector('meta[name="csrf_token"]').getAttribute('content');

    const executor = document.createElement('li');
    executor.innerHTML = `
        <div class="ticket-person button">
            <span class="ticket-person__img ticket-person__img--executor">АП</span>
            <div class="ticket-person__info">
                <p class="ticket-person__label">Алексеев Иван Иванович</p>
                <div class="ticket-person__info-group">
                    <p class="ticket-person__post">Исполнитель</p>
                    <p class="ticket-person__post">Инженер</p>
                    <p class="ticket-person__department">Отдел 942</p>
                    <p class="ticket-person__phone">10 - 10</p>
                    <p class="ticket-person__email">email@polyot.ru</p>
                </div>
            </div>
        </div>
        `;

    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal__overlay"></div>
        <div class="modal__content">
            <div class="modal__header">
                <h3 class="modal__title h3">Пригласить специалиста</h3>
                <button type="button" aria-label="Закрыть окно" class="button button--solid modal__close">
                    <span class="sr-only">Закрыть</span>
                    ⤫
                </button>
            </div>
            <p class="modal__message">Выберите сотрудника, которого хотите пригласить к заявке:</p>

            <input type="text" name="" class="search__input" placeholder="Начните вводить..." value="">

            <ul class="modal__invite-executors"></ul>

            <div class="modal__actions">
                <button type="button" class="button button--outline button--md modal__cancel">Отмена</button>
                <button type="button" class="button button--solid--primary button--md modal__confirm">Отправить уведомление</button>
            </div>
        </div>
        `;

    const modalExecutors = modal.querySelector('.modal__invite-executors');

    for (let index = 0; index < 3; index++)
        modalExecutors.appendChild(executor);

    document.body.appendChild(modal);

    const overlay = modal.querySelector('.modal__overlay');
    const cancelButton = modal.querySelector('.modal__cancel');
    const closeButton = modal.querySelector('.modal__close');
    const confirmButton = modal.querySelector('.modal__confirm');

    const closeModal = () => modal.remove();

    overlay.addEventListener('click', closeModal);
    cancelButton.addEventListener('click', closeModal);
    closeButton.addEventListener('click', closeModal);

    confirmButton.addEventListener('click', async () => {
        try {
            confirmButton.disabled = true;
            confirmButton.textContent = 'Отправляем...';

            const response = await fetch(`/ticket/${ticketId}/invite`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({})
            });

            if (!response.ok) throw new Error();

            closeModal();
        } catch (error) {
            alert('Не удалось отправить приглашение');
            confirmButton.disabled = false;
            confirmButton.textContent = 'Пригласить';
        }

    });
}

export function showAddCommentModal(ticketId) {
    const modal = document.getElementById('modalComment');
    if (!modal) return;

    modal.style.display = 'flex';
    const form = document.getElementById('comment-form');
    if (form) form.reset();

    const filesList = document.getElementById('comment-files');
    if (filesList) {
        filesList.innerHTML = '';
        filesList.style.display = 'none';
    }

    const closeModal = () => modal.style.display = 'none';

    const overlay = modal.querySelector('.modal__overlay');
    overlay.addEventListener('click', closeModal);

    const closeBtn = modal.querySelector('.modal__close');
    closeBtn.addEventListener('click', closeModal);

    initComments();
}

export function SearchExecutors() {
    const searchInput = document.getElementById('executorSearch');
    const executorItems = document.querySelectorAll('#dropdownTicketExecutorList .js-executor-item');
    if (searchInput) {
        searchInput.addEventListener('input', function (e) {
            const searchTerm = e.target.value.toLowerCase().trim();
            executorItems.forEach(item => {
                const label = item.querySelector('.ticket-person__label');
                const userName = label ? label.textContent.toLowerCase() : '';
                const dropdownItem = item.closest('.dropdown-item');
                if (dropdownItem)
                    dropdownItem.style.display = userName.includes(searchTerm) ? '' : 'none';
            });
        });
    }
}

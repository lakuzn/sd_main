// js/ticket/modalManager.js
import { initComments } from '../chat/chat.js';
import { escapeHtml } from '../common/utils.js';

/**
 * Универсальное модальное окно с подтверждением
 */
export function showConfirmModal({ title, message, confirmText, cancelText, onConfirm }) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal__overlay"></div>
        <div class="modal__content">
            <div class="modal__header">
                <h3 class="modal__title h3">${escapeHtml(title)}</h3>
                <button type="button" aria-label="Закрыть окно" class="button button--solid modal__close">
                    <span class="sr-only">Закрыть</span>
                    ⤫
                </button>
            </div>
            <p class="modal__message">${escapeHtml(message)}</p>
            <div class="modal__actions">
                <button type="button" class="button button--outline button--md modal__cancel">${escapeHtml(cancelText)}</button>
                <button type="button" class="button button--solid--primary button--md modal__confirm">${escapeHtml(confirmText)}</button>
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
        onConfirm?.();
        closeModal();
    });

    // Закрытие по Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.style.display === 'flex') {
            closeModal();
        }
    });
}

/**
 * Модальное окно для приглашения специалиста
 */
export function showInviteModal(ticketId) {
    const csrfToken = document.querySelector('meta[name="csrf_token"]')?.getAttribute('content') || '';

    // Временно заглушка – в реальности список исполнителей загружается с сервера
    const mockExecutor = document.createElement('li');
    mockExecutor.innerHTML = `
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
            <input type="text" class="search__input" placeholder="Начните вводить..." value="">
            <ul class="modal__invite-executors"></ul>
            <div class="modal__actions">
                <button type="button" class="button button--outline button--md modal__cancel">Отмена</button>
                <button type="button" class="button button--solid--primary button--md modal__confirm">Отправить уведомление</button>
            </div>
        </div>
    `;

    const modalExecutors = modal.querySelector('.modal__invite-executors');
    // Заглушка – добавим несколько одинаковых элементов
    for (let i = 0; i < 3; i++) {
        modalExecutors.appendChild(mockExecutor.cloneNode(true));
    }

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

    // Закрытие по Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.style.display === 'flex') {
            closeModal();
        }
    });
}

/**
 * Модальное окно для добавления комментария (использует существующий DOM-элемент)
 */
export function showAddCommentModal() {
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
    const closeBtn = modal.querySelector('.modal__close');

    overlay?.addEventListener('click', closeModal);
    closeBtn?.addEventListener('click', closeModal);

    initComments(); // инициализируем логику отправки комментариев

    // Закрытие по Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.style.display === 'flex') {
            closeModal();
        }
    });
}
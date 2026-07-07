// js/ticket/cloneDeleteManager.js
import { fetchCloneTicket, fetchDeleteTicket } from '../api/api.js';
import { showConfirmModal } from './modalManager.js';

/**
 * Инициализирует удаление заявки (кнопка "Удалить заявку")
 */
export function initDeleteTicket() {
    const buttonDeleteTicket = document.getElementById('buttonDeleteTicket');
    if (!buttonDeleteTicket) return;

    const modal = document.getElementById('modalDeleteTicket');
    if (!modal) return;

    buttonDeleteTicket.addEventListener('click', () => {
        modal.style.display = 'flex';
    });

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

    // Закрытие по Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.style.display === 'flex') {
            closeModal();
        }
    });
}

/**
 * Инициализирует клонирование заявки (кнопка "Открыть повторно")
 * Эта функция уже может быть в dashboard/reopenTicket.js, но для единообразия добавим сюда.
 * Если используется только на странице заявки, можно оставить здесь.
 */
export function initCloneTicket() {
    const buttonUnResolved = document.getElementById('buttonUnResolved');
    if (!buttonUnResolved) return;

    buttonUnResolved.addEventListener('click', () => {
        const ticketId = window.currentTicket?.id;
        showConfirmModal({
            title: 'Создать похожую?',
            message: 'Будет создана новая заявка с сохранением полей исходной.',
            confirmText: 'Да, создать заявку',
            cancelText: 'Отмена',
            onConfirm: async () => {
                const result = await fetchCloneTicket(ticketId, buttonUnResolved);
                if (result && result.ticket_id) {
                    window.location.href = '/';
                }
            }
        });
    });
}
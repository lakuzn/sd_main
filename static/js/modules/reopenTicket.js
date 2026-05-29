import { showConfirmModal } from './ticketActions.js';
import { fetchChangeTicketStatus } from "./api.js"

export function initReopenTicket() {
    const buttonsUnResolved = document.querySelectorAll('.js-reopen-card-btn');
    if (!buttonsUnResolved.length) return;

    buttonsUnResolved.forEach(button => {
        const ticketId = button.value;

        button.addEventListener('click', () => {
            showConfirmModal({
                title: 'Создать похожую?',
                message: 'Будет создана заявка с сохранением описания и категорий.',
                confirmText: 'Да, создать заявку',
                cancelText: 'Отмена',
                onConfirm: async () =>
                    await fetchChangeTicketStatus('Новая', button, ticketId),
            });
        });
    });
}
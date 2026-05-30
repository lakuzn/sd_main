import { showConfirmModal } from './ticketActions.js';
import { fetchCloneTicket } from "./api.js"

export function initReopenTicket() {
    const buttonsUnResolved = document.querySelectorAll('.js-reopen-card-btn');
    if (!buttonsUnResolved.length) return;

    buttonsUnResolved.forEach(button => {
        const ticketId = button.dataset.ticketId;

        button.addEventListener('click', () => {
            showConfirmModal({
                title: 'Создать похожую?',
                message: 'Будет создана новая заявка с сохранением описания и категорий.',
                confirmText: 'Да, создать заявку',
                cancelText: 'Отмена',
                onConfirm: async () => {
                    const result = await fetchCloneTicket(ticketId, button);
                    if (result && result.ticket_id) {
                        window.location.href = `/ticket/${result.ticket_id}`;
                    }
                }
            });
        });
    });
}

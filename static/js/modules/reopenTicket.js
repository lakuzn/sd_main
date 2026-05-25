import { showConfirmModal } from './ticketActions.js';
import { fetchChangeTicketStatus } from "./api.js"

export function initReopenTicket() {
    const buttonUnResolved = document.getElementById('buttonUnResolved');

    if (buttonUnResolved) {
        const ticketId = buttonUnResolved.value;

        buttonUnResolved.addEventListener('click', () => {
            showConfirmModal({
                title: 'Создать похожую?',
                message: 'Будет создана заявка с сохранением описания и категорий.',
                confirmText: 'Да, создать заявку',
                cancelText: 'Отмена',
                onConfirm: async () =>
                    await fetchChangeTicketStatus('Новая', buttonUnResolved, ticketId),
            });
        });
    }
}
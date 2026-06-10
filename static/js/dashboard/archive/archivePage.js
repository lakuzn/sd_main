// js/archive/archivePage.js
import { initArchiveTabs } from './archiveTabs.js';
import { showConfirmModal } from '../../ticket/modalManager.js';
import { fetchCloneTicket } from '../../api/api.js';

function initReopenButtons() {
    const buttonsUnResolved = document.querySelectorAll('.js-reopen-card-btn');
    if (!buttonsUnResolved.length) return;

    buttonsUnResolved.forEach(button => {
        const ticketId = button.dataset.ticketId;

        button.addEventListener('click', () => {
            showConfirmModal({
                title: 'Создать похожую?',
                message: 'Будет создана новая заявка с сохранением полей исходной.',
                confirmText: 'Да, создать заявку',
                cancelText: 'Отмена',
                onConfirm: async () => {
                    const result = await fetchCloneTicket(ticketId, button);
                    if (result && result.ticket_id) {
                        window.location.href = '/';
                    }
                }
            });
        });
    });
}

export function initArchivePage() {
    initArchiveTabs();
    initReopenButtons();
}
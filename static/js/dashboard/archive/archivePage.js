// js/archive/archivePage.js
import { initArchiveTabs } from './archiveTabs.js';
import { initArchiveExport } from './archiveExport.js';
import { showConfirmModal } from '../../ticket/modalManager.js';
import { fetchCloneTicket } from '../../api/api.js';

/**
 * Инициализация кнопок "Создать похожую"
 */
function initReopenButtons() {
    const buttonsUnResolved = document.querySelectorAll('.js-reopen-card-btn');
    if (!buttonsUnResolved.length) return;

    buttonsUnResolved.forEach(button => {
        const ticketId = button.dataset.ticketId;

        // Удаляем старый обработчик, чтобы не было дублирования
        const newButton = button.cloneNode(true);
        button.parentNode.replaceChild(newButton, button);

        newButton.addEventListener('click', (e) => {
            e.preventDefault();
            showConfirmModal({
                title: 'Создать похожую?',
                message: 'Будет создана новая заявка с сохранением полей исходной.',
                confirmText: 'Да, создать заявку',
                cancelText: 'Отмена',
                onConfirm: async () => {
                    const result = await fetchCloneTicket(ticketId, newButton);
                    if (result && result.ticket_id) {
                        window.location.href = '/';
                    }
                }
            });
        });
    });
}

// Делаем функцию глобальной для использования в archiveTabs.js
window.initReopenButtons = initReopenButtons;

/**
 * Основная функция инициализации страницы архива
 */
export function initArchivePage() {
    initArchiveTabs();
    initReopenButtons();
    initArchiveExport();
}
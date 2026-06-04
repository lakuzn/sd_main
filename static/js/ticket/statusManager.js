import { fetchChangeTicketStatus, fetchCloneTicket } from "../api/api.js";
import { showConfirmModal } from './modalManager.js';

/**
 * Устанавливает UI для режима "Решена"
 */
export function setResolvedMode() {
    const resolveBlock = document.getElementById('resolve-block');
    const resolvedBanner = document.getElementById('resolved-banner');
    const chatForm = document.getElementById('chat-form')

    if (resolveBlock) resolveBlock.style.display = 'none';
    if (resolvedBanner) resolvedBanner.style.display = 'block';
    if (chatForm) chatForm.style.display = 'none';
}

/**
 * Устанавливает UI для активного режима (заявка не решена)
 */
export function setActiveMode() {
    const resolveBlock = document.getElementById('resolve-block');
    const resolvedBanner = document.getElementById('resolved-banner');
    const chatForm = document.getElementById('chat-form')

    if (resolveBlock) resolveBlock.style.display = 'block';
    if (resolvedBanner) resolvedBanner.style.display = 'none';
    if (chatForm) chatForm.style.display = 'block';
}

/**
 * Инициализирует интерфейс в зависимости от статуса заявки
 */
export function initTicketInterface() {
    const currentStatus = window.currentTicket?.status;
    currentStatus === 'Решена' ? setResolvedMode() : setActiveMode();
}

/**
 * Инициализирует кнопки смены статуса (Решена / Открыть повторно)
 */
export function initStatusButtons() {
    const buttonResolved = document.getElementById('buttonResolved');
    const buttonUnResolved = document.getElementById('buttonUnResolved');

    if (buttonResolved) {
        buttonResolved.addEventListener('click', () => {
            showConfirmModal({
                title: 'Закрыть заявку?',
                message: 'После закрытия заявка перейдёт в статус "Решена".',
                confirmText: 'Да, закрыть заявку',
                cancelText: 'Отмена',
                onConfirm: async () => {
                    const newStatus = await fetchChangeTicketStatus('Решена', buttonResolved);
                    if (newStatus === 'Решена') {
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
                        window.location.href = '/';
                    }
                }
            });
        });
    }
}
import { fetchResolveTicket } from "../api/api.js";
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
 * Инициализирует кнопку закрытия заявки (Решена).
 * Кнопка "Открыть повторно" обрабатывается в cloneDeleteManager.
 */
export function initStatusButtons() {
    const buttonResolved = document.getElementById('buttonResolved');

    if (buttonResolved) {
        buttonResolved.addEventListener('click', () => {
            showConfirmModal({
                title: 'Закрыть заявку?',
                message: 'После закрытия заявка перейдёт в статус "Решена".',
                confirmText: 'Да, закрыть заявку',
                cancelText: 'Отмена',
                onConfirm: async () => {
                    const result = await fetchResolveTicket(window.currentTicket?.id, buttonResolved);
                    if (result && result.status === 'success') {
                        // Перезагружаем страницу: статус, чат и кнопки
                        // ("Открыть повторно" / "Удалить заявку") обновятся актуально
                        window.location.reload();
                    }
                }
            });
        });
    }
}
// js/ticket/ticketPage.js
import { initTicketInterface, initStatusButtons } from './statusManager.js';
import { initDeleteTicket, initCloneTicket } from './cloneDeleteManager.js';
import { initInviteButton, initCommentButtons } from './actionHandlers.js';
import { initChat } from '../chat/chat.js';
import { initTicketParams } from './ticketParams.js';

/**
 * Главная инициализация страницы заявки
 */
export function initTicketPage() {
    initTicketInterface();      // установка режима (решена/активна)
    initStatusButtons();        // кнопки "Решена" / "Открыть повторно"
    initDeleteTicket();         // удаление заявки
    initCloneTicket();          // клонирование (создание похожей)
    initInviteButton();         // пригласить специалиста
    initCommentButtons();       // кнопки комментариев
    initChat();                 // чат и комментарии (socket, отправка)
    initTicketParams();         // редактируемые параметры (приоритет, категории и т.д.)
}
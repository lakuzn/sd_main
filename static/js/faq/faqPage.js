// js/faq/faqPage.js
import { initFiltersFaq } from './filtersFaq.js';
import { initKBSocket } from './kbSocket.js';

/**
 * Инициализация страницы FAQ / Базы знаний
 * - фильтры категорий
 * - WebSocket для обновлений в реальном времени
 */
export function initFaqPage() {
    initFiltersFaq();
    initKBSocket();
}
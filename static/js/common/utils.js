// js/common/utils.js

/**
 * Парсит строку JSON в массив
 * @param {string} rawData
 * @returns {Array}
 */
export function parseToJson(rawData) {
    if (!rawData) return [];

    try {
        const parsed = JSON.parse(rawData);
        return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
        console.warn('Не удалось распарсить строку:', rawData);
        return [];
    }
}

/**
 * Экранирует HTML-спецсимволы
 * @param {string} str
 * @returns {string}
 */
export function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>]/g, function (m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}

/**
 * Преобразует URL в ссылки внутри текста
 * @param {string} text
 * @returns {string}
 */
export function linkify(text) {
    if (!text) return '';

    const urlRegex = /(https?:\/\/[^\s<]+[^<.,:;"')\]\s])/g;

    return text.replace(urlRegex, (url) => {
        return `<a href="${url}" target="_blank" rel="noopener noreferrer">
                    ${url}
                </a>`;
    });
}

/**
 * Дебаунс для ограничения частоты вызова функции
 * @param {Function} fn
 * @param {number} delay
 * @returns {Function}
 */
export function debounce(fn, delay = 300) {
    let timer;
    return function (...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
    };
}

/**
 * Получает CSRF-токен из meta-тега
 * @returns {string}
 */
export function getCSRFToken() {
    return document.querySelector('meta[name="csrf_token"]')?.getAttribute('content') || '';
}

/**
 * Скроллит контейнер вниз
 * @param {HTMLElement} container
 */
export function scrollToBottom(container) {
    if (!container) return;
    setTimeout(() => {
        container.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }, 50);
}

/**
 * Форматирует дату для отображения в чате
 * @param {string} dateStr
 * @returns {string}
 */
export function formatMessageTime(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleTimeString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
    });
}

/**
 * Формирует инициалы из ФИО
 * @param {string} fullName
 * @returns {string}
 */
export function getInitials(fullName) {
    if (!fullName) return '?';
    const nameParts = fullName.trim().split(/\s+/);
    const firstInitial = nameParts[0]?.[0] || '';
    const secondInitial = nameParts[1]?.[0] || '';
    return (firstInitial + secondInitial).toUpperCase();
}

import { linkify } from "../common/utils.js";
import { setResolvedMode, setActiveMode } from "./ticketActions.js";
import { fetchSendMessage, setFileUploadClearFn } from "../api/api.js";
import { initFileUpload } from "../modules/fileUploadChat.js";

let socket = null;
// Флаг, чтобы слушатель receive_comment не дублировался
let commentListenerAttached = false;

export function setupDiscussion(config) {
    const {
        formId,
        inputId,
        fileInputId,
        fileListId,
        containerId,
        historyId,
        dropZoneId = null,
        isComment = false
    } = config;

    const form = document.getElementById(formId);
    const input = document.getElementById(inputId);
    const fileInput = document.getElementById(fileInputId);
    const container = document.getElementById(containerId);

    if (!input || !form) return;
    if (container) container.scrollTop = container.scrollHeight;

    // Защита от повторной привязки обработчиков (иначе сообщения дублируются
    // при повторном открытии окна комментариев)
    if (form.dataset.discussionBound === '1') return;
    form.dataset.discussionBound = '1';

    const fileControls = initFileUpload(fileInputId, fileListId, dropZoneId);

    const sendHandler = () => {
        if (fileControls) setFileUploadClearFn(fileControls.clearFiles);
        fetchSendMessage(input, fileInput, isComment);
    };

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendHandler();
        }
    });

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        sendHandler();
    });

    // Вставка файлов из буфера обмена
    input.addEventListener('paste', (e) => {
        if (!fileInput || !fileControls) return;
        const items = e.clipboardData?.items;
        if (!items) return;

        let hasFiles = false;
        for (const item of items) {
            if (item.kind === 'file') {
                hasFiles = true;
                const file = item.getAsFile();
                if (file) fileControls.addFile(file);
            }
        }
        if (hasFiles) e.preventDefault();
    });
}

function initSocket(ticketId) {
    socket = io();
    socket.on('connect', () => {
        socket.emit('join_ticket', { ticket_id: ticketId });
    });
}

export function initChat() {
    const ticketId = window.currentTicket?.id;
    if (!ticketId) return;

    initSocket(ticketId);

    const history = document.getElementById('chat-history');
    scrollToBottom(history);

    const newMessageDot = document.getElementById('ticketNewMessage');
    const chatInput = document.getElementById('chat-input');

    socket.on('receive_message', (data) => {
        if (history) {
            appendMessage(data, history);
            scrollToBottom(history);
        }

        // Точка-индикатор о новом сообщении от другого пользователя
        if (newMessageDot && data.sender_id !== Number(window.currentUserId || 0)) {
            newMessageDot.style.display = 'inline-block';
        }
    });

    // Скрываем индикатор, когда пользователь работает с чатом
    if (chatInput && newMessageDot) {
        chatInput.addEventListener('focus', () => {
            newMessageDot.style.display = 'none';
        });
    }

    socket.on('ticket_status_changed', (data) => {
        if (data.ticket_id == ticketId) {
            data.new_status === 'Решена' ? setResolvedMode() : setActiveMode();
        }
    });

    socket.on('error', (err) => console.log("Socket error:", err));

    setupDiscussion({
        formId: 'chat-form',
        inputId: 'chat-input',
        fileInputId: 'chat-attachments',
        fileListId: 'chat-files',
        containerId: 'chat-discussion',
        historyId: 'chat-history',
        dropZoneId: 'chat-input',
        isComment: false
    });

    // Слушатель комментариев подключаем один раз вместе с чатом
    _initCommentListener();
}

function _initCommentListener() {
    if (commentListenerAttached || !socket) return;
    commentListenerAttached = true;

    const history = document.getElementById('comment-history');

    socket.on('receive_comment', (data) => {
        if (history) {
            appendComment(data, history);
            scrollToBottom(history);
        }

        // Показываем кнопку «Внутр. комм.», если её ещё нет
        const ticketBlock = document.querySelector('.ticket-block--comments');
        if (ticketBlock) {
            ticketBlock.style.display = '';
            const btn = ticketBlock.querySelector('#buttonSeeComments');
            if (btn) {
                const countEl = btn.querySelector('.comments__count');
                if (countEl) {
                    countEl.textContent = parseInt(countEl.textContent || '0') + 1;
                }
            }
        }
    });
}

export function initComments() {
    const history = document.getElementById('comment-history');
    scrollToBottom(history);

    // Слушатель уже подключён в initChat — только настраиваем форму
    setupDiscussion({
        formId: 'comment-form',
        inputId: 'comment-input',
        fileInputId: 'comment-attachments',
        fileListId: 'comment-files',
        containerId: 'comment-discussion',
        historyId: 'comment-history',
        dropZoneId: 'comment-input',
        isComment: true
    });
}

function appendMessage(data, history) {
    const isMyMessage = data.sender_id === Number(window.currentUserId || 0);

    const nameParts = (data.sender_name || '?').split(' ');
    const initials = nameParts[0][0].toUpperCase()
        + (nameParts.length > 1 ? nameParts[1][0].toUpperCase() : '');

    let timeStr = '';
    if (data.created_at) {
        const date = new Date(data.created_at);
        timeStr = date.toLocaleTimeString('ru-RU', {
            day: "2-digit",
            month: "2-digit",
            hour: '2-digit',
            minute: '2-digit',
        });
    }

    const msgClass = isMyMessage
        ? 'discussion-chat__message--right'
        : 'discussion-chat__message--left';

    const positionLabel = data.sender_position
        ? `<p class="message-content__position">${data.sender_position}</p>`
        : '';

    let attachmentsHTML = '';
    if (data.attachments && data.attachments.length > 0) {
        attachmentsHTML = '<div class="message-attachments">';
        data.attachments.forEach(file => {
            attachmentsHTML += `
                <a href="${file.url}"
                    target="_blank"
                    class="message-attachments__item button button--outline">
                    ${file.file_name}
                </a>`;
        });
        attachmentsHTML += '</div>';
    }

    const newMessageHTML = `
        <div class="discussion-chat__message ${msgClass}">
            <span class="user__avatar">${initials}</span>

            <div class="discussion-chat__message-content">
                <div class="message-content__body">
                    <div class="message-content__title">
                        <p class="message-content__user">${data.sender_name}</p>
                        ${positionLabel}
                        <time class="message-content__time" datetime="${data.created_at || ''}">
                            ${timeStr}
                        </time>
                    </div>
                    <p class="message-content__description">${linkify(data.content || '')}</p>
                </div>

                ${attachmentsHTML}
            </div>
        </div>`;

    history.insertAdjacentHTML('beforeend', newMessageHTML);
}

function appendComment(data, history) {
    let timeStr = '';
    if (data.created_at) {
        const date = new Date(data.created_at);
        timeStr = date.toLocaleTimeString('ru-RU', {
            day: "2-digit",
            month: "2-digit",
            hour: '2-digit',
            minute: '2-digit',
        });
    }

    let attachmentsHTML = '';
    if (data.attachments && data.attachments.length > 0) {
        attachmentsHTML = '<div class="message-attachments">';
        data.attachments.forEach(file => {
            attachmentsHTML += `
                <a href="${file.url}"
                    target="_blank"
                    class="message-attachments__item button button--outline">
                    ${file.file_name}
                </a>`;
        });
        attachmentsHTML += '</div>';
    }

    const newCommentHTML = `
        <div class="discussion-chat__message discussion-chat__message--left">
            <div class="discussion-chat__message-content">
                <div class="message-content__body">
                    <div class="message-content__title">
                        <p class="message-content__user">${data.author_name || ''}</p>
                        <time class="message-content__time" datetime="${data.created_at || ''}">
                            ${timeStr}
                        </time>
                    </div>
                    <p class="message-content__description">${linkify(data.text || '')}</p>
                </div>
                ${attachmentsHTML}
            </div>
        </div>`;

    history.insertAdjacentHTML('beforeend', newCommentHTML);
}

function scrollToBottom(container) {
    if (!container) return;

    setTimeout(() => {
        container.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }, 50);
}

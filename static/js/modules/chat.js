import { linkify } from "./utils.js";
import { setResolvedMode, setActiveMode } from "./ticketActions.js";
import { fetchSendMessage, setFileUploadClearFn } from "./api.js";
import { initFileUpload } from "../modules/fileUploadChat.js";

let socket = null

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

    socket.on('receive_message', (data) => {
        if (history) {
            appendMessage(data, history);
            scrollToBottom(history);
        }
    });

    socket.on('ticket_status_changed', (data) => {
        if (data.ticket_id == ticketId) data.new_status === 'Решена' ? setResolvedMode() : setActiveMode();
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
}

export function initComments() {
    const history = document.getElementById('comment-history');
    scrollToBottom(history);

    socket.on('receive_comment', (data) => {
        if (history) {
            appendComment(data, history);
            scrollToBottom(history);
        }
    });

    socket.on('error', (err) => console.log("Socket error:", err));

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

    // Инициалы
    const nameParts = (data.sender_name || '?').split(' ');
    const initials = nameParts[0][0].toUpperCase()
        + (nameParts.length > 1 ? nameParts[1][0].toUpperCase() : '');

    // Время
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
                            <time class="message-content__time" datetime="${data.created_at || ''}">
                                ${timeStr}
                            </time>
                        </div>
                        <p class="message-content__description">${linkify(data.content || '')}</p>
                    </div>

                    ${attachmentsHTML}
                </div>
            </div>
            `;

    history.insertAdjacentHTML('beforeend', newMessageHTML);
}

function appendComment(data, history) {
    // Время
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

    const newCommentHTML = `
        <div class="discussion-chat__message discussion-chat__message--left">
            <div class="discussion-chat__message-content">
                <div class="message-content__body">
                <div class="message-content__title">
                    <time class="message-content__time" datetime="${data.created_at || ''}">
                        ${timeStr}
                    </time>
                </div>
                <p class="message-content__description">${linkify(data.text || '')}</p>
            </div>
        </div>
        `;

    history.insertAdjacentHTML('beforeend', newCommentHTML);
}

function scrollToBottom(container) {
    if (!container) return;

    setTimeout(() => {
        container.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }, 50);
}


// js/chat/chat.js
import { initSocket } from './socketClient.js';
import { setupDiscussion } from './setupDiscussion.js';
import { renderMessage } from './messageRenderer.js';
import { setResolvedMode, setActiveMode } from '../ticket/statusManager.js';
import { scrollToBottom } from '../common/utils.js';

let chatInitialized = false;

export function initChat() {
    if (chatInitialized) return;
    chatInitialized = true;

    const ticketId = window.currentTicket?.id;
    if (!ticketId) return;

    const history = document.getElementById('chat-history');
    scrollToBottom(history);

    const newMessageDot = document.getElementById('ticketNewMessage');
    const chatInput = document.getElementById('chat-input');

    const socket = initSocket(ticketId, {
        onReceiveMessage: (data) => {
            if (history) {
                const html = renderMessage(data, window.currentUserId, false);
                history.insertAdjacentHTML('beforeend', html);
                scrollToBottom(history);
            }
            if (newMessageDot && data.sender_id !== Number(window.currentUserId)) {
                newMessageDot.style.display = 'inline-block';
            }
        },
        onStatusChanged: (data) => {
            if (data.ticket_id == ticketId) {
                data.new_status === 'Решена' ? setResolvedMode() : setActiveMode();
            }
        }
    });

    // Скрываем индикатор при фокусе на поле ввода
    if (chatInput && newMessageDot) {
        chatInput.addEventListener('focus', () => {
            newMessageDot.style.display = 'none';
        });
    }

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

    const ticketId = window.currentTicket?.id;
    if (!ticketId) return;

    const socket = initSocket(ticketId, {
        onReceiveComment: (data) => {
            if (history) {
                const html = renderMessage(data, window.currentUserId, true);
                history.insertAdjacentHTML('beforeend', html);
                scrollToBottom(history);
            }

            // Показываем кнопку "Внутр. комм.", если её ещё нет
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
        }
    });

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

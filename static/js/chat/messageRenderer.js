// js/chat/messageRenderer.js
import { linkify, formatMessageTime, getInitials, escapeHtml } from '../common/utils.js';

export function renderMessage(data, currentUserId, isComment = false) {
    const isMyMessage = data.sender_id === Number(currentUserId);

    const initials = getInitials(data.sender_name || data.author_name || '?');
    const timeStr = formatMessageTime(data.created_at);

    const msgClass = isMyMessage
        ? 'discussion-chat__message--right'
        : 'discussion-chat__message--left';

    const positionLabel = data.sender_position && !isComment
        ? `<p class="message-content__position">${escapeHtml(data.sender_position)}</p>`
        : '';

    let attachmentsHTML = '';
    if (data.attachments && data.attachments.length > 0) {
        attachmentsHTML = '<div class="message-attachments">';
        data.attachments.forEach(file => {
            attachmentsHTML += `
                <a href="${file.url}" target="_blank" 
                   class="message-attachments__item button button--outline">
                    ${escapeHtml(file.file_name)}
                </a>`;
        });
        attachmentsHTML += '</div>';
    }

    const userName = data.sender_name || data.author_name || 'Пользователь';
    const content = linkify(data.content || data.text || '');

    if (isComment) {
        return `
            <div class="discussion-chat__message discussion-chat__message--left">
                <div class="discussion-chat__message-content">
                    <div class="message-content__body">
                        <div class="message-content__title">
                            <p class="message-content__user">${escapeHtml(userName)}</p>
                            <time class="message-content__time">${timeStr}</time>
                        </div>
                        <p class="message-content__description">${content}</p>
                    </div>
                    ${attachmentsHTML}
                </div>
            </div>`;
    }

    return `
        <div class="discussion-chat__message ${msgClass}">
            <span class="user__avatar">${initials}</span>
            <div class="discussion-chat__message-content">
                <div class="message-content__body">
                    <div class="message-content__title">
                        <p class="message-content__user">${escapeHtml(userName)}</p>
                        ${positionLabel}
                        <time class="message-content__time">${timeStr}</time>
                    </div>
                    <p class="message-content__description">${content}</p>
                </div>
                ${attachmentsHTML}
            </div>
        </div>`;
}
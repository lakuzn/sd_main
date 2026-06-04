// js/chat/discussionSetup.js
import { initChatFileUpload } from './fileUpload.js';
import { fetchSendMessage, setFileUploadClearFn } from '../api/api.js';

export function setupDiscussion(config) {
    const {
        formId,
        inputId,
        fileInputId,
        fileListId,
        containerId,
        dropZoneId = null,
        isComment = false
    } = config;

    const form = document.getElementById(formId);
    const input = document.getElementById(inputId);
    const fileInput = document.getElementById(fileInputId);
    const container = document.getElementById(containerId);

    if (!input || !form) return;
    if (container) container.scrollTop = container.scrollHeight;

    // Защита от повторной привязки
    if (form.dataset.discussionBound === '1') return;
    form.dataset.discussionBound = '1';

    const fileControls = initChatFileUpload(fileInputId, fileListId, dropZoneId);

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

        for (const item of items) {
            if (item.kind === 'file') {
                const file = item.getAsFile();
                if (file) fileControls.addFile(file);
            }
        }
    });
}

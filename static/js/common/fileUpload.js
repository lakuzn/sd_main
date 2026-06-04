// js/common/fileUpload.js

import { escapeHtml } from "./utils.js";

/**
 * Универсальный менеджер загрузки файлов
 * @param {Object} config
 * @param {string} config.fileInputId - ID input[type=file]
 * @param {string} config.fileListId - ID контейнера для отображения списка файлов
 * @param {string} [config.dropZoneId] - ID зоны для drag-and-drop (опционально)
 * @param {string} [config.itemClass='form-files__item'] - класс для элемента списка
 * @param {string} [config.nameClass='form-files__name'] - класс для имени файла
 * @param {string} [config.removeClass='form-files__remove'] - класс для кнопки удаления
 * @param {Function} [config.onChange] - колбэк при изменении списка файлов (получает файлы)
 * @param {Function} [config.fileFilter] - функция фильтрации файлов (по умолчанию все)
 * @returns {Object} API { getFiles, clearFiles, addFile }
 */
export function createFileUploadManager(config) {
    const {
        fileInputId,
        fileListId,
        dropZoneId = null,
        itemClass = 'form-files__item',
        nameClass = 'form-files__name',
        removeClass = 'form-files__remove',
        onChange = null,
        fileFilter = (file) => true
    } = config;

    const fileInput = document.getElementById(fileInputId);
    const fileList = document.getElementById(fileListId);
    const dropZone = dropZoneId ? document.getElementById(dropZoneId) : null;

    if (!fileInput) return null;

    let currentFiles = [];

    // Форматирование размера
    function formatSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Обновление отображения списка
    function updateFileList() {
        if (!fileList) return;
        fileList.innerHTML = '';

        currentFiles.forEach((file, index) => {
            const li = document.createElement('li');
            li.className = itemClass;
            li.innerHTML = `
                <span class="${nameClass}">${escapeHtml(file.name)} (${formatSize(file.size)})</span>
                <button type="button" data-index="${index}" class="${removeClass}" aria-label="Удалить файл">✕</button>
            `;

            fileList.appendChild(li);
        });

        fileList.style.display = currentFiles.length === 0 ? 'none' : 'flex';
    }

    // Синхронизация с input
    function syncFileInput() {
        const dataTransfer = new DataTransfer();
        currentFiles.forEach(f => dataTransfer.items.add(f));
        fileInput.files = dataTransfer.files;
    }

    // Добавление файлов
    function addFiles(files) {
        const fileArray = Array.from(files).filter(fileFilter);
        if (fileArray.length === 0) return;

        currentFiles = [...currentFiles, ...fileArray];
        updateFileList();
        syncFileInput();
    }

    // Удаление по индексу
    function removeFile(index) {
        if (index >= 0 && index < currentFiles.length) {
            currentFiles.splice(index, 1);
            updateFileList();
            syncFileInput();
        }
    }

    // Очистка всех файлов
    function clearFiles() {
        currentFiles = [];
        updateFileList();
        syncFileInput();
        fileInput.value = ''; // очищаем input
    }

    // Обработчики событий
    fileInput.addEventListener('change', (e) => {
        addFiles(e.target.files);
        // Очищаем input, чтобы можно было загрузить те же файлы повторно
        // fileInput.value = '';
    });

    // Клик по кнопкам удаления (делегирование)
    fileList.addEventListener('click', (e) => {
        const btn = e.target.closest(`.${removeClass}`);
        if (btn && btn.dataset.index !== undefined) {
            const index = parseInt(btn.dataset.index);
            removeFile(index);
        }
    });

    // Drag-and-drop
    if (dropZone) {
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            addFiles(e.dataTransfer.files);
        });
    }

    return {
        getFiles: () => [...currentFiles],
        clearFiles,
        addFile: (file) => addFiles([file])
    };
}

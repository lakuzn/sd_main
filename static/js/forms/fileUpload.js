// export function initCreateTicketForm() {
//     const dropZone = document.getElementById('dropzone');
//     const fileInput = document.getElementById('attachments');
//     const selectedFileList = document.getElementById('ticketFiles');

//     if (!dropZone || !fileInput) return;

//     let currentFiles = [];

//     function updateFileList() {
//         selectedFileList.innerHTML = '';

//         currentFiles.forEach((file, index) => {
//             const li = document.createElement('li');
//             li.className = 'ticket__group-item';
//             li.innerHTML = `
//                 <span class="group__item-name">${file.name} ${(file.size / 1024).toFixed(2)}КВ</span>
//                 <button type="button" data-index="${index}" aria-label="Удалить файл" 
//                 class="group__item-remove button button--solid--danger">&#10539</button>
//             `;
//             selectedFileList.appendChild(li);
//         });

//         selectedFileList.style.display = currentFiles.length === 0 ? 'none' : 'flex';

//         selectedFileList.querySelectorAll('.group__item-remove').forEach(btn => {
//             btn.addEventListener('click', () => {
//                 const idx = parseInt(btn.dataset.index);
//                 currentFiles.splice(idx, 1);

//                 const dataTransfer = new DataTransfer();
//                 currentFiles.forEach(f => dataTransfer.items.add(f));
//                 fileInput.files = dataTransfer.files;

//                 updateFileList();
//             });
//         });
//     }

//     function isAllowedFileType(file) {
//         // const allowedTypes = ['image/jpeg', 'image/png', 'application/pdf', ...];
//         // return allowedTypes.includes(file.type) || file.name.match(/\.(jpg|jpeg|png|pdf|doc|docx)$/i);
//         return true;
//     }

//     function handleFiles(files) {
//         const newFiles = Array.from(files).filter(isAllowedFileType);

//         if (newFiles.length === 0) return;

//         currentFiles = [...currentFiles, ...newFiles];
//         updateFileList();

//         const dataTransfer = new DataTransfer();
//         currentFiles.forEach(file => dataTransfer.items.add(file));
//         fileInput.files = dataTransfer.files;
//     }

//     fileInput.addEventListener('change', (e) => {
//         handleFiles(e.target.files);
//     });

//     dropZone.addEventListener('dragover', (e) => {
//         e.preventDefault();
//         dropZone.classList.add('dragover');
//     });

//     dropZone.addEventListener('dragleave', () => {
//         dropZone.classList.remove('dragover');
//     });

//     dropZone.addEventListener('drop', (e) => {
//         e.preventDefault();
//         dropZone.classList.remove('dragover');
//         handleFiles(e.dataTransfer.files);
//     });

//     updateFileList();
// }

import { createFileUploadManager } from '../common/fileUpload.js';

export function initCreateTicketFormFileUpload() {
    return createFileUploadManager({
        fileInputId: 'attachments',
        fileListId: 'ticketFiles',
        dropZoneId: 'dropzone',
        itemClass: 'ticket__group-item',
        nameClass: 'group__item-name',
        removeClass: 'group__item-remove'
    });
}
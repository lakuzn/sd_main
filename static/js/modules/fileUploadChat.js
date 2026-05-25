export function initFileUpload(fileInputId, fileListId, dropZoneId) {
    const fileInput = document.getElementById(fileInputId);
    const fileList = document.getElementById(fileListId);
    const dropZone = document.getElementById(dropZoneId);

    if (!fileInput) return;

    let currentFiles = [];

    function updateFileList() {
        if (!fileList) return;
        fileList.innerHTML = '';

        currentFiles.forEach((file, index) => {
            const li = document.createElement('li');
            li.className = 'form-files__item';
            li.innerHTML = `
                <span class=form-files__name">${file.name} ${(file.size / 1024).toFixed(2)}КВ</span>
                <button type="button" data-index="${index}" aria-label="Удалить файл" 
                class="form-files__remove button button--solid--danger">&#10539</button>
            `;

            const removeBtn = li.querySelector(".form-files__remove");
            removeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                currentFiles.splice(index, 1);
                updateFileList();
                syncFileInput();
            });

            fileList.appendChild(li);
        });

        fileList.style.display = currentFiles.length === 0 ? 'none' : 'flex';
    }

    function syncFileInput() {
        const dataTransfer = new DataTransfer();
        currentFiles.forEach(f => dataTransfer.items.add(f));
        fileInput.files = dataTransfer.files;
    }

    function isAllowedFileType(file) {
        // const allowedTypes = ['image/jpeg', 'image/png', 'application/pdf', ...];
        // return allowedTypes.includes(file.type) || file.name.match(/\.(jpg|jpeg|png|pdf|doc|docx)$/i);
        return true;
    }

    function handleFiles(files) {
        const newFiles = Array.from(files).filter(isAllowedFileType);
        if (newFiles.length === 0) return;

        currentFiles = [...currentFiles, ...newFiles];
        updateFileList();
        syncFileInput();
    }

    function clearFiles() {
        currentFiles = [];
        updateFileList();
        syncFileInput();
        fileInput.value = '';
    }

    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });

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
        handleFiles(e.dataTransfer.files);
    });

    return { clearFiles };
}

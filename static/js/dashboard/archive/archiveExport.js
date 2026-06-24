// js/dashboard/filterExport.js
export function initArchiveExport() {
    const btnExport = document.getElementById('exportExcel');
    if (!btnExport) return;

    // Открытие модалки
    btnExport.addEventListener('click', () => showArchiveExportModal());

    // Обработчики внутри модалки
    const modal = document.getElementById('modalExport');
    if (!modal) return;

    const closeModal = () => { modal.style.display = 'none'; };
    const overlay = modal.querySelector('.modal__overlay');
    const closeBtn = modal.querySelector('.modal__close');
    const cancelBtn = modal.querySelector('.modal__cancel');
    const confirmBtn = modal.querySelector('.modal__confirm');
    const startInput = document.getElementById('exportStart');
    const endInput = document.getElementById('exportEnd');

    // Закрытие по оверлею, крестику или кнопке "Отмена"
    overlay?.addEventListener('click', closeModal);
    closeBtn?.addEventListener('click', closeModal);
    cancelBtn?.addEventListener('click', closeModal);

    // Основное действие – скачивание через fetch
    confirmBtn?.addEventListener('click', async () => {
        const start = startInput?.value || '';
        const end = endInput?.value || '';

        // Валидация: начало не позже конца
        if (start && end && start > end) {
            alert('Дата начала не может быть позже даты окончания.');
            return;
        }

        // Формируем URL с параметрами
        const params = new URLSearchParams();
        if (start) params.set('start', start);
        if (end) params.set('end', end);
        const url = `/export?${params.toString()}`;

        try {
            // Отправляем GET-запрос
            const response = await fetch(url, {
                method: 'GET',
                headers: { 'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }
            });

            if (!response.ok) {
                // Пытаемся прочитать сообщение об ошибке (может быть flash или JSON)
                const errorText = await response.text();
                alert(`Ошибка при выгрузке: ${response.status} ${response.statusText}\n${errorText}`);
                return;
            }

            // Получаем blob (двоичные данные файла)
            const blob = await response.blob();

            // Извлекаем имя файла из заголовка Content-Disposition (если есть)
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `report_${new Date().toISOString().slice(0, 10)}.xlsx`;
            if (contentDisposition) {
                const match = contentDisposition.match(/filename="?(.+)"?/);
                if (match) filename = match[1];
            }

            // Создаём ссылку и инициируем скачивание
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(link.href);

            // Закрываем модалку
            closeModal();

        } catch (error) {
            console.error('Ошибка при скачивании:', error);
            alert('Произошла ошибка при скачивании файла. Попробуйте позже.');
        }
    });

    // Закрытие по Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.style.display === 'flex') {
            closeModal();
        }
    });
}

function showArchiveExportModal() {
    const modal = document.getElementById('modalExport');
    if (!modal) return;

    // Очищаем предыдущие значения
    const startInput = document.getElementById('exportStart');
    const endInput = document.getElementById('exportEnd');
    if (startInput) startInput.value = '';
    if (endInput) {
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        endInput.value = `${year}-${month}-${day}`;
    }

    modal.style.display = 'flex';
}
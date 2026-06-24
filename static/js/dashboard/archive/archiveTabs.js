// js/archive/archiveTabs.js
let currentType = 'all';

/**
 * Обновление счётчиков на кнопках
 */
function updateCounters(counts) {
    for (const [key, value] of Object.entries(counts)) {
        const countElement = document.getElementById(`count-${key}`);
        if (countElement) {
            countElement.textContent = value;
        }
    }
}

/**
 * Обновление активной вкладки
 */
function setActiveTab(activeType) {
    const tabs = document.querySelectorAll('#archiveTabs .button');
    tabs.forEach(tab => {
        const tabType = tab.dataset.type;
        if (tabType === activeType) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });
}

/**
 * Загрузка тикетов архива по типу фильтра
 */
async function loadArchiveTickets(type) {
    const container = document.getElementById('archiveCardsContainer');
    const noResultsMessage = document.getElementById('noResultsMessage');

    if (!container) return;

    // Показываем индикатор загрузки (опционально)
    container.innerHTML = '<div class="loading">Загрузка...</div>';

    try {
        const response = await fetch(`/api/archive/tickets?type=${type}`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Обновляем контейнер с карточками
        if (data.tickets_html && data.tickets_html.trim()) {
            container.innerHTML = data.tickets_html;
            if (noResultsMessage) {
                noResultsMessage.style.display = 'none';
            }
        } else {
            container.innerHTML = '';
            if (noResultsMessage) {
                noResultsMessage.style.display = 'flex';
            }
        }

        // Обновляем счётчики
        if (data.counts) {
            updateCounters(data.counts);
        }

        // Обновляем активную вкладку
        currentType = type;
        setActiveTab(type);

        // Переинициализируем кнопки "Создать похожую"
        if (window.initReopenButtons) {
            window.initReopenButtons();
        }

    } catch (err) {
        console.error('Ошибка загрузки архива:', err);
        container.innerHTML = '<div class="error">Ошибка загрузки заявок. Попробуйте обновить страницу.</div>';
    }
}

/**
 * Инициализация обработчиков вкладок
 */
function initTabs() {
    const tabs = document.querySelectorAll('#archiveTabs .button');

    if (tabs.length === 0) return;

    // Если только одна вкладка (user) — не вешаем обработчики переключения
    if (tabs.length === 1) {
        // Для user просто показываем все заявки
        return;
    }

    tabs.forEach(tab => {
        tab.addEventListener('click', async (e) => {
            e.preventDefault();
            const type = tab.dataset.type;
            if (!type || type === currentType) return;

            await loadArchiveTickets(type);
        });
    });
}

/**
 * Экспорт функций для использования в archivePage.js
 */
export function initArchiveTabs() {
    initTabs();
}

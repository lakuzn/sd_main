// js/archive/archiveTabs.js
let currentType = 'my';

function updateCounters(counts) {
    document.getElementById('count-my').textContent = counts.my || 0;
    document.getElementById('count-executor').textContent = counts.executor || 0;
    document.getElementById('count-all').textContent = counts.all || 0;
}

function renderCards(data) {
    const container = document.getElementById('archiveCardsContainer');
    const noResults = document.getElementById('noResultsMessage');
    const description = document.getElementById('archiveDescription');

    if (!container) return;

    if (!data.count || data.count === 0) {
        container.innerHTML = '';
        if (noResults) noResults.style.display = 'flex';
        if (description) description.textContent = 'Архивных заявок не найдено';
        return;
    }

    if (noResults) noResults.style.display = 'none';

    let html = '';
    if (data.my_html) {
        if (data.executor_html) html += '<h2 class="h2 content__subtitle">Мои обращения</h2>';
        html += data.my_html;
    }
    if (data.executor_html) {
        html += '<h2 class="h2 content__subtitle">Заявки, где я исполнитель</h2>';
        html += data.executor_html;
    }

    container.innerHTML = html;
    if (description && data.count !== undefined) {
        description.textContent = `Найдено заявок: ${data.count}`;
    }
}

async function loadArchiveTickets(type) {
    const container = document.getElementById('archiveCardsContainer');
    if (!container) return;

    container.innerHTML = '<div class="loader">Загрузка...</div>';

    try {
        const response = await fetch(`/api/archive/tickets?type=${type}`);
        const data = await response.json();

        updateCounters(data.counts || { my: 0, executor: 0, all: 0 });
        renderCards(data);
    } catch (err) {
        console.error('Ошибка загрузки архива:', err);
        container.innerHTML = '<li class="error">Не удалось загрузить архив</li>';
    }
}

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

function initTabs() {
    const tabs = document.querySelectorAll('#archiveTabs .button');
    if (!tabs.length) return;

    tabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            e.preventDefault();
            const type = tab.dataset.type;
            if (!type) return;

            currentType = type;
            setActiveTab(type);
            loadArchiveTickets(type);
        });
    });
}

export function initArchiveTabs() {
    initTabs();
    loadArchiveTickets('my');
}
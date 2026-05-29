export function initSearchFilter() {
    const queryText = window?.query_text;
    let currentType = 'all';

    function loadSearchResults(type) {
        currentType = type;
        const resultsContainer = document.getElementById('search-results');
        // Показываем спиннер (опционально)
        resultsContainer.innerHTML = '<div class="loader">Загрузка...</div>';

        fetch(`/search/filter?q=${encodeURIComponent(queryText)}&type=${type}`)
            .then(response => response.json())
            .then(data => {
                const hasAll = data.counts.all;
                const hasTickets = data.counts.tickets;
                const hasKnowledge = data.counts.knowledge;

                if (!hasAll) {
                    resultsContainer.innerHTML = `
                        <div class="content__noresults">
                            <p>
                                Не нашлось результатов с таким запросом.
                            </p>
                        </div>
                        `
                } else {
                    if (data.html_tickets && data.html_knowledge) {
                        resultsContainer.innerHTML = `
                            <div id="tickets-container">${data.html_tickets || ''}</div>
                            <div id="knowledge-container">${data.html_knowledge || ''}</div>
                            `;
                    } else if (data.html_tickets) {
                        resultsContainer.innerHTML = `
                            <div id="tickets-container">${data.html_tickets || ''}</div>
                            `;
                    } else if (data.html_knowledge) {
                        resultsContainer.innerHTML = `
                            <div id="knowledge-container">${data.html_knowledge || ''}</div>
                            `;
                    }

                    // Обновляем счётчики
                    document.getElementById('count-all').textContent = hasAll;
                    document.getElementById('count-tickets').textContent = hasTickets;
                    document.getElementById('count-knowledge').textContent = hasKnowledge;

                    // Обновляем активный класс кнопок
                    document.querySelectorAll('.search-filter .button').forEach(btn => {
                        btn.dataset.type === type
                            ? btn.classList.add('active')
                            : btn.classList.remove('active');
                    });
                }
            })
            .catch(err => {
                console.error('Ошибка загрузки:', err);
                document.getElementById('search-results').innerHTML = '<p class="error">Не удалось загрузить результаты</p>';
            });
    }

    document.querySelectorAll('.search-filter .button').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const type = btn.dataset.type;
            loadSearchResults(type);
        });
    });

    if (queryText)
        loadSearchResults('all');
}
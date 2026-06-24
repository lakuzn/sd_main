// export function initSearchPage() {
//     const queryText = window?.query_text;
//     let currentType = 'all';

//     function loadSearchResults(type) {
//         currentType = type;
//         const resultsContainer = document.getElementById('search-results');
//         // Показываем спиннер (опционально)
//         resultsContainer.innerHTML = '<div class="loader">Загрузка...</div>';

//         fetch(`/search/filter?q=${encodeURIComponent(queryText)}&type=${type}`)
//             .then(response => response.json())
//             .then(data => {
//                 const hasAll = data.counts.all;
//                 const hasTickets = data.counts.tickets;
//                 const hasKnowledge = data.counts.knowledge;

//                 if (!hasAll) {
//                     resultsContainer.innerHTML = `
//                         <div class="content__noresults">
//                             <p>
//                                 Не нашлось результатов с таким запросом.
//                             </p>
//                         </div>
//                         `
//                 } else {
//                     if (data.html_tickets && data.html_knowledge) {
//                         resultsContainer.innerHTML = `
//                             <div id="tickets-container">${data.html_tickets || ''}</div>
//                             <div id="knowledge-container">${data.html_knowledge || ''}</div>
//                             `;
//                     } else if (data.html_tickets) {
//                         resultsContainer.innerHTML = `
//                             <div id="tickets-container">${data.html_tickets || ''}</div>
//                             `;
//                     } else if (data.html_knowledge) {
//                         resultsContainer.innerHTML = `
//                             <div id="knowledge-container">${data.html_knowledge || ''}</div>
//                             `;
//                     }

//                     // Обновляем счётчики
//                     document.getElementById('count-all').textContent = hasAll;
//                     document.getElementById('count-tickets').textContent = hasTickets;
//                     document.getElementById('count-knowledge').textContent = hasKnowledge;

//                     // Обновляем активный класс кнопок
//                     document.querySelectorAll('.search-filter .button').forEach(btn => {
//                         btn.dataset.type === type
//                             ? btn.classList.add('active')
//                             : btn.classList.remove('active');
//                     });
//                 }
//             })
//             .catch(err => {
//                 console.error('Ошибка загрузки:', err);
//                 document.getElementById('search-results').innerHTML = '<p class="error">Не удалось загрузить результаты</p>';
//             });
//     }

//     document.querySelectorAll('.search-filter .button').forEach(btn => {
//         btn.addEventListener('click', (e) => {
//             e.preventDefault();
//             const type = btn.dataset.type;
//             loadSearchResults(type);
//         });
//     });

//     if (queryText)
//         loadSearchResults('all');
// }

// search/searchFilter.js
function renderSearchResults(data) {
    const container = document.getElementById('search-results');
    if (!container) return;

    const { counts, html_tickets, html_knowledge } = data;

    if (!counts.all) {
        container.innerHTML = `<div class="content__noresults"><p>Не нашлось результатов.</p></div>`;
        return;
    }

    let html = '';
    if (html_tickets) html += `<div id="tickets-container">${html_tickets}</div>`;
    if (html_knowledge) html += `<div id="knowledge-container">${html_knowledge}</div>`;
    container.innerHTML = html;

    // Обновить счетчики
    document.getElementById('count-all').textContent = counts.all;
    document.getElementById('count-tickets').textContent = counts.tickets || 0;
    document.getElementById('count-knowledge').textContent = counts.knowledge || 0;
}

function setActiveFilterButton(type) {
    document.querySelectorAll('.search-filter .button').forEach(btn => {
        btn.dataset.type === type ? btn.classList.add('active') : btn.classList.remove('active');
    });
}

async function loadSearchResults(query, type) {
    const container = document.getElementById('search-results');
    container.innerHTML = '<div class="loader">Загрузка...</div>';
    try {
        const response = await fetch(`/search/filter?q=${encodeURIComponent(query)}&type=${type}`);
        const data = await response.json();
        renderSearchResults(data);
        setActiveFilterButton(type);
    } catch (err) {
        console.error(err);
        container.innerHTML = '<p class="error">Не удалось загрузить результаты</p>';
    }
}

export function initSearchPage() {
    const queryText = window.query_text;
    if (!queryText) return;

    // Привязка кнопок
    document.querySelectorAll('.search-filter .button').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            loadSearchResults(queryText, btn.dataset.type);
        });
    });

    loadSearchResults(queryText, 'all');
}
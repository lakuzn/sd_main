import { initFiltersFaq } from "../modules/filtersFaq.js";
import { initTicketActions } from "../modules/ticketActions.js";
import { initChat } from "../chat/chat.js";
import { initFileUpload } from "../modules/fileUpload.js";
import { initDropdownNotification } from "../modules/dropdownNotification.js";
import { initReopenTicket } from "../modules/reopenTicket.js";
import { initTicketParams } from "../modules/ticketParams.js";
import { initFaqsActions } from "../modules/faqsActions.js";
import { initArticle } from "../modules/article.js";
import { initSocketDashboardTickets } from "../modules/dashboard.js";
import { initSearchFilter } from "../modules/search/searchFilter.js"

export async function initAllComponents() {
    initDropdownNotification();

    if (document.getElementById('create_ticket')) {
        initFileUpload();
    }
    else if (document.getElementById('ticket')) {
        initTicketActions();
        initChat();
        initTicketParams();
    }
    else if (document.getElementById('archive')) {
        initReopenTicket();
    }
    else if (document.getElementById('faqs')) {
        initFiltersFaq();
        initFaqsActions();
        initKBSocket();
    }
    else if (document.getElementById('article_create')) {
        initArticle();
    }
    else if (document.getElementById('dashboard')) {
        initSocketDashboardTickets();
    }
    else if (document.getElementById('search')) {
        initSearchFilter();
    }
}

function initKBSocket() {
    if (typeof io === 'undefined') return;

    const kbSocket = io();
    kbSocket.on('connect', () => {
        kbSocket.emit('join_kb');
    });

    kbSocket.on('kb_article_created', (data) => {
        addArticleToKBCatalog(data);
    });
}

function addArticleToKBCatalog(article) {
    // Ищем группу категории
    let group = null;
    document.querySelectorAll('.faqs-group').forEach(g => {
        const heading = g.querySelector('.faqs-group__category');
        if (heading && heading.textContent.trim() === article.category) {
            group = g;
        }
    });

    const articleHTML = `
        <a href="${article.url}" class="faqs-group__item">
            <p class="faqs-group__item-title">${article.title}</p>
            <time class="faqs-group__item-date">${article.updated_at}</time>
        </a>`;

    if (group) {
        const list = group.querySelector('.faqs-group__list');
        if (list) list.insertAdjacentHTML('afterbegin', articleHTML);
    } else {
        // Новая категория — добавляем группу
        const wrap = document.querySelector('.content__faqs');
        if (wrap) {
            const groupHTML = `
                <div class="faqs-group">
                    <h2 class="faqs-group__category h2">${article.category}</h2>
                    <div class="faqs-group__list">
                        ${articleHTML}
                    </div>
                </div>`;
            wrap.insertAdjacentHTML('beforeend', groupHTML);
        }
    }
}

// js/faq/kbSocket.js

import { escapeHtml } from "../common/utils.js";

export function initKBSocket() {
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
            <p class="faqs-group__item-title">${escapeHtml(article.title)}</p>
            <time class="faqs-group__item-date">${article.updated_at}</time>
        </a>`;

    if (group) {
        const list = group.querySelector('.faqs-group__list');
        if (list) list.insertAdjacentHTML('afterbegin', articleHTML);
    } else {
        const wrap = document.querySelector('.content__faqs');
        if (wrap) {
            const groupHTML = `
                <div class="faqs-group">
                    <h2 class="faqs-group__category h2">${escapeHtml(article.category)}</h2>
                    <div class="faqs-group__list">
                        ${articleHTML}
                    </div>
                </div>`;
            wrap.insertAdjacentHTML('beforeend', groupHTML);
        }
    }
}
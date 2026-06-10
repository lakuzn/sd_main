// js/dashboard/filterUtils.js
// (общие утилиты)
export function updateCardsContainer(html, count, hasFilters, originalDescription) {
    const cardsContainer = document.querySelector('.content__cards');
    const descriptionEl = document.querySelector('.content__description');
    const pagination = document.querySelector('.pagination');

    if (pagination) pagination.style.display = 'none';

    if (cardsContainer) {
        cardsContainer.innerHTML = count
            ? html
            : '<li class="noresults__title">Ничего не найдено</li>';
    }

    if (descriptionEl) {
        descriptionEl.textContent = hasFilters
            ? `Найдено заявок: ${count}`
            : originalDescription;
    }
}
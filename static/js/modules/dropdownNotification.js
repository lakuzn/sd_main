import { fetchReadNotifications } from "./api.js";

export function initDropdownNotification() {
    const button = document.querySelector('.notifications-button');
    const dropdownMenu = document.querySelector('.notifications-dropdown');
    const readAllButton = document.querySelector('.dropdown-header__button');
    const dropdownItems = document.querySelectorAll('.dropdown-item');

    if (!button || !dropdownMenu) return;

    dropdownMenu.style.display = 'none';
    button.setAttribute('aria-expanded', 'false');
    button.setAttribute('aria-haspopup', 'true');
    dropdownMenu.setAttribute('aria-label', 'Уведомления')
    dropdownItems.forEach((item) => item.setAttribute('role', 'menuitem'));

    function toggleDropdown(event) {
        event.stopPropagation();
        const isOpen = dropdownMenu.style.display === 'flex';
        isOpen ? closeDropdown() : openDropdown();
    }

    function openDropdown() {
        document.querySelectorAll('.dropdown').forEach(d => {
            if (d !== dropdownMenu) d.style.display = 'none';
        });

        dropdownMenu.style.display = 'flex';
        button.setAttribute('aria-expanded', 'true');
    }

    function closeDropdown() {
        dropdownMenu.style.display = 'none';
        button.setAttribute('aria-expanded', 'false');
    }

    button.addEventListener('click', toggleDropdown);

    button.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === '') {
            e.preventDefault();
            toggleDropdown();
        }

        if (e.key === 'Escape') closeDropdown();
    });

    document.addEventListener('click', function (e) {
        if (!dropdownMenu.contains(e.target) && !button.contains(e.target))
            closeDropdown();
    });


    if (readAllButton) {
        const badge = document.querySelector('.notifications__button-badge');
        const unreadItems = document.querySelectorAll('.dropdown-item__content--unchecked');


        readAllButton.addEventListener('click', () => {
            fetchReadNotifications(readAllButton, badge, unreadItems);
            closeDropdown();
        });
    }
}
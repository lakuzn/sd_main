function dropdownFaqsActions(buttonId, wrapperId) {
    const button = document.getElementById(buttonId);
    const wrapper = document.getElementById(wrapperId);

    if (!button || !wrapper) return null;

    function toggleDropdown(event) {
        event.stopPropagation();
        const isOpen = wrapper.style.display === 'flex';
        isOpen ? closeDropdown() : openDropdown();
    }

    function openDropdown() {
        document.querySelectorAll('.dropdown').forEach(d => {
            if (d !== wrapper) d.style.display = 'none';
        });

        wrapper.style.display = 'flex';
        button.setAttribute('aria-expanded', 'true');
    }

    function closeDropdown() {
        wrapper.style.display = 'none';
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
        if (!wrapper.contains(e.target) && !button.contains(e.target))
            closeDropdown();
    });
}

export async function initFaqsActions() {
    dropdownFaqsActions('dropdownTicketMore', 'dropdownTicketMoreList');
}
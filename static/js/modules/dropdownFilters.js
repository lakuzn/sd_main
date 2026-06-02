export function initDropdownFilters(listId, options, onSelect, placeholder = "Выберите...", hasAllOption = false, initialValue = null) {
    const list = document.getElementById(listId)
    if (!list) return null;

    const wrapper = list.parentElement;
    const button = wrapper.querySelector('.filters__dropdown-button');
    if (!button) return null;

    button.textContent = initialValue || placeholder;
    list.innerHTML = '';

    options.forEach(text => {
        const li = document.createElement('li');
        li.setAttribute('role', 'option');
        li.tabIndex = 0;
        li.textContent = text;
        li.classList.add('button', 'filters__dropdown-item');
        list.appendChild(li);

        li.addEventListener('click', () => selectOption(text, li));
        li.addEventListener('keydown', e => {
            if (e.key === 'Enter' || e.key == ' ') {
                e.preventDefault();
                selectOption(text, li);
            }
        });
    });

    function selectOption(text, selectedLi) {
        button.textContent = text;

        list.querySelectorAll('li').forEach(li => li.classList.remove('active'));
        if (selectedLi) selectedLi.classList.add('active');

        closeDropdown();
        if (onSelect) onSelect(text);
    }

    function setInitialActive() {
        if (!initialValue) {
            if (hasAllOption && options.length > 0) {
                const firstLi = list.querySelector('li');
                if (firstLi) firstLi.classList.add('active');
            }
            return;
        }

        const initialLi = Array.from(list.querySelectorAll('li')).find(li => li.textContent === initialValue);
        if (initialLi) {
            initialLi.classList.add('active');
        }
    }

    function openDropdown() {
        document.querySelectorAll('.filters__dropdown').forEach(d => {
            if (d !== wrapper) d.classList.remove('open');
        });
        wrapper.classList.add('open');
        button.setAttribute('aria-expanded', 'true');
    }

    function closeDropdown() {
        wrapper.classList.remove('open');
        button.setAttribute('aria-expanded', 'false');
    }

    button.addEventListener('click', e => {
        e.stopPropagation();
        const isOpen = wrapper.classList.contains('open');
        if (isOpen) closeDropdown();
        else openDropdown();
    });

    document.addEventListener('click', e => {
        if (!wrapper.contains(e.target)) closeDropdown();
    });

    button.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === '') {
            e.preventDefault();
            const isOpen = wrapper.classList.contains('open');
            if (isOpen) closeDropdown();
            else openDropdown();
        }
        if (e.key === 'Escape') closeDropdown();
    });

    function setDefaultActive() {
        if (hasAllOption && options.length > 0) {
            const firstLi = list.querySelector('li');
            if (firstLi) {
                firstLi.classList.add('active');
            }
        }
    }

    setDefaultActive();
    setInitialActive();

    return {
        setValue: (value) => {
            const li = Array.from(list.querySelectorAll('li')).find(l => l.textContent === value);
            if (li) selectOption(value, li);
        },
        reset: () => {
            button.textContent = placeholder;
            list.querySelectorAll('li').forEach(li => li.classList.remove('active'));
            setDefaultActive();
        }
    };
}
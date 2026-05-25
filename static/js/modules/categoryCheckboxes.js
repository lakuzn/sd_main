export function createCategoryCheckboxes(containerId, options, initialSelectedIds = [], onChange) {
    const container = document.getElementById(containerId);
    if (!container) return null;

    let currentSelected = initialSelectedIds;
    const originalSelected = currentSelected;

    function render() {
        const header = container.querySelector('.dropdown-header');
        container.innerHTML = '';
        if (header) container.appendChild(header);

        const listContainer = document.createElement('div');
        listContainer.className = 'dropdown-list';

        options.forEach(category => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'dropdown-item';

            const ul = document.createElement('ul');
            ul.className = 'ticket-category__list';

            const li = document.createElement('ul');
            li.className = 'ticket-category__header';

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `category_${category.id}`;
            checkbox.className = 'sr-only';
            checkbox.checked = currentSelected.includes(category.id);
            checkbox.value = category.id;

            const label = document.createElement('label');
            label.htmlFor = `category_${category.id}`;
            label.className = 'ticket-category__select ticket-category__select--header button';
            label.textContent = category.name;

            if (checkbox.checked) label.classList.add('checked');

            label.addEventListener('click', (e) => {
                e.preventDefault();
                checkbox.checked = !checkbox.checked;

                const event = new Event('change', { bubbles: true });
                checkbox.dispatchEvent(event);
            });

            checkbox.addEventListener('change', () => {
                if (checkbox.checked) {
                    if (!currentSelected.includes(category.id))
                        currentSelected.push(category.id);

                    label.classList.add('checked');
                } else {
                    currentSelected = currentSelected.filter(id => id !== category.id);
                    label.classList.remove('checked');
                }

                onChange?.([...currentSelected]);
            });

            li.appendChild(checkbox);
            li.appendChild(label);
            ul.appendChild(li);
            itemDiv.appendChild(ul);
            listContainer.appendChild(itemDiv);
        });

        container.appendChild(listContainer);
    }

    render();

    return {
        getValue: () => [...currentSelected],
        setValue: (newIds) => {
            currentSelected = [...newIds];
            render();
            if (onChange) onChange([...currentSelected]);
        },
        reset: () => {
            currentSelected = [...originalSelected];
            render();
            if (onChange) onChange([...currentSelected]);
        },
        getOriginalValue: () => [...originalSelected]
    }
}
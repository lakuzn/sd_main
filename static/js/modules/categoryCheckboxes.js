// categoryCheckboxes.js
export function createCategoryCheckboxes(containerId, allCategories, initialSelectedIds = [], onChange, selectedContainerId = null) {
    const container = document.getElementById(containerId);
    if (!container) return null;

    // Если передан контейнер для отображения выбранных категорий
    const selectedContainer = selectedContainerId ? selectedContainerId : null;

    let currentSelected = [...initialSelectedIds];
    const originalSelected = [...initialSelectedIds];

    // Функция обновления отображения выбранных категорий
    function updateSelectedDisplay() {
        if (!selectedContainer) return;

        if (currentSelected.length === 0) {
            selectedContainer.innerHTML = `
                <div class="categories-item">
                    <p class="categories-item__label">Не указаны</p>
                </div>
            `;
            return;
        }

        selectedContainer.innerHTML = '';
        currentSelected.forEach(id => {
            const category = allCategories.find(cat => cat.id === id);
            if (category) {
                const item = document.createElement('div');
                item.setAttribute('id', id);
                item.className = 'categories-item';
                item.innerHTML = `<p class="categories-item__label">${escapeHtml(category.name)}</p>`;
                selectedContainer.appendChild(item);
            }
        });
    }

    // Рендер чекбоксов
    function render() {
        // Сохраняем заголовок (если есть)
        const header = container.querySelector('.dropdown-header');
        container.innerHTML = '';
        if (header) container.appendChild(header);

        const listContainer = document.createElement('div');
        listContainer.className = 'dropdown-list';

        allCategories.forEach(category => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'dropdown-item';

            const ul = document.createElement('ul');
            ul.className = 'ticket-category__list';

            const li = document.createElement('li');
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
                    if (!currentSelected.includes(category.id)) {
                        currentSelected.push(category.id);
                    }
                    label.classList.add('checked');
                } else {
                    currentSelected = currentSelected.filter(id => id !== category.id);
                    label.classList.remove('checked');
                }
                updateSelectedDisplay();
                if (onChange) onChange([...currentSelected]);
            });

            li.appendChild(checkbox);
            li.appendChild(label);
            ul.appendChild(li);
            itemDiv.appendChild(ul);
            listContainer.appendChild(itemDiv);
        });

        container.appendChild(listContainer);
        updateSelectedDisplay();
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
        getOriginalValue: () => [...originalSelected],
        // Дополнительно обновить оригинальное значение (после сохранения)
        updateOriginal: () => {
            // не нужно для reload, но можно оставить
        }
    };
}

// Вспомогательная функция для безопасности
function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>]/g, function (m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}
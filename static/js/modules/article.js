import { fetchCategories } from "../api/api.js";

function dropdownArticleCategory(buttonId, listId, categoriesData, onChange) {
    const list = document.getElementById(listId)
    const button = document.getElementById(buttonId);

    if (!list || !button) return null;

    const wrapper = list.parentElement; // .dropdown
    let currentValue = categoriesData[0]?.name || '';
    let currentId = categoriesData[0]?.id || null;

    list.innerHTML = '';

    categoriesData.forEach(cat => {
        const li = document.createElement('li');
        li.setAttribute('role', 'option');
        li.classList.add('dropdown-item');
        li.dataset.categoryId = cat.id;

        const btn = document.createElement('button');
        btn.textContent = cat.name;
        btn.classList.add('button', 'dropdown-item__el');
        li.appendChild(btn);

        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            selectOption(cat.name, cat.id, li)
        });

        btn.addEventListener('keydown', e => {
            if (e.key === 'Enter' || e.key == ' ') {
                e.preventDefault();
                selectOption(cat.name, cat.id, li);
            }
        });

        list.appendChild(li);

    });

    if (categoriesData.length > 0) {
        button.textContent = categoriesData[0].name;
        currentId = categoriesData[0].id;

        const categoryIdInput = document.getElementById('category_id');
        if (categoryIdInput) categoryIdInput.value = currentId;
    }

    function selectOption(text, id, selectedLi) {
        if (currentValue === text) {
            closeDropdown();
            return;
        }

        currentValue = text;
        currentId = id;
        button.textContent = text;

        const categoryIdInput = document.getElementById('category_id');
        if (categoryIdInput) categoryIdInput.value = id;

        list.querySelectorAll('li').forEach(li => li.classList.remove('active'));
        if (selectedLi) selectedLi.classList.add('active');

        closeDropdown();

        if (onChange) onChange(currentValue);
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

    button.addEventListener('click', e => {
        e.stopPropagation();
        const isOpen = wrapper.style.display === 'flex';
        isOpen ? closeDropdown() : openDropdown();
    });

    button.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === '') {
            e.preventDefault();
            const isOpen = wrapper.style.display === 'flex';
            isOpen ? closeDropdown() : openDropdown();
        }
        if (e.key === 'Escape') closeDropdown();
    });

    document.addEventListener('click', e => {
        if (!wrapper.contains(e.target)) closeDropdown();
    });

    function setInitialActive() {
        button.textContent = currentValue;

        const initialLi = Array.from(list.querySelectorAll('li'))
            .find(li => li.textContent.trim() === currentValue);

        if (initialLi) initialLi.classList.add('active');
    }

    setInitialActive();

    return {
        getValue: () => ({ id: currentId, name: currentValue }),
        setValue: (id, name) => {
            const targetLi = Array.from(list.querySelectorAll('li'))
                .find(li => li.dataset.categoryId == id);

            if (targetLi) {
                list.querySelectorAll('li').
                    forEach(li => li.classList.remove('active'));
                targetLi.classList.add('active');

                currentValue = name;
                currentId = id;
                button.textContent = name;

                const categoryIdInput = document.getElementById('category_id');
                if (categoryIdInput) categoryIdInput.value = id;

                if (onChange) onChange(newValue);
            }
        },
    };
}

export async function initArticle() {
    const categories = await fetchCategories();

    const categoriesDropdown = dropdownArticleCategory(
        'articleCategory',
        'articleCategoryList',
        categories,
        (id, name) => { id, name }
    );
}
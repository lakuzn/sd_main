// js/forms/article.js
import { fetchCategories } from '../api/api.js';
import { createDropdown } from '../common/dropdown.js';

function initArticleCategoryDropdown(buttonId, listId, categoriesData, onChange) {
    const button = document.getElementById(buttonId);
    const list = document.getElementById(listId);

    if (!button || !list) return null;

    // Нормализуем категории в формат для createDropdown
    const options = categoriesData.map(cat => ({
        id: cat.id,
        name: cat.name
    }));

    const dropdown = createDropdown({
        button: button,
        list: list,
        options: options,
        placeholder: 'Выберите категорию',
        initialValue: options[0]?.id,
        returnObject: true,
        wrapperClass: 'dropdown',
        listItemClass: 'dropdown-item',
        onSelect: (selected) => {
            const categoryIdInput = document.getElementById('category_id');
            if (categoryIdInput) categoryIdInput.value = selected.id;
            if (onChange) onChange(selected.id, selected.name);
        }
    });

    // Устанавливаем начальное значение в скрытое поле
    const initialValue = dropdown.getValue();
    const categoryIdInput = document.getElementById('category_id');
    if (categoryIdInput && initialValue) {
        categoryIdInput.value = initialValue.id;
    }

    return dropdown;
}

export async function initArticleForm() {
    const categories = await fetchCategories();
    if (!categories || categories.length === 0) return;

    const categoriesDropdown = initArticleCategoryDropdown(
        'articleCategory',
        'articleCategoryList',
        categories,
        (id, name) => {
            id, name
            // можно добавить дополнительную логику при выборе
        }
    );
}
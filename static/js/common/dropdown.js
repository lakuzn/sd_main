// js/common/dropdown.js

/**
 * Универсальный дропдаун
 * @param {Object} config
 * @param {string|HTMLElement} config.button - ID кнопки или элемент кнопки
 * @param {string|HTMLElement} config.list - ID контейнера списка или элемент списка
 * @param {Array} config.options - массив опций (строки или объекты)
 * @param {Function} config.onSelect - callback при выборе (получает value, option)
 * @param {string} [config.placeholder='Выберите...'] - текст, если ничего не выбрано
 * @param {string|number|null} [config.initialValue=null] - начальное значение (строка или id)
 * @param {string} [config.displayKey='name'] - если options - объекты, поле для отображения
 * @param {string} [config.valueKey='id'] - если options - объекты, поле для значения
 * @param {boolean} [config.returnObject=false] - возвращать ли объект { id, name } вместо value
 * @param {string} [config.wrapperClass='dropdown'] - класс обёртки (для поиска родителя)
 * @param {string|string[]} [config.listItemClass='dropdown-item'] - класс элемента списка 
 * @param {boolean} [config.closeOnSelect=true] - закрывать дропдаун после выбора
 * @param {Function} [config.onUpdate]   // вызывается при изменении значения (получает value, option)
 */
export function createDropdown(config) {
    const {
        button: buttonIdOrElement,
        list: listIdOrElement,
        options,
        onSelect,
        placeholder = 'Выберите...',
        initialValue = null,
        displayKey = 'name',
        valueKey = 'id',
        returnObject = false,
        wrapperClass = 'dropdown',
        listItemClass = 'dropdown-item',
        closeOnSelect = true,
        onUpdate
    } = config;

    // Получаем элементы
    const button = typeof buttonIdOrElement === 'string'
        ? document.getElementById(buttonIdOrElement)
        : buttonIdOrElement;

    const list = typeof listIdOrElement === 'string'
        ? document.getElementById(listIdOrElement)
        : listIdOrElement;

    if (!button || !list) {
        console.error('Dropdown: button or list not found', config);
        return null;
    }

    // Определяем обёртку (ближайший родитель с классом wrapperClass)
    let wrapper = list.parentElement;
    while (wrapper && !wrapper.classList.contains(wrapperClass)) {
        wrapper = wrapper.parentElement;
    }
    if (!wrapper) wrapper = list; // fallback

    // Нормализуем опции в единый массив объектов { id, name }
    const normalizedOptions = options.map(opt => {
        if (typeof opt === 'string') {
            return { id: opt, name: opt };
        }
        return {
            id: opt[valueKey],
            name: opt[displayKey]
        };
    });

    // Поиск значения по id или по name
    let currentOption = null;
    if (initialValue !== null && initialValue !== undefined) {
        if (typeof initialValue === 'object' && initialValue.id) {
            currentOption = normalizedOptions.find(o => o.id == initialValue.id);
        } else {
            // сначала ищем по id, потом по name
            currentOption = normalizedOptions.find(o => o.id == initialValue)
                || normalizedOptions.find(o => o.name === initialValue);
        }
    }
    if (!currentOption && normalizedOptions.length > 0) {
        currentOption = normalizedOptions[0];
    }

    let currentValue = currentOption ? currentOption.id : null;
    let currentDisplay = currentOption ? currentOption.name : placeholder;

    const originalValue = currentValue;
    const originalDisplay = currentDisplay;

    // Рендерим список опций
    function renderList() {
        const listItemClasses = Array.isArray(listItemClass)
            ? listItemClass
            : listItemClass.split(/\s+/).filter(c => c);

        list.innerHTML = '';
        normalizedOptions.forEach(opt => {
            const li = document.createElement('li');
            li.setAttribute('role', 'option');
            // Добавляем базовые классы + пользовательские + уникальный класс-маркер
            li.classList.add('button', ...listItemClasses, 'dropdown-item__option');
            li.dataset.value = opt.id;
            li.textContent = opt.name;

            li.addEventListener('click', (e) => {
                e.stopPropagation();
                selectOption(opt);
            });

            li.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    selectOption(opt);
                }
            });

            list.appendChild(li);
        });

        // Устанавливаем активный элемент
        updateActiveItem();
    }

    function updateActiveItem() {
        const items = list.querySelectorAll('.dropdown-item__option');
        items.forEach(item => {
            const val = item.dataset.value;
            val == currentValue
                ? item.classList.add('active')
                : item.classList.remove('active');
        });
    }

    function selectOption(option) {
        if (currentValue === option.id) {
            if (closeOnSelect) closeDropdown();
            return;
        }

        currentValue = option.id;
        currentDisplay = option.name;
        button.textContent = currentDisplay;

        updateActiveItem();

        if (onUpdate) {
            const returnVal = returnObject ? { id: option.id, name: option.name } : option.id;
            onUpdate(returnVal, option);
        }

        if (closeOnSelect) closeDropdown();

        const returnVal = returnObject ? { id: option.id, name: option.name } : option.id;
        if (onSelect) onSelect(returnVal, option);
    }

    // Управление видимостью
    function openDropdown() {
        // Закрыть все другие дропдауны
        document.querySelectorAll(`.${wrapperClass}`).forEach(d => {
            if (d !== wrapper) d.style.display = 'none';
        });
        wrapper.style.display = 'flex';
        button.setAttribute('aria-expanded', 'true');
    }

    function closeDropdown() {
        wrapper.style.display = 'none';
        button.setAttribute('aria-expanded', 'false');
    }

    function toggleDropdown(e) {
        e.stopPropagation();
        const isOpen = wrapper.style.display === 'flex';
        isOpen ? closeDropdown() : openDropdown();
    }

    // Обработчики кнопки
    button.addEventListener('click', toggleDropdown);
    button.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            toggleDropdown(e);
        }
        if (e.key === 'Escape') closeDropdown();
    });

    // Закрытие при клике вне
    document.addEventListener('click', (e) => {
        if (!wrapper.contains(e.target)) closeDropdown();
    });

    // Инициализация отображения
    button.textContent = currentDisplay;
    renderList();

    // API
    return {
        getValue: () => returnObject ? { id: currentValue, name: currentDisplay } : currentValue,
        setValue: (val) => {
            let targetOption;
            if (typeof val === 'object' && val.id) {
                targetOption = normalizedOptions.find(o => o.id == val.id);
            } else {
                targetOption = normalizedOptions.find(o => o.id == val) || normalizedOptions.find(o => o.name === val);
            }
            if (targetOption) {
                selectOption(targetOption);
            }
        },
        reset: () => {
            currentValue = originalValue;
            currentDisplay = originalDisplay;
            button.textContent = currentDisplay;
            updateActiveItem();
            if (onSelect) {
                const returnVal = returnObject ? { id: currentValue, name: currentDisplay } : currentValue;
                onSelect(returnVal);
            }
        },
        open: openDropdown,
        close: closeDropdown,
        getOriginalValue: () => returnObject ? { id: originalValue, name: originalDisplay } : originalValue
    };
}

/**
 * Простая функция для открытия/закрытия дропдауна
 * @param {string} buttonId - ID кнопки-триггера
 * @param {string} listId - ID контейнера списка
 */
export function initDropdownToggle(buttonId, wrapperId) {
    const button = document.getElementById(buttonId);
    const wrapper = document.getElementById(wrapperId);

    if (!button || !wrapper) return;

    function toggle(e) {
        e.stopPropagation();
        const isOpen = wrapper.style.display === 'flex';
        isOpen ? close() : open();
    }

    function open() {
        document.querySelectorAll('.dropdown').forEach(d => {
            if (d !== wrapper) d.style.display = 'none';
        });

        wrapper.style.display = 'flex';
        button.setAttribute('aria-expanded', 'true');
    }

    function close() {
        wrapper.style.display = 'none';
        button.setAttribute('aria-expanded', 'false');
    }

    button.addEventListener('click', toggle);

    button.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            toggle(e);
        }
        if (e.key === 'Escape') close();
    });

    document.addEventListener('click', (e) => {
        if (!wrapper.contains(e.target) && !button.contains(e.target)) close();
    });

    // API
    return {
        open,
        close,
        toggle
    };
}

import { fetchTicketParamsOptions, fetchChangeTicketParams } from "./api.js"
import { createCategoryCheckboxes } from "./categoryCheckboxes.js";

function dropdownChangeTicketPriority(buttonId, listId, options, initialValue, onChange) {
    const list = document.getElementById(listId)
    if (!list) return null;

    const wrapper = list.parentElement; // .dropdown
    const button = document.getElementById(buttonId);

    if (!button) return null;

    const valueDisplay = button.querySelector('span') || button;
    let currentValue = (initialValue && options.includes(initialValue))
        ? initialValue : 'Без приоритета';

    const originalValue = currentValue;

    list.innerHTML = '';

    options.forEach(opt => {
        const li = document.createElement('li');
        li.setAttribute('role', 'option');
        li.classList.add('dropdown-item');
        const btn = document.createElement('button');
        btn.textContent = opt;
        btn.classList.add('button', 'dropdown-item__el');
        li.appendChild(btn);
        list.appendChild(li);

        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            selectOption(opt, li)
        });

        btn.addEventListener('keydown', e => {
            if (e.key === 'Enter' || e.key == ' ') {
                e.preventDefault();
                selectOption(opt, li);
            }
        });
    });

    function selectOption(text, selectedLi) {
        if (currentValue === text) {
            closeDropdown();
            return;
        }

        currentValue = text;
        valueDisplay.textContent = text;

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
        valueDisplay.textContent = currentValue;

        const initialLi = Array.from(list.querySelectorAll('li'))
            .find(li => li.textContent.trim() === currentValue);

        if (initialLi) initialLi.classList.add('active');
    }

    setInitialActive();

    return {
        getValue: () => currentValue,
        setValue: (newValue) => {
            if (options.includes(newValue)) {
                currentValue = newValue;
                valueDisplay.textContent = newValue;

                const targetLi = Array.from(list.querySelectorAll('li'))
                    .find(li => li.textContent.trim() === newValue);

                if (targetLi) {
                    list.querySelectorAll('li').
                        forEach(li => li.classList.remove('active'));
                    targetLi.classList.add('active');
                }

                if (onChange) onChange(newValue);
            }
        },
        reset: () => {
            currentValue = originalValue;
            valueDisplay.textContent = originalValue;

            const originalLi = Array.from(list.querySelectorAll('li'))
                .find(li => li.textContent.trim() === originalValue);

            if (originalLi) {
                list.querySelectorAll('li').
                    forEach(li => li.classList.remove('active'));
                originalLi.classList.add('active');
            } else {
                list.querySelectorAll('li').
                    forEach(li => li.classList.remove('active'));
            }
        },
        getOriginalValue: () => originalValue
    };
}

function dropdownTicketInfo(buttonId, wrapperId) {
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

function parseToJson(rawData) {
    if (!rawData) return [];

    try {
        const parsed = JSON.parse(rawData);
        return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
        console.warn('Не удалось распарсить строку:', rawData);
        return [];
    }
}

function markAsChanged(field, newValue) {
    const originalValue = originalParams[field];
    let isChanged;

    if (Array.isArray(originalValue) && Array.isArray(newValue))
        isChanged = JSON.stringify(originalValue)
            !== JSON.stringify(newValue);
    else
        isChanged = originalValue !== newValue;


    if (!isChanged) delete changedParams[field];
    else changedParams[field] = newValue;

    const hasChanges = Object.keys(changedParams).length > 0;
    if (applyButton) applyButton.style.display = hasChanges ? 'flex' : 'none';
    if (cancelButton) cancelButton.style.display = hasChanges ? 'flex' : 'none';
}

function getExecutorData(executorId) {
    const executorEl = document.querySelector(`.js-executor-item[id="${executorId}"]`);
    if (!executorEl) return null;

    const dropdownItem = executorEl.closest('.dropdown-item');
    if (!dropdownItem) return null;

    const fullName = dropdownItem.querySelector('.ticket-person__label')?.textContent || '';

    // Инициалы
    const nameParts = fullName.trim().split(' ');
    const initials = (nameParts[0][0] || '') + (nameParts[1][0] || '');

    return {
        id: executorId,
        full_name: fullName,
        initials: initials,
    }
}

function renderExecutorItem(executor) {
    return `
        <div id="${executor.id}" class="ticket-person">
            <!-- <img src="" alt=""> -->
            <span class="ticket-person__img ticket-person__img--executor">
                ${executor.initials}
            </span>
            <p class="ticket-person__label">
                ${executor.full_name}
            </p>
        </div>
    `;
}

function updateTicketExecutors() {
    if (!ticketExecutorsContainer) return;

    if (!selectedExecutors.length) {
        ticketExecutorsContainer.innerHTML =
            ' <p class="ticket-person__label">Исполнитель не назначен</p>';
        return
    }

    ticketExecutorsContainer.innerHTML = '';
    selectedExecutors.forEach(id => {
        const executor = getExecutorData(id);

        if (executor)
            ticketExecutorsContainer.insertAdjacentHTML('beforeend',
                renderExecutorItem(executor));
    });
}

function updateDropdownSelection() {
    const executors = document.querySelectorAll('#dropdownTicketExecutorList .dropdown-item');
    executors.forEach(item => {
        const person = item.querySelector('.ticket-person');
        if (!person) return;

        const execId = parseInt(item.querySelector('.js-executor-item')?.id);

        selectedExecutors.includes(execId) ? person.classList.add('selected') : person.classList.remove('selected');
    });
}

function initExecutors() {
    selectedExecutors = parseToJson(window.currentTicket?.executor_ids || []);
    updateDropdownSelection();
    updateTicketExecutors();

    const executorItemsList = document.querySelectorAll('#dropdownTicketExecutorList .js-executor-item');
    executorItemsList.forEach(item => {
        item.addEventListener('click', (e) => {
            e.stopPropagation();

            const execId = parseInt(item.id);
            if (isNaN(execId)) return;

            const index = selectedExecutors.indexOf(execId);
            if (index !== -1) {
                selectedExecutors.splice(index, 1);
                item.classList.remove('selected');
            } else {
                selectedExecutors.push(execId);
                item.classList.add('selected');
            }

            updateTicketExecutors();
            markAsChanged('executor_ids', [...selectedExecutors]);
        });
    });
}

async function initPriority() {
    const options = await fetchTicketParamsOptions();

    priorityDropdown = dropdownChangeTicketPriority(
        'changeTicketPriorityBtn',
        'changeTicketPriorityList',
        options.priorities,
        window.currentTicket?.priority,
        (newValue) => markAsChanged('priority', newValue)
    );
}

async function initCategories() {
    const options = await fetchTicketParamsOptions();

    categoryCheckboxes = createCategoryCheckboxes(
        'dropdownTicketCategoryList',
        options.categories,
        parseToJson(window.currentTicket?.category_ids || []),
        (newIds) => markAsChanged('categories', newIds)
    )
}

function initDocumentNumber() {
    const docNumberInput = document.getElementById('documentNumber');
    if (docNumberInput) {
        docNumberInput.addEventListener('input', (e) => {
            markAsChanged('document_number', e.target.value.trim());
        });
    }
}

function initDeadline() {
    const deadlineInput = document.getElementById('ticketTime');
    if (deadlineInput) {
        deadlineInput.addEventListener('change', (e) => {
            markAsChanged('desired_deadline', e.target.value || null);
        });
    }
}

async function applyChanges() {
    if (Object.keys(changedParams).length === 0) return;

    const success = await fetchChangeTicketParams(changedParams, applyButton);
    if (success) {
        for (const [field, newValue] of Object.entries(changedParams))
            originalParams[field] = newValue;

        resetAllFields();
        window.location.reload();
    }
}

function resetAllFields() {
    if (priorityDropdown && priorityDropdown.reset) priorityDropdown.reset();
    if (categoryCheckboxes && categoryCheckboxes.reset) categoryCheckboxes.reset();

    selectedExecutors = originalParams.executor_ids ? [...originalParams.executor_ids] : [];
    updateTicketExecutors();

    if (docNumberInput) docNumberInput.value = originalParams.document_number || '';
    if (deadlineInput) deadlineInput.value = originalParams.desired_deadline || '';

    changedParams = {};
    if (applyButton) applyButton.style.display = 'none'
    if (cancelButton) cancelButton.style.display = 'none'
}

function disableEditFields() {
    if (applyButton) applyButton.style.display = 'none';
    if (cancelButton) cancelButton.style.display = 'none';

    if (docNumberInput) docNumberInput.disabled = true;
    if (deadlineInput) deadlineInput.disabled = true;


}

let priorityDropdown = null;
let categoryCheckboxes = null;
let selectedExecutors = [];
let changedParams = {};
let originalParams = {};

const ticketExecutorsContainer = document.querySelector('.ticket-executors');
const applyButton = document.getElementById('ticketChangeParams');
const cancelButton = document.getElementById('ticketChangeParamsCancel');
const docNumberInput = document.getElementById('documentNumber');
const deadlineInput = document.getElementById('ticketTime');


export async function initTicketParams() {
    originalParams = {
        priority: window.currentTicket?.priority || null,
        categories: window.currentTicket?.category_ids || [],
        executor_ids: parseToJson(window.currentTicket?.executor_ids || []),
        document_number: document.getElementById('documentNumber')?.value.trim(),
        desired_deadline: document.getElementById('ticketTime')?.value || null
    }

    await initPriority();
    await initCategories();
    initExecutors();
    initDocumentNumber();
    initDeadline();

    if (applyButton) applyButton.addEventListener('click', applyChanges);
    if (cancelButton) cancelButton.addEventListener('click', resetAllFields);

    dropdownTicketInfo('dropdownTicketSender', 'dropdownTicketSenderList');
    dropdownTicketInfo('dropdownTicketExecutor', 'dropdownTicketExecutorList');
    dropdownTicketInfo('dropdownTicketCategory', 'dropdownTicketCategoryList');
    dropdownTicketInfo('dropdownTicketMore', 'dropdownTicketMoreList');
}

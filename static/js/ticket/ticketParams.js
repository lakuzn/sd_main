// js/ticketParams.js
import { fetchTicketParamsOptions, fetchChangeTicketParams } from '../api/api.js';
import { initDropdownToggle } from '../common/dropdown.js';
import { parseToJson } from '../common/utils.js';
import { createChangeTracker } from '../common/changeTracker.js';
import { initPriorityDropdown } from './priorityManager.js';
import { initCategoriesManager } from './categoriesManager.js';
import { initDepartmentsManager } from './departmentsManager.js';
import { initExecutorsManager } from './executorsManager.js';


export async function initTicketParams() {
    const editableRoles = ['admin', 'classifier', 'head'];
    const canEdit = editableRoles.includes(window.currentUserRole);

    const classifierCanEdit =
        (window.currentTicket?.status === 'Новая'
            || window.currentTicket?.status === 'В обработке')
        && window.currentUserRole === 'classifier';

    // 1. Всегда инициализируем дропдауны для просмотра (заявитель, исполнители readonly, Ещё)
    initDropdownToggle('dropdownTicketSender', 'dropdownTicketSenderList');
    initDropdownToggle('dropdownTicketExecutorUser', 'dropdownTicketExecutorListUser');
    initDropdownToggle('dropdownTicketMore', 'dropdownTicketMoreList');

    // Если пользователь не может редактировать – дальше ничего не делаем
    if (!canEdit || (!classifierCanEdit)) return;

    // 2. Исходные значения для трекера
    const originalParams = {
        priority: window.currentTicket?.priority || null,
        categories: parseToJson(window.currentTicket?.category_ids || []),
        executor_ids: parseToJson(window.currentTicket?.executor_ids || []),
        department_ids: parseToJson(window.currentTicket?.department_ids || []),
        document_number: document.getElementById('documentNumber')?.value.trim() || '',
        desired_deadline: document.getElementById('ticketTime')?.value || null
    };

    // 3. Трекер изменений (кнопки Применить/Отмена)
    const applyBtn = document.getElementById('ticketChangeParams');
    const cancelBtn = document.getElementById('ticketChangeParamsCancel');
    const changeTracker = createChangeTracker({
        applyButton: applyBtn,
        cancelButton: cancelBtn,
        originalParams
    });

    // 4. Загружаем опции с сервера
    const options = await fetchTicketParamsOptions();
    if (!options) return;

    // 5. Приоритет (редактируемый дропдаун)
    const priorityDropdown = initPriorityDropdown({
        buttonId: 'changeTicketPriorityBtn',
        listId: 'changeTicketPriorityList',
        priorities: options.priorities,
        initialValue: originalParams.priority,
        onChange: (newVal) => changeTracker.markAsChanged('priority', newVal)
    });

    // 6. Категории (чекбоксы + отображение выбранных)
    //    Сначала инициализируем дропдаун для кнопки категорий
    initDropdownToggle('dropdownTicketCategory', 'dropdownTicketCategoryList');
    const categoriesManager = initCategoriesManager({
        checkboxContainerId: 'dropdownTicketCategoryList',
        displayContainer: document.getElementById('dropdownTicketCategory'),
        categories: options.categories,
        initialSelectedIds: originalParams.categories,
        onChange: (newIds) => changeTracker.markAsChanged('categories', newIds)
    });

    // 7. Отделы (аналогично)
    initDropdownToggle('dropdownTicketDept', 'dropdownTicketDeptList');
    let executorsManager = null; // будет инициализирован позже
    const departmentsManager = initDepartmentsManager({
        checkboxContainerId: 'dropdownTicketDeptList',
        displayContainer: document.getElementById('dropdownTicketDept'),
        departments: options.departments,
        initialSelectedIds: originalParams.department_ids,
        onChange: (newIds) => changeTracker.markAsChanged('department_ids', newIds),
        enableSearch: true,
        searchInputId: 'deptSearch',
        onMutualExclusion: () => {
            if (executorsManager && executorsManager.getValue().length > 0) {
                executorsManager.setValue([]);
                changeTracker.markAsChanged('executor_ids', []);
            }
        }
    });

    // 8. Исполнители (редактируемый блок)
    initDropdownToggle('dropdownTicketExecutor', 'dropdownTicketExecutorList');
    executorsManager = initExecutorsManager({
        displayContainer: document.querySelector('.ticket-executors'),
        dropdownListId: 'dropdownTicketExecutorList',
        initialExecutorIds: originalParams.executor_ids,
        onChange: (newIds) => {
            changeTracker.markAsChanged('executor_ids', newIds);
            if (newIds.length > 0 && departmentsManager.getValue().length > 0) {
                departmentsManager.setValue([]);
                changeTracker.markAsChanged('department_ids', []);
            }
        },
        enableSearch: true,
        searchInputId: 'executorSearch'
    });

    // 9. Простые поля (номер документа, срок)
    const docInput = document.getElementById('documentNumber');
    if (docInput) {
        docInput.addEventListener('input', (e) => {
            changeTracker.markAsChanged('document_number', e.target.value.trim());
        });
    }
    const deadlineInput = document.getElementById('ticketTime');
    if (deadlineInput) {
        deadlineInput.addEventListener('change', (e) => {
            changeTracker.markAsChanged('desired_deadline', e.target.value || null);
        });
    }

    // 10. Кнопка "Применить"
    if (applyBtn) {
        applyBtn.addEventListener('click', async () => {
            const changed = changeTracker.getChangedParams();
            if (Object.keys(changed).length === 0) return;
            const success = await fetchChangeTicketParams(changed, applyBtn);
            if (success) {
                changeTracker.syncOriginal();
                window.location.reload(); // или обновить данные без перезагрузки
            }
        });
    }

    // 11. Кнопка "Отмена"
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            const original = changeTracker.resetAllFields();
            priorityDropdown?.setValue(original.priority);
            categoriesManager?.setValue(original.categories);
            departmentsManager?.setValue(original.department_ids);
            executorsManager?.setValue(original.executor_ids);
            if (docInput) docInput.value = original.document_number;
            if (deadlineInput) deadlineInput.value = original.desired_deadline;
        });
    }
}

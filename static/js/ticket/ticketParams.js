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
    const isResolved = window.currentTicket?.status === 'Решена';
    const canEditFull = editableRoles.includes(window.currentUserRole) && !isResolved;

    // 1. Всегда инициализируем дропдауны для просмотра (заявитель, исполнители readonly, Ещё)
    initDropdownToggle('dropdownTicketSender', 'dropdownTicketSenderList');
    initDropdownToggle('dropdownTicketExecutorUser', 'dropdownTicketExecutorListUser');
    initDropdownToggle('dropdownTicketMore', 'dropdownTicketMoreList');

    // Исполнитель может править только Host Name и номер документа (например, когда
    // машина не включается и host name заранее неизвестен). Признак — наличие
    // редактируемого поля #hostName в разметке (рендерится для исполнителя заявки).
    const docInput = document.getElementById('documentNumber');
    const hostInput = document.getElementById('hostName');
    const canEditMeta = canEditFull || !!hostInput;

    // Если пользователь не может редактировать – дальше ничего не делаем
    if (!canEditMeta) return;
    // 2. Исходные значения для трекера
    const originalParams = {
        priority: window.currentTicket?.priority || null,
        categories: parseToJson(window.currentTicket?.category_ids || []),
        executor_ids: parseToJson(window.currentTicket?.executor_ids || []),
        department_ids: parseToJson(window.currentTicket?.department_ids || []),
        document_number: document.getElementById('documentNumber')?.value.trim() || '',
        host_name: document.getElementById('hostName')?.value.trim() || '',
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

    // Менеджеры приоритета / категорий / отделов / исполнителей — только для
    // персонала (классификатор / начальник / админ).
    let priorityDropdown = null;
    let categoriesManager = null;
    let departmentsManager = null;
    let executorsManager = null;

    if (canEditFull) {
        // 4. Загружаем опции с сервера
        const options = await fetchTicketParamsOptions();
        if (options) {
            // 5. Приоритет (редактируемый дропдаун)
            priorityDropdown = initPriorityDropdown({
                buttonId: 'changeTicketPriorityBtn',
                listId: 'changeTicketPriorityList',
                priorities: options.priorities,
                initialValue: originalParams.priority,
                onChange: (newVal) => changeTracker.markAsChanged('priority', newVal)
            });

            // 6. Категории (чекбоксы + отображение выбранных)
            initDropdownToggle('dropdownTicketCategory', 'dropdownTicketCategoryList');
            categoriesManager = initCategoriesManager({
                checkboxContainerId: 'dropdownTicketCategoryList',
                displayContainer: document.getElementById('dropdownTicketCategory'),
                categories: options.categories,
                initialSelectedIds: originalParams.categories,
                onChange: (newIds) => changeTracker.markAsChanged('categories', newIds)
            });

            // 7. Отделы (аналогично)
            initDropdownToggle('dropdownTicketDept', 'dropdownTicketDeptList');
            departmentsManager = initDepartmentsManager({
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
        }
    }

    // 9. Простые поля: номер документа и Host Name (доступны и исполнителю)
    if (docInput) {
        docInput.addEventListener('input', (e) => {
            changeTracker.markAsChanged('document_number', e.target.value.trim());
        });
    }
    if (hostInput) {
        hostInput.addEventListener('input', (e) => {
            changeTracker.markAsChanged('host_name', e.target.value.trim());
        });
    }

    // Срок решения может менять только персонал
    const deadlineInput = canEditFull ? document.getElementById('ticketTime') : null;
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
            if (hostInput) hostInput.value = original.host_name;
            if (deadlineInput) deadlineInput.value = original.desired_deadline;
        });
    }
}

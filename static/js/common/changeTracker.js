// js/common/changeTracker.js

/**
 * Создаёт трекер изменений для формы
 * @param {Object} config
 * @param {HTMLElement} config.applyButton - кнопка "Применить"
 * @param {HTMLElement} config.cancelButton - кнопка "Отмена"
 * @param {Object} config.originalParams - исходные значения параметров
 * @param {Function} [config.onChange] - колбэк при любом изменении (опционально)
 * @returns {Object} API трекера
 */
export function createChangeTracker({ applyButton, cancelButton, originalParams, onChange }) {
    // Копируем исходные значения (защита от мутаций)
    const original = JSON.parse(JSON.stringify(originalParams));
    let changed = {};

    // Вспомогательная функция сравнения значений
    function isEqual(a, b) {
        if (Array.isArray(a) && Array.isArray(b)) {
            return JSON.stringify(a) === JSON.stringify(b);
        }
        if (typeof a === 'object' && a !== null && typeof b === 'object' && b !== null) {
            return JSON.stringify(a) === JSON.stringify(b);
        }
        return a === b;
    }

    // Обновление видимости кнопок
    function updateActionButtons() {
        const hasChanges = Object.keys(changed).length > 0;
        if (applyButton) applyButton.style.display = hasChanges ? 'flex' : 'none';
        if (cancelButton) cancelButton.style.display = hasChanges ? 'flex' : 'none';
    }

    /**
     * Отмечает поле как изменённое
     * @param {string} field
     * @param {any} newValue
     */
    function markAsChanged(field, newValue) {
        const originalValue = original[field];
        const isChanged = !isEqual(originalValue, newValue);

        if (!isChanged) {
            delete changed[field];
        } else {
            changed[field] = JSON.parse(JSON.stringify(newValue)); // копия
        }

        updateActionButtons();
        if (onChange) onChange(changed);
    }

    /**
     * Сбрасывает все изменения до исходных значений
     * @returns {Object} исходные значения
     */
    function resetAllFields() {
        changed = {};
        updateActionButtons();
        if (onChange) onChange(changed);
        return JSON.parse(JSON.stringify(original));
    }

    /**
     * Синхронизирует original с текущими changed (после успешного сохранения)
     */
    function syncOriginal() {
        for (const [field, value] of Object.entries(changed)) {
            original[field] = JSON.parse(JSON.stringify(value));
        }
        changed = {};
        updateActionButtons();
        if (onChange) onChange(changed);
    }

    /**
     * Возвращает текущие изменённые параметры
     */
    function getChangedParams() {
        return { ...changed };
    }

    /**
     * Проверяет, есть ли изменения
     */
    function hasChanges() {
        return Object.keys(changed).length > 0;
    }

    /**
     * Возвращает исходные значения (копию)
     */
    function getOriginalParams() {
        return JSON.parse(JSON.stringify(original));
    }

    /**
     * Обновляет исходные значения для поля (например, после загрузки новых данных)
     */
    function updateOriginalField(field, newValue) {
        original[field] = JSON.parse(JSON.stringify(newValue));
        // Если это поле было в changed – удаляем его
        if (changed[field] !== undefined) {
            delete changed[field];
            updateActionButtons();
            if (onChange) onChange(changed);
        }
    }

    return {
        markAsChanged,
        resetAllFields,
        syncOriginal,
        getChangedParams,
        hasChanges,
        getOriginalParams,
        updateOriginalField,
        // Для прямого доступа к кнопкам (если нужно)
        updateActionButtons
    };
}

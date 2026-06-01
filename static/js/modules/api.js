function getCSRFToken() {
    const csrfToken = document.querySelector('meta[name="csrf_token"]').getAttribute('content');
    return csrfToken || '';
}

// Временнон хранилище файлов
let fileUploadClearFn = null;

export function setFileUploadClearFn(fn) {
    fileUploadClearFn = fn;
}

export async function fetchFilterOptions() {
    try {
        const response = await fetch('/api/filters/options');
        if (!response.ok) throw new Error('Не удалось загрузить опции');
        const data = await response.json();

        return {
            categories: data.categories || [],
            priorities: data.priorities || [],
            statuses: data.statuses || []
        };
    } catch (error) {
        console.error('Ошибка загрузки опций фильтров:', error);

        // fallback
        return {
            categories: ['Оборудование', 'ПО', 'Почта', 'Документооборот'],
            priorities: ['Высокий', 'Средний', 'Низкий'],
            statuses: ['В работе', 'Новая', 'Решена', 'Ожидает ответа', 'В обработке', 'Требует проверки']
        }
    };
}

export async function fetchCategories() {
    try {
        const response = await fetch('/api/categories');
        if (!response.ok) throw new Error('Не удалось загрузить категории');
        const data = await response.json();

        return data.categories || [];
    } catch (error) {
        console.error('Ошибка загрузки категорий:', error);

        // fallback
        return ['Оборудование', 'ПО', 'Почта', 'Документооборот'];
    };
}

export async function fetchTicketParamsOptions() {
    try {
        const response = await fetch('/api/ticket/params');
        if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        const data = await response.json();
        return {
            categories: data.categories || [],
            priorities: data.priorities || [],
            statuses: data.statuses || [],
            executors: data.executors || [],
            departments: data.departments || []
        };
    } catch (error) {
        console.error('Ошибка загрузки опций параметров:', error);

        // fallback
        return null;
    };
}

export async function fetchSendMessage(input, fileInput, isComment = false) {
    const ticketId = window.currentTicket?.id;
    if (!ticketId) return;

    const content = input.value.trim();
    const files = fileInput.files;

    if (!content && files.length === 0) return;

    const formData = new FormData();
    formData.append('content', content);

    for (let i = 0; i < files.length; i++) {
        formData.append('attachments', files[i]);
    }

    const csrfToken = getCSRFToken();
    if (csrfToken) formData.append('csrf_token', csrfToken);

    try {
        const url = isComment
            ? `/api/ticket/${ticketId}/internal_comment`
            : `/api/ticket/${ticketId}/reply`;

        const response = await fetch(url, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`${response.status}: ${errorText}`);
        }

        const result = await response.json();

        if (result.status === 'success') {
            input.value = '';
            fileInput.value = '';
            if (fileUploadClearFn) fileUploadClearFn();

            const formFilesList = document.getElementById('formFiles');
            if (formFilesList) {
                formFilesList.innerHTML = ``;
                formFilesList.style.display = 'none';
            }
        } else {
            alert('Ошибка: ' + result.message);
        }
    } catch (error) {
        console.error('Ошибка отправки сообщения:', error);
        alert('Не удалось отправить сообщение. Проверьте соединение.');
    }
}

export async function fetchChangeTicketStatus(newStatus, buttonElement,
    ticketId = window.currentTicket?.id || 1) {
    if (buttonElement.disabled) return;

    const originalText = buttonElement.textContent;
    const csrfToken = document.querySelector('meta[name="csrf_token"]').getAttribute('content');

    try {
        buttonElement.disabled = true;
        buttonElement.textContent = 'Сохранение...';

        const response = await fetch(`/api/ticket/${ticketId}/status`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ status: newStatus })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Ошибка сервера');
        }

        const result = await response.json();
        return result.status;
    } catch (error) {
        console.error('Ошибка смены статуса:', error);
        alert(`Не удалось сменить статус: ${error}`);
        return null;
    } finally {
        buttonElement.disabled = false;
        buttonElement.textContent = originalText;
    }
}

export async function fetchCloneTicket(ticketId, buttonElement) {
    if (buttonElement && buttonElement.disabled) return null;

    const originalText = buttonElement ? buttonElement.textContent : '';
    const csrfToken = getCSRFToken();

    try {
        if (buttonElement) {
            buttonElement.disabled = true;
            buttonElement.textContent = 'Создание...';
        }

        const response = await fetch(`/api/ticket/${ticketId}/clone`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Ошибка сервера');
        }

        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Ошибка создания похожей заявки:', error);
        alert(`Не удалось создать заявку: ${error}`);
        return null;
    } finally {
        if (buttonElement) {
            buttonElement.disabled = false;
            buttonElement.textContent = originalText;
        }
    }
}

export async function fetchDeleteTicket(ticketId, buttonElement) {
    if (buttonElement && buttonElement.disabled) return null;

    const originalText = buttonElement ? buttonElement.textContent : '';
    const csrfToken = getCSRFToken();

    try {
        if (buttonElement) {
            buttonElement.disabled = true;
            buttonElement.textContent = 'Удаление...';
        }

        const response = await fetch(`/api/ticket/${ticketId}/delete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Ошибка сервера');
        }

        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Ошибка удаления заявки:', error);
        alert(`Не удалось удалить заявку: ${error}`);
        return null;
    } finally {
        if (buttonElement) {
            buttonElement.disabled = false;
            buttonElement.textContent = originalText;
        }
    }
}

export async function fetchChangeTicketParams(params, buttonElement) {
    if (!buttonElement || buttonElement.disabled) return;

    const ticketId = window.currentTicket?.id;
    if (!ticketId) return false;

    const originalText = buttonElement.textContent;

    try {
        buttonElement.disabled = true;
        buttonElement.textContent = 'Сохранение...';

        const response = await fetch(`/api/ticket/${ticketId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify(params)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Ошибка сервера');
        }

        const result = await response.json();
        return result.status === 'success';
    } catch (error) {
        console.error('Ошибка изменения параметров:', error);
        alert(`Не удалось применить изменения: ${error}`);
        return false;
    } finally {
        buttonElement.disabled = false;
        buttonElement.textContent = originalText;
    }
}

export async function fetchReadNotifications(buttonElement, badge, unreadItems) {
    if (!buttonElement || buttonElement.disabled) return;

    try {
        buttonElement.disabled = true;

        const response = await fetch(`/api/notifications/read_all`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Ошибка сервера');
        }

        if (badge)
            badge.style.display = 'none';

        unreadItems.forEach(item => item.classList.remove('dropdown-item__content--unchecked'));

        const result = await response.json();
        return result.status === 'success';
    } catch (error) {
        console.error('Ошибка отметки уведомлений:', error);
        alert(`Не удалось отметить уведомления: ${error}`);
        return false;
    } finally {
        buttonElement.disabled = false;
    }
}

// js/dashboard/filtersState.js
// (состояние фильтров)
export const filtersState = {
    category_id: '',
    executor_id: '',
    applicant_id: '',
    host_name: ''
};

export function updateState(key, value) {
    if (key in filtersState) {
        filtersState[key] = value;
    }
}

export function getStateParams() {
    const params = new URLSearchParams();
    if (filtersState.category_id) params.set('category_id', filtersState.category_id);
    if (filtersState.executor_id) params.set('executor_id', filtersState.executor_id);
    if (filtersState.applicant_id) params.set('applicant_id', filtersState.applicant_id);
    if (filtersState.host_name) params.set('host_name', filtersState.host_name);
    return params;
}

export function resetState() {
    filtersState.category_id = '';
    filtersState.executor_id = '';
    filtersState.applicant_id = '';
    filtersState.host_name = '';
}
// js/dashboard/filterReset.js
export function initResetFilter(resetCallback) {
    const resetBtn = document.getElementById('filterReset');
    if (!resetBtn) return;

    // Если передан колбэк, используем его
    if (resetCallback) {
        resetBtn.addEventListener('click', resetCallback);
    }
}
// js/dashboard/filterReset.js
export function initResetFilter() {
    const resetBtn = document.getElementById('filterReset');
    if (!resetBtn) return;

    resetBtn.addEventListener('click', () => {
        window.location.reload();
    });
}
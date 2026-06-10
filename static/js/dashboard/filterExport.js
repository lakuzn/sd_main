// js/dashboard/filterExport.js
export function initExportFilter() {
    const link = document.getElementById('exportExcel');
    if (!link) return;

    const startInput = document.getElementById('exportStart');
    const endInput = document.getElementById('exportEnd');
    const baseHref = link.getAttribute('href');

    function updateHref() {
        const params = new URLSearchParams();
        if (startInput?.value) params.set('start', startInput.value);
        if (endInput?.value) params.set('end', endInput.value);
        const qs = params.toString();
        link.setAttribute('href', qs ? `${baseHref}?${qs}` : baseHref);
    }

    if (startInput) startInput.addEventListener('change', updateHref);
    if (endInput) endInput.addEventListener('change', updateHref);
}
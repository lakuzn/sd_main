// js/dashboard/filterExport.js
import { escapeHtml } from '../../common/utils.js';

export function initArchiveExport() {
    const btnExcport = document.getElementById('exportExcel');
    if (!btnExcport) return;

    btnExcport.addEventListener('click', () => showArchiveExportModal());

    // const startInput = document.getElementById('exportStart');
    // const endInput = document.getElementById('exportEnd');
    // const baseHref = btnExcport.getAttribute('href');

    // function updateHref() {
    //     const params = new URLSearchParams();
    //     if (startInput?.value) params.set('start', startInput.value);
    //     if (endInput?.value) params.set('end', endInput.value);
    //     const qs = params.toString();
    //     btnExcport.setAttribute('href', qs ? `${baseHref}?${qs}` : baseHref);
    // }

    // if (startInput) startInput.addEventListener('change', updateHref);
    // if (endInput) endInput.addEventListener('change', updateHref);
}

function showArchiveExportModal() {
    const modal = document.getElementById('modalExport');
    if (!modal) return;

    modal.style.display = 'flex';

    const closeModal = () => modal.style.display = 'none';
    const overlay = modal.querySelector('.modal__overlay');
    const closeBtn = modal.querySelector('.modal__close');

    overlay?.addEventListener('click', closeModal);
    closeBtn?.addEventListener('click', closeModal);
}
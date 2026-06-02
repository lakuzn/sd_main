import { initAllComponents } from "./components/index.js";

export { initAllComponents };

document.addEventListener('DOMContentLoaded', async function () {
    await initAllComponents();

    // Переносы предлогов
    document.querySelectorAll('p').forEach(p => {
        p.innerHTM = p.innerHTML.replace(/(\s(в|на|с|о|к|у|за|и|для|или))\s/g, '$1&nbsp;');
    });
})
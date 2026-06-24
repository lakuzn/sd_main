import { initAllComponents } from "./index.js";

export { initAllComponents };

document.addEventListener('DOMContentLoaded', async function () {
    await initAllComponents();
})
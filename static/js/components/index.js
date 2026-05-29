import { initFiltersFaq } from "../modules/filtersFaq.js";
import { initTicketActions } from "../modules/ticketActions.js";
import { initChat } from "../modules/chat.js";
import { initFileUpload } from "../modules/fileUpload.js";
import { initDropdownNotification } from "../modules/dropdownNotification.js";
import { initReopenTicket } from "../modules/reopenTicket.js";
import { initTicketParams } from "../modules/ticketParams.js";
import { initFaqsActions } from "../modules/faqsActions.js";
import { initArticle } from "../modules/article.js";
import { initSocketDashboardTickets } from "../modules/dashboard.js";
import { initSearchFilter } from "../modules/search/searchFilter.js"

export async function initAllComponents() {
    initDropdownNotification();

    if (document.getElementById('create_ticket')) {
        initFileUpload();
    }
    else if (document.getElementById('ticket')) {
        initTicketActions();
        initChat();
        initTicketParams();
    }
    else if (document.getElementById('archive')) {
        initReopenTicket();
    }
    else if (document.getElementById('faqs')) {
        initFiltersFaq();
        initFaqsActions();
    }
    else if (document.getElementById('article_create')) {
        initArticle();
    }
    else if (document.getElementById('dashboard')) {
        initSocketDashboardTickets();
    }
    else if (document.getElementById('search')) {
        initSearchFilter();
    }
}
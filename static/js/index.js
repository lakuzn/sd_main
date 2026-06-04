import { initTicketPage } from "./ticket/ticketPage.js";
import { initCreateTicketForm } from "./forms/createTicket.js";
import { initArchivePage } from "./dashboard/reopenTicket.js";
import { initFaqPage } from "./faq/faqPage.js";
import { initArticleForm } from "./forms/article.js";
import { initDashboard } from "./dashboard/dashboard.js";
import { initSearchPage } from "./search/searchFilter.js";
import { initDropdownNotification } from "./notifications/dropdownNotification.js";
import { fixRussianPrepositions } from './common/utils.js';

export async function initAllComponents() {
    initDropdownNotification();

    if (document.getElementById('create_ticket')) {
        initCreateTicketForm();
    }
    else if (document.getElementById('ticket')) {
        initTicketPage();
    }
    else if (document.getElementById('archive')) {
        initArchivePage();
    }
    else if (document.getElementById('faqs')) {
        initFaqPage();
    }
    else if (document.getElementById('article_create')) {
        initArticleForm();
    }
    else if (document.getElementById('dashboard')) {
        initDashboard();
    }
    else if (document.getElementById('search')) {
        initSearchPage();
    }

    fixRussianPrepositions(); // переносы предлогов
}
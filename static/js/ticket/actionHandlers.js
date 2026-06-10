// js/ticket/actionHandlers.js
import { showInviteModal, showAddCommentModal } from './modalManager.js';

export function initInviteButton() {
    const buttonInvite = document.getElementById('buttonInvite');
    const ticketId = window.currentTicket?.id;
    if (buttonInvite && ticketId) {
        buttonInvite.addEventListener('click', () => showInviteModal(ticketId));
    }
}

export function initCommentButtons() {
    const buttonAddComment = document.getElementById('buttonAddComment');
    const buttonSeeComments = document.getElementById('buttonSeeComments');

    if (buttonAddComment) {
        buttonAddComment.addEventListener('click', () => showAddCommentModal());
    }
    if (buttonSeeComments) {
        buttonSeeComments.addEventListener('click', () => showAddCommentModal());
    }
}
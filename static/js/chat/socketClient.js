// js/chat/socketClient.js
let socket = null;
let commentListenerAttached = false;

export function initSocket(ticketId, callbacks = {}) {
    if (socket) return socket;

    socket = io();

    socket.on('connect', () => {
        socket.emit('join_ticket', { ticket_id: ticketId });
    });

    socket.on('receive_message', (data) => {
        if (callbacks.onReceiveMessage) callbacks.onReceiveMessage(data);
    });

    socket.on('receive_comment', (data) => {
        if (!commentListenerAttached && callbacks.onReceiveComment) {
            commentListenerAttached = true;
            callbacks.onReceiveComment(data);
        } else if (callbacks.onReceiveComment) {
            callbacks.onReceiveComment(data);
        } else {
            console.log(commentListenerAttached, callbacks.onReceiveComment);
        }
    });

    socket.on('ticket_status_changed', (data) => {
        if (callbacks.onStatusChanged) callbacks.onStatusChanged(data);
    });

    socket.on('error', (err) => console.error('Socket error:', err));

    return socket;
}

export function getSocket() {
    return socket;
}

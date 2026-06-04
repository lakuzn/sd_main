// js/chat/socketClient.js
let socket = null;
let callbacks = {
    onReceiveMessage: null,
    onReceiveComment: null,
    onStatusChanged: null
};

export function initSocket(ticketId, newCallbacks = {}) {
    // Обновляем колбэки (даже если сокет уже существует)
    Object.assign(callbacks, newCallbacks);

    if (socket) return socket;

    socket = io();

    socket.on('connect', () => {
        socket.emit('join_ticket', { ticket_id: ticketId });
    });

    socket.on('receive_message', (data) => {
        if (callbacks.onReceiveMessage) callbacks.onReceiveMessage(data);
    });

    socket.on('receive_comment', (data) => {
        if (callbacks.onReceiveComment) callbacks.onReceiveComment(data);
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
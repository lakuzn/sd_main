from flask_socketio import emit, join_room, leave_room
from flask_login import current_user, login_required
from app.extensions import socketio


@socketio.on("join_dashboard")
@login_required
def handle_join_dashboard():
    role = current_user.role
    user_id = current_user.id

    # Персональная комната пользователя (для его дашборда)
    join_room(f"dashboard_{role}_{user_id}")

    # Если роль позволяет – присоединяемся к общим комнатам
    if role == "admin":
        join_room("dashboard_admin_all")
    elif role == "classifier" or role == "head":
        join_room("dashboard_classifier_all")

    emit("dashboard_joined", {"status": "ok"})


@socketio.on("leave_dashboard")
@login_required
def handle_leave_dashboard():
    role = current_user.role
    user_id = current_user.id

    leave_room(f"dashboard_{role}_{user_id}")

    if role == "admin":
        leave_room("dashboard_admin_all")
    elif role == "classifier":
        leave_room("dashboard_classifier_all")

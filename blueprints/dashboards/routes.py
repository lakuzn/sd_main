from flask import render_template, request
from flask_login import login_required, current_user
from app.blueprints.dashboards import dashboards_bp
from app.services.dashboard_service import DashboardService
from app.utils.decorators import role_required


# Дашборд пользователя
@dashboards_bp.route("/user")
@login_required
def user():

    page = request.args.get("page", 1, type=int)
    data = DashboardService.get_user_data(current_user.id, page)

    return render_template(
        "dashboards/user.html", tickets=data["tickets"], pagination=data["pagination"]
    )


# Дашборд агента / начальника отдела
@dashboards_bp.route("/executor")
@login_required
@role_required(["executor", "admin", "head"])
def executor():
    if current_user.role == "head":
        data = DashboardService.get_head_data(current_user.id)
    else:
        data = DashboardService.get_executor_data(current_user.id)

    return render_template(
        "dashboards/executor.html",
        tickets=data["tickets"],
    )


# Дашборд админа
@dashboards_bp.route("/admin")
@login_required
@role_required(["admin"])
def admin():
    data = DashboardService.get_admin_data()

    return render_template(
        "dashboards/admin.html",
        tickets=data["tickets"],
        # category_data=data["category_data"],
        # status_data=data["status_data"],
        overdue_count=data["overdue_count"],
    )


# Дашборд классификатора
@dashboards_bp.route("/classifier")
@login_required
@role_required(["classifier", "admin"])
def classifier():
    page = request.args.get("page", 1, type=int)
    data = DashboardService.get_classifier_data(current_user.id)

    return render_template(
        "dashboards/classifier.html",
        tickets=data["tickets"],
        pagination=data["pagination"],
    )


# Архив
@dashboards_bp.route("/archive")
@login_required
def archive():
    context = DashboardService.get_archive_data(current_user.id, current_user.role)

    return render_template(
        "dashboards/archive.html",
        **context,
    )

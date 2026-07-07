from datetime import datetime, timedelta
from flask import render_template, request, send_file, flash, redirect, url_for
from flask_login import login_required, current_user
from app.blueprints.dashboards import dashboards_bp
from app.services.archive_service import ArchiveService
from app.services.dashboard_service import DashboardService
from app.utils.decorators import role_required


# Дашборд пользователя
@dashboards_bp.route("/user")
@login_required
def user():

    page = request.args.get("page", 1, type=int)
    data = DashboardService.get_user_data(current_user.id, page)

    return render_template(
        "dashboards/user.html",
        tickets=data["tickets"],
        pagination=data["pagination"],
        unread_ticket_ids=data["unread_ticket_ids"],
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
        unread_ticket_ids=data["unread_ticket_ids"],
    )


# Дашборд классификатора
@dashboards_bp.route("/classifier")
@login_required
@role_required(["classifier", "admin"])
def classifier():
    page = request.args.get("page", 1, type=int)
    data = DashboardService.get_classifier_data(current_user.id, page)

    return render_template(
        "dashboards/classifier.html",
        tickets=data["tickets"],
        pagination=data["pagination"],
        unread_ticket_ids=data["unread_ticket_ids"],
    )


# Дашборд админа
@dashboards_bp.route("/admin")
@login_required
@role_required(["admin"])
def admin():
    page = request.args.get("page", 1, type=int)
    data = DashboardService.get_classifier_data(current_user.id, page)

    return render_template(
        "dashboards/admin.html",
        tickets=data["tickets"],
        pagination=data["pagination"],
        unread_ticket_ids=data["unread_ticket_ids"],
    )


# Фильтрация дашборда
@dashboards_bp.route("/filter")
@login_required
@role_required(["classifier", "executor", "head", "admin"])
def filter_dashboard():
    category_id = request.args.get("category_id", type=int)
    executor_id = request.args.get("executor_id", type=int)
    applicant_id = request.args.get("applicant_id", type=int)
    host_name = (request.args.get("host_name") or "").strip() or None

    data = DashboardService.get_filtered_tickets(
        current_user,
        category_id=category_id,
        executor_id=executor_id,
        applicant_id=applicant_id,
        host_name=host_name,
    )

    html = render_template(
        "partials/pages/ticket/cards.html",
        tickets=data["tickets"],
        unread_ticket_ids=data["unread_ticket_ids"],
        card_unclassified=current_user.role in ["classifier", "admin"],
    )

    return {"html": html, "count": len(data["tickets"])}


# Выгрузка заявок
@dashboards_bp.route("/export")
@login_required
@role_required(["classifier", "head", "admin"])
def export_report():
    start_s = request.args.get("start")
    end_s = request.args.get("end")

    start_date = end_date = None
    try:
        if start_s:
            start_date = datetime.strptime(start_s, "%Y-%m-%d")
        if end_s:
            end_date = datetime.strptime(end_s, "%Y-%m-%d") + timedelta(days=1)
    except ValueError:
        flash("Некорректный формат даты периода.", "warning")
        return redirect(url_for("home"))

    if start_date and end_date and start_date >= end_date:
        flash("Дата начала должна быть раньше даты окончания.", "warning")
        return redirect(url_for("home"))

    try:
        stream = DashboardService.export_report(current_user, start_date, end_date)
    except ImportError:
        flash(
            "Для выгрузки в Excel требуется библиотека openpyxl "
            "(pip install openpyxl).",
            "danger",
        )
        return redirect(url_for("home"))

    filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return send_file(
        stream,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# Архив
@dashboards_bp.route("/archive")
@login_required
def archive():
    """Страница архива заявок"""
    data = ArchiveService.get_archive_data(current_user.id, current_user.role, "all")
    categories = ArchiveService.get_categories_for_role(current_user.role, current_user)

    return render_template(
        "dashboards/archive.html",
        tickets=data["tickets"],
        counts=data["counts"],
        categories=categories,
        current_filter=data["current_filter"],
    )

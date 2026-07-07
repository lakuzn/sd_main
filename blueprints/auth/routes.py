from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request,
    session,
    current_app,
)
from flask_login import login_user, logout_user, current_user, login_required
from app.blueprints.auth import auth_bp
from app.forms.auth_forms import LoginForm
from app.models.user import User
from app.extensions import db


def get_remote_user():
    header_user = request.headers.get("X-Remote-User")
    if header_user and header_user.strip() and header_user.strip() != "(null)":
        return header_user.strip()
    return request.environ.get("REMOTE_USER") or request.environ.get("LOGON_USER")


@auth_bp.before_app_request
def kerberos_sso_login():
    if not current_app.config.get("KERBEROS_SSO_ENABLED"):
        return
    if current_user.is_authenticated:
        return
    explicit_sso = request.endpoint == "auth.sso"
    if session.get("suppress_sso") and not explicit_sso:
        return
    if explicit_sso:
        session.pop("suppress_sso", None)

    remote = get_remote_user()
    if not remote:
        return

    username = remote.split("\\")[-1].split("@")[0].strip().lower()
    if not username:
        return

    user = User.query.filter(db.func.lower(User.username) == username).first()
    if user and user.is_active:
        login_user(user)


def _safe_next(target):
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return None


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    next_url = _safe_next(request.args.get("next"))
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.password_hash and user.check_password(form.password.data):
            if not user.is_active:
                flash("Ваша учетная запись заблокирована.", "danger")
                return redirect(url_for("auth.login"))

            login_user(user)
            session.pop("suppress_sso", None)
            flash("Вы успешно вошли в систему.", "success")

            return redirect(_safe_next(request.form.get("next")) or url_for("home"))
        else:
            flash("Неверный email или пароль.", "danger")

    return render_template("auth/login.html", next=next_url)


@auth_bp.route("/sso")
def sso():

    next_url = _safe_next(request.args.get("next")) or url_for("home")

    if current_user.is_authenticated:
        return redirect(next_url)

    remote = get_remote_user()
    if remote:
        flash(
            f"Доменная учётная запись «{remote}» опознана, но не найдена в системе "
            "или отключена. Обратитесь к администратору.",
            "danger",
        )
    else:
        flash(
            "Не удалось определить доменную учётную запись "
            "(Kerberos и доменный пароль не сработали). "
            "Войдите локальной учётной записью или обратитесь к администратору.",
            "warning",
        )
    return redirect(url_for("auth.login", next=_safe_next(request.args.get("next"))))


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()  # Удаляем куки сессии
    session["suppress_sso"] = True
    flash("Вы вышли из системы.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/account")
@login_required
def account():
    return render_template("auth/account.html")

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


@auth_bp.before_app_request
def kerberos_sso_login():
    """Автоматический вход по Kerberos (Single Sign-On).

    Сам Kerberos выполняет IIS (Windows Authentication). Уже аутентифицированное
    имя пользователя IIS передаёт в переменную окружения REMOTE_USER, например
    "COMPANY\\ivanov" или "ivanov@company.local". Здесь мы просто находим этого
    пользователя в нашей базе (выгруженной из AD) и логиним его.

    Включается только если в конфиге KERBEROS_SSO_ENABLED=true (рабочий сервер
    IIS). На машине разработчика без домена SSO выключен — работает обычный
    вход по логину/паролю.
    """
    if not current_app.config.get("KERBEROS_SSO_ENABLED"):
        return
    if current_user.is_authenticated:
        return
    # После явного выхода (logout) временно не логиним автоматически
    if session.get("suppress_sso"):
        return

    remote = request.environ.get("REMOTE_USER") or request.environ.get("LOGON_USER")
    if not remote:
        return

    # Из "COMPANY\\ivanov" или "ivanov@company.local" получаем "ivanov"
    username = remote.split("\\")[-1].split("@")[0].strip().lower()
    if not username:
        return

    user = User.query.filter(db.func.lower(User.username) == username).first()
    if user and user.is_active:
        login_user(user)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        # У доменных (AD) пользователей локального пароля нет (password_hash пуст) —
        # они входят только через Kerberos. Поэтому проверяем наличие пароля.
        if user and user.password_hash and user.check_password(form.password.data):
            if not user.is_active:
                flash("Ваша учетная запись заблокирована.", "danger")
                return redirect(url_for("auth.login"))

            login_user(user)
            # Разрешаем автоматический вход по Kerberos снова
            session.pop("suppress_sso", None)
            flash("Вы успешно вошли в систему.", "success")

            return redirect(url_for("home"))
        else:
            flash("Неверный email или пароль.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()  # Удаляем куки сессии
    # При входе через Kerberos браузер аутентифицирован на уровне Windows, поэтому
    # без этого флага нас бы тут же залогинило обратно. Флаг подавляет авто-вход
    # до следующего явного входа (или до закрытия браузера).
    session["suppress_sso"] = True
    flash("Вы вышли из системы.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/account")
@login_required
def account():
    return render_template("auth/account.html")

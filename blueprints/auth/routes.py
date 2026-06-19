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
    """Возвращает имя пользователя, аутентифицированного веб-сервером, или None.

    ВАЖНО про связку Apache (mod_auth_gssapi) + gunicorn (mod_proxy_http):
    при проксировании Apache НЕ передаёт имя пользователя в WSGI-переменную
    окружения ``REMOTE_USER`` (она заполняется только при встроенном запуске —
    mod_wsgi / mod_cgi). Поэтому в конфиге Apache имя пробрасывается отдельным
    HTTP-заголовком::

        RequestHeader set X-Remote-User "%{REMOTE_USER}s"

    Читаем имя в порядке приоритета:
      1) HTTP-заголовок ``X-Remote-User`` — основной путь для Apache + gunicorn;
      2) WSGI ``REMOTE_USER`` — на случай mod_wsgi / mod_cgi;
      3) ``LOGON_USER`` — историческое имя из IIS.

    Заголовку можно доверять, потому что Apache в конфиге безусловно
    ПЕРЕЗАПИСЫВАЕТ его (``RequestHeader set`` затирает значение, присланное
    клиентом), а gunicorn слушает только 127.0.0.1 и снаружи недоступен.
    """
    header_user = request.headers.get("X-Remote-User")
    # Когда пользователь НЕ аутентифицирован (пути-исключения: /auth/login,
    # /static, /healthz), Apache подставляет в заголовок пустую строку или
    # литерал "(null)" — такое значение именем пользователя НЕ считаем.
    if header_user and header_user.strip() and header_user.strip() != "(null)":
        return header_user.strip()
    return request.environ.get("REMOTE_USER") or request.environ.get("LOGON_USER")


@auth_bp.before_app_request
def kerberos_sso_login():
    """Автоматический вход по Kerberos (Single Sign-On).

    Kerberos/Negotiate выполняет Apache (mod_auth_gssapi). Уже аутентифицированное
    имя пользователя Apache передаёт приложению в HTTP-заголовке ``X-Remote-User``
    (см. get_remote_user), например "POLYOT\\ivanov" или "ivanov@polyot.ru".
    Здесь мы находим этого пользователя в нашей базе (выгруженной из AD) и логиним.

    Включается только если в конфиге KERBEROS_SSO_ENABLED=true (рабочий сервер
    в домене). На машине разработчика без домена SSO выключен — работает обычный
    вход по логину/паролю.
    """
    if not current_app.config.get("KERBEROS_SSO_ENABLED"):
        return
    if current_user.is_authenticated:
        return
    # Заход на /auth/sso — это ЯВНЫЙ доменный вход (пользователь нажал кнопку),
    # поэтому подавление авто-входа после прошлого logout здесь снимаем.
    explicit_sso = request.endpoint == "auth.sso"
    # После явного выхода (logout) на обычных страницах не логиним автоматически
    if session.get("suppress_sso") and not explicit_sso:
        return
    if explicit_sso:
        session.pop("suppress_sso", None)

    remote = get_remote_user()
    if not remote:
        return

    # Из "COMPANY\\ivanov" или "ivanov@company.local" получаем "ivanov"
    username = remote.split("\\")[-1].split("@")[0].strip().lower()
    if not username:
        return

    user = User.query.filter(db.func.lower(User.username) == username).first()
    if user and user.is_active:
        login_user(user)


def _safe_next(target):
    """Возвращает target, только если это локальный путь (защита от open-redirect)."""
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

        # У доменных (AD) пользователей локального пароля нет (password_hash пуст) —
        # они входят только через Kerberos/доменный вход (кнопка ниже). Поэтому
        # форма проверяет только ЛОКАЛЬНЫЕ учётки (есть password_hash).
        if user and user.password_hash and user.check_password(form.password.data):
            if not user.is_active:
                flash("Ваша учетная запись заблокирована.", "danger")
                return redirect(url_for("auth.login"))

            login_user(user)
            # Разрешаем автоматический вход по Kerberos снова
            session.pop("suppress_sso", None)
            flash("Вы успешно вошли в систему.", "success")

            return redirect(_safe_next(request.form.get("next")) or url_for("home"))
        else:
            flash("Неверный email или пароль.", "danger")

    return render_template("auth/login.html", next=next_url)


@auth_bp.route("/sso")
def sso():
    """Единая точка ДОМЕННОГО входа (Kerberos/Negotiate ИЛИ ручной доменный
    логин+пароль). ИМЕННО на этот путь конфиг Apache навешивает mod_auth_gssapi и
    проставляет заголовок X-Remote-User. Сам вход уже выполняется в
    kerberos_sso_login() (before_app_request) — здесь только решаем, куда направить.

    Сюда пользователь попадает по кнопке «Войти по доменной учётной записи» со
    страницы /auth/login. На весь сайт Kerberos НЕ навешиваем, чтобы не ломать
    локальный вход (см. конфиг Apache).
    """
    next_url = _safe_next(request.args.get("next")) or url_for("home")

    if current_user.is_authenticated:
        return redirect(next_url)

    # Дошли сюда без авторизации: Apache либо не аутентифицировал (нет билета/keytab),
    # либо пользователя нет в нашей базе. Объясняем и возвращаем на форму входа.
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

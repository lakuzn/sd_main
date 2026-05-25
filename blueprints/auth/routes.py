from flask import render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from app.blueprints.auth import auth_bp
from app.forms.auth_forms import LoginForm
from app.models.user import User


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash("Ваша учетная запись заблокирована.", "danger")
                return redirect(url_for("auth.login"))

            login_user(user)
            flash("Вы успешно вошли в систему.", "success")

            return redirect(url_for("home"))
        else:
            flash("Неверный email или пароль.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()  # Удаляем куки сессии
    flash("Вы вышли из системы.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/account")
def account():
    return render_template("auth/account.html")

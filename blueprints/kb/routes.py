import os
from datetime import datetime
from flask import (
    request,
    redirect,
    url_for,
    flash,
    render_template,
    jsonify,
    current_app,
    abort,
)
from flask_login import login_required, current_user
from app.blueprints.kb import kb_bp
from app.services.kb_service import KBService
from app.models.category import Category
from app.utils.decorators import role_required
from app.forms.kb_forms import ArticleForm
from werkzeug.utils import secure_filename


@kb_bp.route("/")
@login_required
def catalog():
    staff_only = current_user.role != "user"
    grouped_articles = KBService.get_all_articles_grouped_by_category(
        staff_only=staff_only
    )
    return render_template("kb/catalog.html", grouped_articles=grouped_articles)


@kb_bp.route("/<int:id>")
@login_required
def article(id):
    article = KBService.get_article_by_id(id)
    can_edit = KBService.can_edit(article, current_user)
    return render_template("kb/article.html", article=article, can_edit=can_edit)


@kb_bp.route("/create", methods=["GET", "POST"])
@login_required
@role_required(
    ["admin", "executor", "classifier", "head"]
)  # Доступ только для персонала
def create_article():
    form = ArticleForm()

    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]

    if form.validate_on_submit():
        article = KBService.create_article(
            title=form.title.data,
            content=form.content.data,
            category_id=form.category_id.data,
            is_staff_only=form.is_staff_only.data,
            author_id=current_user.id,
        )
        flash("Статья успешно опубликована!", "success")
        return redirect(url_for("kb.article", id=article.id))
    return render_template("kb/create_article.html", form=form)


@kb_bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
@role_required(["admin", "executor", "classifier", "head"])
def edit_article(id):
    article = KBService.get_article_by_id(id)

    if not KBService.can_edit(article, current_user):
        abort(403)

    form = ArticleForm(obj=article)

    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]

    if form.validate_on_submit():
        KBService.update_article(
            article_id=article.id,
            title=form.title.data,
            content=form.content.data,
            category_id=form.category_id.data,
            is_staff_only=form.is_staff_only.data,
            editor=current_user,
        )
        flash("Статья обновлена.", "success")
        return redirect(url_for("kb.article", id=article.id))

    return render_template("kb/create_article.html", form=form, article=article)


@kb_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
@role_required(["admin", "executor", "classifier", "head"])
def delete_article(id):
    article = KBService.get_article_by_id(id)

    if not KBService.can_edit(article, current_user):
        abort(403)

    KBService.delete_article(article.id, current_user)
    flash("Статья удалена.", "success")
    return redirect(url_for("kb.catalog"))


@kb_bp.route("/upload", methods=["POST"])
@login_required
@role_required(["admin", "executor", "classifier", "head"])
def upload_attachment():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"status": "error", "message": "Файл не выбран"}), 400

    upload_folder = os.path.join(current_app.root_path, "static", "uploads", "kb")
    os.makedirs(upload_folder, exist_ok=True)

    original_name = file.filename
    safe_name = secure_filename(original_name) or "file"
    unique_name = f"{int(datetime.now().timestamp())}_{safe_name}"
    file.save(os.path.join(upload_folder, unique_name))

    db_path = f"uploads/kb/{unique_name}"

    return jsonify(
        {
            "status": "success",
            "file_name": original_name,
            "url": url_for("static", filename=db_path),
        }
    )

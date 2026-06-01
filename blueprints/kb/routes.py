from flask import request, redirect, url_for, flash, render_template
from flask_login import login_required, current_user
from app.blueprints.kb import kb_bp
from app.services.kb_service import KBService
from app.models.category import Category
from app.utils.decorators import role_required
from app.forms.kb_forms import ArticleForm


@kb_bp.route("/")
@login_required
def catalog():
    staff_only = current_user.role != "user"
    grouped_articles = KBService.get_all_articles_grouped_by_category(staff_only=staff_only)
    return render_template("kb/catalog.html", grouped_articles=grouped_articles)


@kb_bp.route("/<int:id>")
@login_required
def article(id):
    article = KBService.get_article_by_id(id)
    return render_template("kb/article.html", article=article)


@kb_bp.route("/create", methods=["GET", "POST"])
@login_required
@role_required(["admin", "executor", "classifier"])  # Доступ только для персонала
def create_article():
    form = ArticleForm()

    # Заполняем список категорий
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

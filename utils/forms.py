from flask import flash


def flash_form_errors(form):
    """Обработчик ошибок для WTForms"""
    for field, errors in form.errors.items():
        for error in errors:
            label = getattr(form, field).label.text
            flash(f"Ошибка в поле '{label}': {error}" "error")

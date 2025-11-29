from flask import Blueprint, render_template, request, url_for, redirect, g, flash
from werkzeug.security import generate_password_hash
from decorators import login_required
from db import db
from forms import UserForm, ResetPasswordConfirmForm

bp = Blueprint('profile', __name__, url_prefix='/profile')

@bp.route('/index')
@login_required
def index():
    return render_template('profile/index.html', user=g.user)

@bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    form = UserForm(request.form, obj=g.user)
    if request.method == 'POST' and form.validate():
        g.user.name = form.name.data
        g.user.email = form.email.data
        db.session.commit()
        return redirect(url_for('profile.index'))
    return render_template('profile/edit.html', form=form)

@bp.route('/reset', methods=['GET', 'POST'])
@login_required
def reset_password():
    form = ResetPasswordConfirmForm(request.form)
    if request.method == 'POST' and form.validate():
        g.user.password = generate_password_hash(form.new_password.data)
        db.session.commit()
        flash('Password reset successfully.')
        return redirect(url_for('profile.index'))
    return render_template('auth/reset_password_confirm.html', form=form)

from flask import Blueprint, render_template, request, url_for, redirect, g, flash
from decorators import login_required
from services.auth import edit_user, edit_user_password


bp = Blueprint('profile', __name__, url_prefix='/profile')

@bp.route('/index')
@login_required
def index():
    return render_template('profile/index.html', user=g.user)

@bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        edit_user(g.user.id, name, email)
        flash('Profile updated successfully.')
        return redirect(url_for('profile.index'))
    return render_template('profile/edit.html', user=g.user)

@bp.route('/reset', methods=['GET', 'POST'])
@login_required
def reset_password():
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        try:
            edit_user_password(g.user.id, new_password, confirm_password)
            flash('Password reset successfully.')
            return redirect(url_for('profile.index'))
        except ValueError as e:
            flash(str(e))
    return render_template('auth/reset_password_confirm.html')

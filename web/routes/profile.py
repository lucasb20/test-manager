from flask import Blueprint, render_template, request, url_for, redirect, g, flash
from werkzeug.security import generate_password_hash
from decorators import login_required
from db import db, User


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
        user = db.session.execute(db.select(User).filter_by(id=g.user.id)).scalar()
        user.name = name
        user.email = email
        db.session.commit()
        flash('Profile updated successfully.')
        return redirect(url_for('profile.index'))
    return render_template('profile/edit.html', user=g.user)

@bp.route('/reset', methods=['GET', 'POST'])
@login_required
def reset_password():
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        if new_password != confirm_password:
            flash('Passwords do not match.')
        else:
            g.user.password = generate_password_hash(new_password)
            db.session.commit()
            flash('Password reset successfully.')
            return redirect(url_for('profile.index'))
    return render_template('auth/reset_password_confirm.html')
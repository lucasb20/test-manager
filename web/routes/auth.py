from flask import Blueprint, request, render_template, redirect, url_for, flash, session, g, current_app
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.exc import IntegrityError
from utils import send_email, generate_reset_token, verify_reset_token
from forms import RegistrationForm, LoginForm, ResetPasswordForm, ResetPasswordConfirmForm
from db import db, User

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        user = db.session.execute(db.select(User).filter_by(email=form.email.data)).scalar()
        if user and check_password_hash(user.password, form.password.data):
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('index'))
        flash('Invalid email or password.')
    return render_template('auth/login.html', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        try:
            user = User(
                name=form.name.data,
                email=form.email.data,
                password=generate_password_hash(form.password.data)
            )
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.')
            return redirect(url_for('auth.login'))
        except IntegrityError:
            flash('Email already registered.')
    return render_template('auth/register.html', form=form)

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@bp.route('/reset', methods=['GET', 'POST'])
def reset_password():
    form = ResetPasswordForm(request.form)
    if request.method == 'POST' and form.validate():
        user_id = db.session.execute(db.select(User.id).filter_by(email=form.email.data)).scalar()
        if user_id:
            token = generate_reset_token(user_id, current_app.config['SECRET_KEY'])
            send_email(form.email.data, 'Password Reset', f'Your password reset link: {url_for("auth.reset_password_confirm", token=token, _external=True)}')
            current_app.logger.info(url_for("auth.reset_password_confirm", token=token, _external=True))
        flash('Password reset email sent.')
    return render_template('auth/reset_password.html', form=form)

@bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password_confirm(token):
    user_id = verify_reset_token(token, current_app.config['SECRET_KEY'])
    if user_id is None:
        flash('Invalid or expired reset link.')
        return redirect(url_for('auth.reset_password'))
    form = ResetPasswordConfirmForm(request.form)
    if request.method == 'POST' and form.validate():
        db.session.execute(db.update(User).where(User.id == user_id).values(password=generate_password_hash(form.new_password.data)))
        db.session.commit()
        flash('Password has been reset. Please log in.')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_confirm.html', form=form)

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = db.session.get(User, user_id)

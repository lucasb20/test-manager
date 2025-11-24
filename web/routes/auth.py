from flask import Blueprint, request, render_template, redirect, url_for, flash, session, g, current_app
from sqlalchemy.exc import IntegrityError
import click
from utils import send_email, generate_reset_token, verify_reset_token
from services.auth import verify_credentials, create_user, get_user_by_email, edit_user_password, get_user, RegistrationForm, LoginForm, ResetPasswordForm, ResetPasswordConfirmForm


bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        user_id = verify_credentials(form.email.data, form.password.data)
        if user_id is not None:
            session.clear()
            session['user_id'] = user_id
            return redirect(url_for('index'))
        flash('Invalid email or password.')
    return render_template('auth/login.html', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        try:
            create_user(form.name.data, form.email.data, form.password.data)
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
        user_id = get_user_by_email(form.email.data)
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
        edit_user_password(user_id, form.new_password.data)
        flash('Password has been reset. Please log in.')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_confirm.html', form=form)

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = get_user(user_id)

@bp.cli.command('create-admin')
@click.argument('name')
@click.argument('email')
@click.argument('password')
def create_admin(name, email, password):
    create_user(name, email, password, is_admin=True)

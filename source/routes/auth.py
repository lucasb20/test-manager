from flask import Blueprint, request
import click
from werkzeug.security import check_password_hash, generate_password_hash
from flask import render_template, redirect, url_for, flash, session, g, current_app
from db import db, User
from utils import send_email, generate_reset_token, verify_reset_token


bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        error = None
        user = db.session.execute(db.select(User).filter_by(email=email)).scalar()

        if user is None or not check_password_hash(user.password, password):
            error = 'Incorrect email or password.'

        if error is None:
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('index'))
        flash(error)

    return render_template('auth/login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            flash('Passwords do not match.')
        else:
            user = db.session.execute(db.select(User).filter_by(email=email)).first()
            if user:
                flash('Email address already registered.')
            else:
                new_user = User(name=name, email=email, password=generate_password_hash(password))
                db.session.add(new_user)
                db.session.commit()
                flash('Registration successful! Please log in.')
                return redirect(url_for('auth.login'))
    return render_template('auth/register.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@bp.route('/reset', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        user = db.session.query(User).filter_by(email=email).first()
        if user:
            token = generate_reset_token(user.id, current_app.config['SECRET_KEY'])
            send_email(email, 'Password Reset', f'Your password reset link: {url_for("auth.reset_password_confirm", token=token, _external=True)}')
        flash('Password reset email sent.')
    return render_template('auth/reset_password.html')

@bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password_confirm(token):
    user_id = verify_reset_token(token, current_app.config['SECRET_KEY'])
    if user_id is None:
        flash('Invalid or expired reset link.')
        return redirect(url_for('auth.reset_password'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        if new_password != confirm_password:
            flash('Passwords do not match.')
            return redirect(url_for('auth.reset_password_confirm', token=token))
        user = db.get_or_404(User, user_id)
        user.password = generate_password_hash(new_password)
        db.session.commit()
        flash('Password has been reset. Please log in.')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password_confirm.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = db.one_or_404(db.select(User).filter_by(id=user_id))

@bp.cli.command('create-admin')
@click.argument('name')
@click.argument('email')
@click.argument('password')
def create_admin(name, email, password):
    admin_user = User(name=name, email=email, password=generate_password_hash(password), is_admin=True)
    db.session.add(admin_user)
    db.session.commit()
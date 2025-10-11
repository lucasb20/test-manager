from flask import Blueprint, request
import click
from werkzeug.security import check_password_hash, generate_password_hash
from flask import render_template, redirect, url_for, flash, session, g, current_app
from db import db, User, Project
import jwt
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta, timezone


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
            session['project_id'] = None
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
            token = jwt.encode({'user_id': user.id, 'exp': datetime.now(tz=timezone.utc) + timedelta(hours=1)}, current_app.config['SECRET_KEY'], algorithm='HS256')
            msg = MIMEText(f'Your password reset link: {url_for("auth.reset_2", token=token, _external=True)}')
            msg['Subject'] = 'Password Reset'
            msg['From'] = 'noreply@example.com'
            msg['To'] = email
            with smtplib.SMTP('maildev', 1025) as server:
                server.send_message(msg)
        flash('Password reset email sent.')
    return render_template('auth/reset1.html')

@bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset_2(token):
    try:
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = data['user_id']
    except jwt.ExpiredSignatureError:
        flash('The reset link has expired.')
        return redirect(url_for('auth.reset_password'))
    except jwt.InvalidTokenError:
        flash('Invalid reset link.')
        return redirect(url_for('auth.reset_password'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        if new_password != confirm_password:
            flash('Passwords do not match.')
            return redirect(url_for('auth.reset_2', token=token))
        user = db.get_or_404(User, user_id)
        user.password = generate_password_hash(new_password)
        db.session.commit()
        flash('Password has been reset. Please log in.')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset2.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    project_id = session.get('project_id')
    if user_id is None:
        g.user = None
    else:
        g.user = db.one_or_404(db.select(User).filter_by(id=user_id))

    if project_id is None:
        g.project = None
    else:
        g.project = db.one_or_404(db.select(Project).filter_by(id=project_id))

@bp.cli.command('create-admin')
@click.argument('name')
@click.argument('email')
@click.argument('password')
def create_admin(name, email, password):
    admin_user = User(name=name, email=email, password=generate_password_hash(password), is_admin=True)
    db.session.add(admin_user)
    db.session.commit()
from werkzeug.security import check_password_hash, generate_password_hash
from db import db, User
from wtforms import Form, StringField, PasswordField, validators


class RegistrationForm(Form):
    name = StringField('Name', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=35)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm_password', message='Passwords must match')])
    confirm_password = PasswordField('Confirm Password')

class LoginForm(Form):
    email = StringField('Email', [validators.Length(min=6, max=35)])
    password = PasswordField('Password', [validators.DataRequired()])

class ResetPasswordForm(Form):
    email = StringField('Email', [validators.Length(min=6, max=35)])

class ResetPasswordConfirmForm(Form):
    new_password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm_password', message='Passwords must match')])
    confirm_password = PasswordField('Confirm Password')

def verify_credentials(email, password):
    user = db.session.execute(db.select(User).filter_by(email=email)).scalar()
    if user and check_password_hash(user.password, password):
        return user.id
    return None

def create_user(name, email, password, is_admin=False):
    new_user = User(name=name, email=email, password=generate_password_hash(password), is_admin=is_admin)
    db.session.add(new_user)
    db.session.commit()

def get_user(user_id):
    return db.session.get(User, user_id)

def get_user_by_email(email):
    return db.session.execute(db.select(User.id).filter_by(email=email)).scalar()

def edit_user_password(user_id, password):
    user = db.session.get(User, user_id)
    user.password = generate_password_hash(password)
    db.session.commit()

def edit_user(user_id, name, email):
    user = db.session.get(User, user_id)
    user.name = name
    user.email = email
    db.session.commit()

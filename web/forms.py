from wtforms import Form, StringField, PasswordField, TextAreaField, SelectField, BooleanField, validators

class UserForm(Form):
    name = StringField('Name', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=35)])

class RegistrationForm(UserForm):
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

class ProjectForm(Form):
    name = StringField('Name', [validators.InputRequired(), validators.Length(min=1, max=80)])
    description = TextAreaField('Description', [validators.Optional(), validators.Length(max=500)])

class RequirementForm(Form):
    title = StringField('Title', [validators.InputRequired(), validators.Length(min=1, max=200)])
    description = TextAreaField('Description', [validators.Optional(), validators.Length(max=500)])
    priority = SelectField('Priority', choices=[('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')], validators=[validators.InputRequired()])

class TestCaseForm(Form):
    title = StringField('Title', [validators.InputRequired(), validators.Length(max=200)])
    preconditions = StringField('Preconditions', [validators.Length(max=200)])
    steps = TextAreaField('Steps', [validators.Length(max=500)])
    expected_result = StringField('Expected Result', [validators.InputRequired(), validators.Length(max=200)])
    is_functional = SelectField('Functional', choices=[('1', 'Yes'), ('0', 'No')], coerce=int)
    is_automated = BooleanField('Automated')

class TestSuiteForm(Form):
    name = StringField('Name', [validators.InputRequired(), validators.Length(min=1, max=200)])
    description = TextAreaField('Description', [validators.Optional(), validators.Length(max=500)])

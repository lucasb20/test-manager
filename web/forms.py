from wtforms import Form, StringField, EmailField, PasswordField, TextAreaField, SelectField, IntegerField, validators

class UserForm(Form):
    name = StringField('Name', [validators.DataRequired(), validators.Length(min=4, max=25)])
    email = EmailField('Email', [validators.DataRequired()])

class RegistrationForm(UserForm):
    password = PasswordField('Password', [validators.DataRequired(), validators.EqualTo('confirm_password', message='Passwords must match')])
    confirm_password = PasswordField('Confirm Password')

class LoginForm(Form):
    email = EmailField('Email', [validators.DataRequired()])
    password = PasswordField('Password', [validators.DataRequired()])

class ResetPasswordForm(Form):
    email = EmailField('Email', [validators.DataRequired()])

class ResetPasswordConfirmForm(Form):
    new_password = PasswordField('New Password', [validators.DataRequired(), validators.EqualTo('confirm_password', message='Passwords must match')])
    confirm_password = PasswordField('Confirm Password')

class ProjectForm(Form):
    name = StringField('Name', [validators.InputRequired(), validators.Length(min=1, max=80)])
    description = TextAreaField('Description', [validators.Length(max=500)])

class RequirementForm(Form):
    title = StringField('Title', [validators.InputRequired(), validators.Length(min=1, max=200)])
    description = TextAreaField('Description', [validators.Length(max=500)])
    type = SelectField('Type', choices=[('functional', 'Functional'), ('quality', 'Quality'), ('constraint', 'Constraint')])
    priority = SelectField('Priority', choices=[('high', 'High'), ('medium', 'Medium'), ('low', 'Low')])

class TestCaseForm(Form):
    title = StringField('Title', [validators.InputRequired(), validators.Length(max=200)])
    preconditions = StringField('Preconditions', [validators.Length(max=200)])
    steps = TextAreaField('Steps', [validators.Length(max=500)])
    expected_result = StringField('Expected Result', [validators.Length(max=200)])

class TestSuiteForm(Form):
    name = StringField('Name', [validators.InputRequired(), validators.Length(min=1, max=200)])
    description = TextAreaField('Description', [validators.Length(max=500)])

class TestResultForm(Form):
    status = SelectField('Status', choices=[('None', 'Select status'), ('pass', 'Pass'), ('fail', 'Fail'), ('skip', 'Skip')])
    notes = TextAreaField('Description', [validators.Length(max=200)])

    def validate_status(form, field):
        if field.data == 'None':
            raise validators.ValidationError('Choose an option.')

class BugForm(Form):
    title = StringField('Title', [validators.InputRequired(), validators.Length(max=80)])
    description = TextAreaField('Description', [validators.Length(max=200)])
    priority = SelectField('Priority', choices=[('high', 'High'), ('medium', 'Medium'), ('low', 'Low')])
    status = SelectField('Status', choices=[('open', 'Open'), ('progress', 'Progress'), ('closed', 'Closed')])

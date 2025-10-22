from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime


class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    password = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(500), default=None)
    manager_id = db.Column(db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class ProjectMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.ForeignKey('project.id'))
    user_id = db.Column(db.ForeignKey('user.id'))
    role = db.Column(db.String(50))

class Requirement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.String(500), default=None)
    project_id = db.Column(db.ForeignKey('project.id'))
    priority = db.Column(db.String(50))
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    @property
    def code_with_prefix(self):
        return f"REQ-{self.order:03d}"

class TestCase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    preconditions = db.Column(db.String(200))
    steps = db.Column(db.String(500))
    expected_result = db.Column(db.String(200))
    project_id = db.Column(db.ForeignKey('project.id'))
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    @property
    def code_with_prefix(self):
        return f"CT-{self.order:03d}"

class RequirementTestCase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requirement_id = db.Column(db.ForeignKey('requirement.id'))
    test_case_id = db.Column(db.ForeignKey('test_case.id'))

class TestPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    description = db.Column(db.String(500), default=None)
    project_id = db.Column(db.ForeignKey('project.id'))
    platform = db.Column(db.String(50))
    milestone = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class TestPlanCase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_plan_id = db.Column(db.ForeignKey('test_plan.id'))
    test_case_id = db.Column(db.ForeignKey('test_case.id'))
    order = db.Column(db.Integer, default=0)

    @property
    def testcase(self):
        return db.session.get(TestCase, self.test_case_id)

class TestExecution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_plan_id = db.Column(db.ForeignKey('test_plan.id'))
    status = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)

    @property
    def name(self):
        name = db.session.get(TestPlan, self.test_plan_id).name
        return name if name else "Unnamed Test Plan"

    @property
    def next_case(self):
        return len(db.session.execute(
            db.select(TestResult.id).filter_by(test_execution_id=self.id)
        ).scalars().all())

class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_execution_id = db.Column(db.ForeignKey('test_execution.id'))
    test_case_id = db.Column(db.ForeignKey('test_case.id'))
    executed_by = db.Column(db.ForeignKey('user.id'))
    result = db.Column(db.String(50))
    executed_at = db.Column(db.DateTime, default=datetime.now)
    notes = db.Column(db.String(200))

    @property
    def test_case_code(self):
        test_case = db.session.get(TestCase, self.test_case_id)
        return test_case.code_with_prefix if test_case else "Unknown"

    @property
    def executor(self):
        user = db.session.get(User, self.executed_by)
        return user.name if user else "Unknown"

class AISuggestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requirement_id = db.Column(db.ForeignKey('requirement.id'))
    suggestion = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.now)
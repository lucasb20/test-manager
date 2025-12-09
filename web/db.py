from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from utils import code_with_prefix

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(500), default=None)
    manager_id = db.Column(db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    @property
    def manager(self):
        manager = db.session.execute(
            db.select(User.name).filter_by(id=self.manager_id)
        ).scalar()
        return manager or "Unassigned"

class ProjectMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.ForeignKey('project.id'))
    user_id = db.Column(db.ForeignKey('user.id'))
    role = db.Column(db.String(50), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.now)

    @property
    def name(self):
        name = db.session.execute(
            db.select(User.name).filter_by(id=self.user_id)
        ).scalar()
        return name or "Unknown"

    @property
    def email(self):
        email = db.session.execute(
            db.select(User.email).filter_by(id=self.user_id)
        ).scalar()
        return email or "Unknown"

class Requirement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), default=None)
    project_id = db.Column(db.ForeignKey('project.id'))
    priority = db.Column(db.String(50), nullable=False)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now)

    @property
    def code_with_prefix(self):
        return code_with_prefix("REQ", self.order)

    @property
    def last_order(self):
        last_req_order = db.session.execute(
            db.select(Requirement.order).filter_by(project_id=self.project_id).order_by(Requirement.order.desc())
        ).scalars().first()
        return last_req_order or 0

class TestCase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    preconditions = db.Column(db.String(200), nullable=False)
    steps = db.Column(db.String(500), nullable=False)
    expected_result = db.Column(db.String(200), nullable=False)
    is_functional = db.Column(db.Boolean, nullable=False, default=True)
    is_automated = db.Column(db.Boolean, nullable=False, default=False)
    project_id = db.Column(db.ForeignKey('project.id'))
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now)

    @property
    def code_with_prefix(self):
        return code_with_prefix("TC", self.order)

    @property
    def requirements_codes(self):
        reqs_orders = db.session.execute(
            db.select(Requirement.order).join(RequirementTestCase).filter(RequirementTestCase.test_case_id == self.id)
        ).scalars().all()
        return ', '.join([code_with_prefix("REQ", order) for order in reqs_orders])

    @property
    def last_order(self):
        last_tc_order = db.session.execute(
            db.select(TestCase.order).filter_by(project_id=self.project_id).order_by(TestCase.order.desc())
        ).scalars().first()
        return last_tc_order or 0

    @property
    def functional(self):
        return "Functional" if self.is_functional else "Non-Functional"

    @property
    def automation(self):
        return "Yes" if self.is_automated else "No"

class RequirementTestCase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requirement_id = db.Column(db.ForeignKey('requirement.id'))
    test_case_id = db.Column(db.ForeignKey('test_case.id'))

class TestSuite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), default=None)
    project_id = db.Column(db.ForeignKey('project.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class TestSuiteCase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_suite_id = db.Column(db.ForeignKey('test_suite.id'))
    test_case_id = db.Column(db.ForeignKey('test_case.id'))
    order = db.Column(db.Integer, default=0)

    @property
    def testcase(self):
        return db.session.get(TestCase, self.test_case_id)

class TestRun(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_suite_id = db.Column(db.ForeignKey('test_suite.id'))
    status = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)

    @property
    def name(self):
        name = db.session.execute(
            db.select(TestSuite.name).filter_by(id=self.test_suite_id)
        ).scalar()
        return name or "Unnamed Test Suite"

    @property
    def next_case(self):
        return db.session.execute(
            db.select(db.func.count()).select_from(TestResult).filter_by(test_run_id=self.id)
        ).scalar()

class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_run_id = db.Column(db.ForeignKey('test_run.id'))
    test_case_id = db.Column(db.ForeignKey('test_case.id'))
    executed_by = db.Column(db.ForeignKey('user.id'))
    result = db.Column(db.String(50))
    executed_at = db.Column(db.DateTime, default=datetime.now)
    notes = db.Column(db.String(200))

    @property
    def test_case_code(self):
        test_case = db.session.execute(
            db.select(TestCase.order).filter_by(id=self.test_case_id)
        ).scalar()
        return code_with_prefix("TC", test_case) if test_case else "Unknown"

    @property
    def executor(self):
        name = db.session.execute(
            db.select(User.name).filter_by(id=self.executed_by)
        ).scalar()
        return name or "Unknown"

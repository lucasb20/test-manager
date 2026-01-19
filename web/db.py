from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.mysql import ENUM
from utils import code_with_prefix

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    member_associations = db.relationship('ProjectMember', backref='member', lazy=True, cascade="all, delete-orphan")

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(500), default=None)
    manager_id = db.Column(db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    members = db.relationship('ProjectMember', backref='project', lazy=True, cascade="all, delete-orphan")
    requirements = db.relationship('Requirement', backref='project', lazy=True, cascade="all, delete-orphan")
    test_cases = db.relationship('TestCase', backref='project', lazy=True, cascade="all, delete-orphan")
    test_suites = db.relationship('TestSuite', backref='project', lazy=True, cascade="all, delete-orphan")
    bugs = db.relationship('Bug', backref='project', lazy=True, cascade="all, delete-orphan")

    @property
    def manager(self):
        return db.session.execute(db.select(User.name).filter_by(id=self.manager_id)).scalar()

class ProjectMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.ForeignKey('project.id'))
    user_id = db.Column(db.ForeignKey('user.id'))
    role = db.Column(ENUM('manager', 'editor', 'viewer'))
    joined_at = db.Column(db.DateTime, default=datetime.now)

    @property
    def name(self):
        return db.session.execute(db.select(User.name).filter_by(id=self.user_id)).scalar()

    @property
    def email(self):
        return db.session.execute(db.select(User.email).filter_by(id=self.user_id)).scalar()

class Requirement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), default=None)
    project_id = db.Column(db.ForeignKey('project.id'))
    type = db.Column(ENUM('functional', 'quality', 'constraint'), nullable=False)
    priority = db.Column(ENUM('high', 'medium', 'low'), nullable=False)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    testcase_associations = db.relationship('RequirementTestCase', backref='requirement', lazy=True, cascade="all, delete-orphan")

    @property
    def code_with_prefix(self):
        return code_with_prefix("REQ", self.order)

    @property
    def last_order(self):
        last_req_order = db.session.execute(db.select(Requirement.order).filter_by(project_id=self.project_id).order_by(Requirement.order.desc()).limit(1)).scalars().first()
        return last_req_order or 0

class TestCase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    preconditions = db.Column(db.String(200), nullable=False)
    steps = db.Column(db.String(500), nullable=False)
    expected_result = db.Column(db.String(200), nullable=False)
    is_automated = db.Column(db.Boolean, nullable=False, default=False)
    project_id = db.Column(db.ForeignKey('project.id'))
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    requirement_associations = db.relationship('RequirementTestCase', backref='test_case', lazy=True, cascade="all, delete-orphan")
    bug_associations = db.relationship('BugTestCase', backref='test_case', lazy=True, cascade="all, delete-orphan")
    testsuite_associations = db.relationship('TestSuiteCase', backref='test_case', lazy=True, cascade="all, delete-orphan")

    @property
    def code_with_prefix(self):
        return code_with_prefix("TC", self.order)

    @property
    def requirements_codes(self):
        reqs_orders = db.session.execute(db.select(Requirement.order).join(RequirementTestCase).filter(RequirementTestCase.test_case_id == self.id)).scalars().all()
        return [code_with_prefix("REQ", order) for order in reqs_orders]

    @property
    def last_order(self):
        last_tc_order = db.session.execute(db.select(TestCase.order).filter_by(project_id=self.project_id).order_by(TestCase.order.desc()).limit(1)).scalars().first()
        return last_tc_order or 0

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
    testcase_associations = db.relationship('TestSuiteCase', backref='test_suite', lazy=True, cascade="all, delete-orphan")
    testruns = db.relationship('TestRun', backref='test_suite', lazy=True, cascade="all, delete-orphan")

class TestSuiteCase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_suite_id = db.Column(db.ForeignKey('test_suite.id'))
    test_case_id = db.Column(db.ForeignKey('test_case.id'))
    order = db.Column(db.Integer, default=0)

    @property
    def testcase_code(self):
        tc_order = db.session.execute(db.select(TestCase.order).filter_by(id=self.test_case_id)).scalar()
        return code_with_prefix("TC", tc_order)

    @property
    def testcase_title(self):
        return db.session.execute(db.select(TestCase.title).filter_by(id=self.test_case_id)).scalar()

class TestRun(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_suite_id = db.Column(db.ForeignKey('test_suite.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    testresults = db.relationship('TestResult', backref='test_run', lazy=True, cascade="all, delete-orphan")

    @property
    def duration(self):
        return db.session.execute(db.select(db.func.sum(TestResult.duration)).filter(TestResult.test_run_id == self.id, TestResult.executed_at != None)).scalar()

    @property
    def total_executed(self):
        return db.session.execute(db.select(db.func.count()).select_from(TestResult).filter(TestResult.test_run_id == self.id, TestResult.executed_at != None)).scalar()

    @property
    def total_results(self):
        return db.session.execute(db.select(db.func.count()).select_from(TestResult).filter_by(test_run_id=self.id)).scalar()
    
    @property
    def is_finished(self):
        trs = db.session.execute(db.select(TestResult.executed_at).filter_by(test_run_id=self.id)).scalars()
        return all(trs)

class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_run_id = db.Column(db.ForeignKey('test_run.id'))
    test_case_id = db.Column(db.ForeignKey('test_case.id'))
    executed_by = db.Column(db.ForeignKey('user.id'))
    status = db.Column(ENUM('pass', 'fail', 'skip'), nullable=False)
    executed_at = db.Column(db.DateTime)
    notes = db.Column(db.String(200))
    duration = db.Column(db.Integer)

    @property
    def testcase_code(self):
        order = db.session.execute(db.select(TestCase.order).filter_by(id=self.test_case_id)).scalar()
        return code_with_prefix("TC", order) if order else "Unknown"

    @property
    def open_bugs(self):
        return db.session.execute(db.select(Bug).join(BugTestCase).filter(BugTestCase.test_case_id == self.test_case_id, Bug.status != 'Closed')).scalars().all()

    @property
    def executor(self):
        return db.session.execute(db.select(User.name).filter_by(id=self.executed_by)).scalar()

class Bug(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200), default=None)
    project_id = db.Column(db.ForeignKey('project.id'))
    reported_by = db.Column(db.ForeignKey('user.id'))
    status = db.Column(ENUM('open', 'progress', 'closed'), nullable=False)
    priority = db.Column(ENUM('high', 'medium', 'low'), nullable=False)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    testcase_associations = db.relationship('BugTestCase', backref='bug', lazy=True, cascade="all, delete-orphan")

    @property
    def code_with_prefix(self):
        return code_with_prefix("BUG", self.order)

    @property
    def last_order(self):
        last_bug_order = db.session.execute(db.select(Bug.order).filter_by(project_id=self.project_id).order_by(Bug.order.desc()).limit(1)).scalars().first()
        return last_bug_order or 0

    @property
    def testcases_codes(self):
        tcs_orders = db.session.execute(db.select(TestCase.order).join(BugTestCase).filter(BugTestCase.bug_id == self.id)).scalars().all()
        return [code_with_prefix("TC", order) for order in tcs_orders]

    @property
    def reporter(self):
        return db.session.execute(db.select(User.name).filter_by(id=self.reported_by)).scalar()

class BugTestCase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bug_id = db.Column(db.ForeignKey('bug.id'))
    test_case_id = db.Column(db.ForeignKey('test_case.id'))

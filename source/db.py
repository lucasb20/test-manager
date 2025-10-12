from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime


class Base(DeclarativeBase):
  pass


db = SQLAlchemy(model_class=Base)


class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    is_admin: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

class Project(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    description: Mapped[str | None] = mapped_column(default=None)
    manager_id: Mapped[int] = mapped_column(db.ForeignKey('user.id'))
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)

class ProjectMember(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(db.ForeignKey('project.id'))
    user_id: Mapped[int] = mapped_column(db.ForeignKey('user.id'))
    role: Mapped[str]

class Requirement(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    description: Mapped[str]
    code: Mapped[str]
    project_id: Mapped[int] = mapped_column(db.ForeignKey('project.id'))
    status: Mapped[str]
    priority: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)

class TestCase(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    preconditions: Mapped[str]
    steps: Mapped[str]
    expected_result: Mapped[str]
    project_id: Mapped[int] = mapped_column(db.ForeignKey('project.id'))
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)

class RequirementTestCase(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    requirement_id: Mapped[int] = mapped_column(db.ForeignKey('requirement.id'))
    test_case_id: Mapped[int] = mapped_column(db.ForeignKey('test_case.id'))

class TestPlan(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    description: Mapped[str | None] = mapped_column(default=None)
    project_id: Mapped[int] = mapped_column(db.ForeignKey('project.id'))
    platform: Mapped[str]
    milestone: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)

class TestPlanCase(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    test_plan_id: Mapped[int] = mapped_column(db.ForeignKey('test_plan.id'))
    test_case_id: Mapped[int] = mapped_column(db.ForeignKey('test_case.id'))

class TestExecution(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    test_plan_id: Mapped[int] = mapped_column(db.ForeignKey('test_plan.id'))
    status: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

class TestResult(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    test_execution_id: Mapped[int] = mapped_column(db.ForeignKey('test_execution.id'))
    test_case_id: Mapped[int] = mapped_column(db.ForeignKey('test_case.id'))
    executed_by: Mapped[int] = mapped_column(db.ForeignKey('user.id'))
    result: Mapped[str]
    executed_at: Mapped[datetime] = mapped_column(default=datetime.now)
    notes: Mapped[str]

class SystemLogs(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(db.ForeignKey('user.id'))
    action: Mapped[str]
    table_name: Mapped[str]
    record_id: Mapped[int]
    timestamp: Mapped[datetime] = mapped_column(default=datetime.now)

class AISuggestion(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    requirement_id: Mapped[int] = mapped_column(db.ForeignKey('requirement.id'))
    suggestion: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
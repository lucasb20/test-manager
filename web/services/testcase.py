from wtforms import Form, StringField, validators, TextAreaField, SelectField, BooleanField
from datetime import datetime
import re
from db import db, TestCase, RequirementTestCase, TestPlanCase


class TestCaseForm(Form):
    title = StringField('Title', [validators.InputRequired(), validators.Length(max=200)])
    preconditions = StringField('Preconditions', [validators.Length(max=200)])
    steps = TextAreaField('Steps', [validators.Length(max=500)])
    expected_result = StringField('Expected Result', [validators.InputRequired(), validators.Length(max=200)])
    is_functional = SelectField('Functional', choices=[('1', 'Yes'), ('0', 'No')], coerce=int)
    is_automated = BooleanField('Automated')

def normalize_steps(steps):
    rows = re.sub(r'^\s*\d+[\.\-\)]?\s*', '', steps, flags=re.MULTILINE)
    rows = [row.strip() for row in rows.splitlines() if row.strip()]
    norm_steps = []
    for i, row in enumerate(rows, 1):
        row = re.sub(r'[\.\s,]+$', '', row).strip()
        if not re.search(r'[\.\?\!]$', row):
            row += '.'
        norm_steps.append(f"{i}. {row}")
    return "\n".join(norm_steps)

def create_testcase(title, preconditions, steps, expected_result, project_id, is_functional, is_automated):
    testcase = TestCase(
        title=title,
        preconditions=preconditions,
        steps=normalize_steps(steps),
        expected_result=expected_result,
        project_id=project_id,
        is_functional=is_functional,
        is_automated=is_automated
    )
    testcase.order = testcase.last_order + 1
    db.session.add(testcase)
    db.session.commit()
    return testcase

def get_testcases(project_id):
    return db.session.execute(
        db.select(TestCase).filter_by(project_id=project_id).order_by(TestCase.order.asc())
    ).scalars().all()

def get_testcase(testcase_id):
    return db.session.get(TestCase, testcase_id)

def edit_testcase(testcase_id, title, preconditions, steps, expected_result, is_functional, is_automated):
    testcase = db.session.get(TestCase, testcase_id)
    testcase.title = title
    testcase.preconditions = preconditions
    testcase.steps = normalize_steps(steps)
    testcase.expected_result = expected_result
    testcase.is_functional = is_functional
    testcase.is_automated = is_automated
    testcase.updated_at = datetime.now()
    db.session.commit()
    return testcase

def update_orders(project_id):
    testcases = db.session.execute(
        db.select(TestCase).filter_by(project_id=project_id).order_by(TestCase.order.asc())
    ).scalars().all()
    for index, tc in enumerate(testcases):
        tc.order = index + 1
    db.session.commit()
    return testcases

def update_pair(testcase_id1, testcase_id2):
    testcase1 = db.get_or_404(TestCase, testcase_id1)
    testcase2 = db.get_or_404(TestCase, testcase_id2)
    testcase1.order, testcase2.order = testcase2.order, testcase1.order
    db.session.commit()

def delete_testcase(testcase_id):
    testcase = db.session.get(TestCase, testcase_id)
    rtcs = db.session.execute(
        db.select(RequirementTestCase).filter_by(testcase_id=testcase_id)
    ).scalars().all()
    for rtc in rtcs:
        db.session.delete(rtc)
    tpcs = db.session.execute(
        db.select(TestPlanCase).filter_by(test_case_id=testcase_id)
    ).scalars().all()
    for tpc in tpcs:
        db.session.delete(tpc)
    db.session.delete(testcase)
    db.session.commit()

from db import db, TestCase, Requirement, RequirementTestCase
from services.requirement import get_requirement, get_requirements
from services.testcase import get_testcases, get_testcase
import re


def create_associations_to_requirement(requirement_id, testcase_ids):
    requirement = get_requirement(requirement_id)
    testcases = get_testcases(requirement.project_id)
    associated_ids = get_associated_testcase_ids(requirement_id)
    for testcase in testcases:
        if str(testcase.id) in testcase_ids and testcase.id not in associated_ids:
            association = RequirementTestCase(requirement_id=requirement.id, test_case_id=testcase.id)
            db.session.add(association)
        elif str(testcase.id) not in testcase_ids and testcase.id in associated_ids:
            db.session.execute(
                db.delete(RequirementTestCase).filter_by(requirement_id=requirement.id, test_case_id=testcase.id)
            )
    db.session.commit()

def create_associations_to_testcase(testcase_id, requirement_ids):
    testcase = get_testcase(testcase_id)
    requirements = get_requirements(testcase.project_id)
    associated_ids = get_associated_requirement_ids(testcase_id)
    for req in requirements:
        if str(req.id) in requirement_ids and req.id not in associated_ids:
            association = RequirementTestCase(requirement_id=req.id, test_case_id=testcase.id)
            db.session.add(association)
        elif str(req.id) not in requirement_ids and req.id in associated_ids:
            db.session.execute(
                db.delete(RequirementTestCase).filter_by(requirement_id=req.id, test_case_id=testcase.id)
            )
    db.session.commit()

def create_associations_with_codes(testcase_id, codes):
    orders = re.findall(r'REQ-(\d+)', codes)
    for order in orders:
        req = db.session.execute(
            db.select(Requirement).filter_by(order=int(order))
        ).scalar_one_or_none()
        if req:
            association = RequirementTestCase(requirement_id=req.id, test_case_id=testcase_id)
            db.session.add(association)
    db.session.commit()

def get_associated_testcase_ids(requirement_id):
    return db.session.execute(
        db.select(RequirementTestCase.test_case_id).filter_by(requirement_id=requirement_id)
    ).scalars().all()

def get_associated_requirement_ids(testcase_id):
    return db.session.execute(
        db.select(RequirementTestCase.requirement_id).filter_by(test_case_id=testcase_id)
    ).scalars().all()

def get_testcases_for_requirement(requirement_id):
    return db.session.execute(
        db.select(TestCase).join(RequirementTestCase).filter(
            RequirementTestCase.requirement_id == requirement_id
        ).order_by(TestCase.order.asc())
    ).scalars().all()

def get_requirements_for_testcase(testcase_id):
    return db.session.execute(
        db.select(Requirement).join(RequirementTestCase).filter(
            RequirementTestCase.test_case_id == testcase_id
        )
    ).scalars().all()
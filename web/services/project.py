from db import db, Project, ProjectMember, TestCase, Requirement, RequirementTestCase, TestPlanCase, TestPlan, TestExecution, TestResult


def create_project(name, description, owner_id):
    project = Project(name=name, description=description, manager_id=owner_id)
    db.session.add(project)
    db.session.flush()
    project_member = ProjectMember(project_id=project.id, user_id=owner_id, role="manager")
    db.session.add(project_member)
    db.session.commit()
    return project

def get_projects(user):
    if user.is_admin:
        projects = db.session.execute(db.select(Project)).scalars()
    else:
        projects = db.session.execute(
            db.select(Project).join(ProjectMember).filter(ProjectMember.user_id == user.id)
        ).scalars()
    return projects

def get_project(project_id):
    return db.session.get(Project, project_id)

def edit_project(project_id, name, description):
    project = db.session.get(Project, project_id)
    project.name = name
    project.description = description
    db.session.commit()
    return project

def delete_project(project_id):
    project = db.session.get(Project, project_id)
    project_members = db.session.execute(
        db.select(ProjectMember).filter_by(project_id=project.id)
    ).scalars()
    for member in project_members:
        db.session.delete(member)
    rtcs = db.session.execute(
        db.select(RequirementTestCase).join(Requirement).filter(Requirement.project_id == project.id)
    ).scalars()
    for rtc in rtcs:
        db.session.delete(rtc)
    testcases = db.session.execute(
        db.select(TestCase).filter_by(project_id=project.id)
    ).scalars()
    for testcase in testcases:
        db.session.delete(testcase)
    requirements = db.session.execute(
        db.select(Requirement).filter_by(project_id=project.id)
    ).scalars()
    for requirement in requirements:
        db.session.delete(requirement)
    testplancases = db.session.execute(
        db.select(TestPlanCase).join(TestPlan).filter(TestPlan.project_id == project.id)
    ).scalars()
    for testplancase in testplancases:
        db.session.delete(testplancase)
    testplans = db.session.execute(
        db.select(TestPlan).filter_by(project_id=project.id)
    ).scalars()
    for testplan in testplans:
        db.session.delete(testplan)
    testexecutions = db.session.execute(
        db.select(TestExecution).join(TestPlan).filter(TestPlan.project_id == project.id)
    ).scalars()
    for testexecution in testexecutions:
        db.session.delete(testexecution)
    testresults = db.session.execute(
        db.select(TestResult).join(TestExecution).join(TestPlan).filter(TestPlan.project_id == project.id)
    ).scalars()
    for testresult in testresults:
        db.session.delete(testresult)
    db.session.delete(project)
    db.session.commit()
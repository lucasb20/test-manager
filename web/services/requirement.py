from wtforms import Form, StringField, validators, TextAreaField, SelectField
from datetime import datetime
from db import db, Requirement, RequirementTestCase


class RequirementForm(Form):
    title = StringField('Title', [validators.InputRequired(), validators.Length(min=1, max=200)])
    description = TextAreaField('Description', [validators.Optional(), validators.Length(max=500)])
    priority = SelectField('Priority', choices=[('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')], validators=[validators.InputRequired()])

def create_requirement(title, description, priority, project_id):
    requirement = Requirement(
        title=title,
        description=description,
        priority=priority,
        project_id=project_id
    )
    requirement.order = requirement.last_order + 1
    db.session.add(requirement)
    db.session.commit()
    return requirement

def get_requirements(project_id):
    return db.session.execute(
        db.select(Requirement).filter_by(project_id=project_id).order_by(Requirement.order.asc())
    ).scalars().all()

def get_requirement(requirement_id):
    return db.session.get(Requirement, requirement_id)

def edit_requirement(requirement_id, title, description, priority):
    requirement = get_requirement(requirement_id)
    if requirement:
        requirement.title = title
        requirement.description = description
        requirement.priority = priority
        requirement.updated_at = datetime.now()
        db.session.commit()
    return requirement

def update_orders(project_id):
    requirements = get_requirements(project_id)
    for index, req in enumerate(requirements):
        req.order = index + 1
    db.session.commit()
    return requirements

def update_pair(requirement_id1, requirement_id2):
    requirement1 = db.session.execute(
        db.select(Requirement).filter_by(id=requirement_id1)
    ).scalar()
    requirement2 = db.session.execute(
        db.select(Requirement).filter_by(id=requirement_id2)
    ).scalar()
    requirement1.order, requirement2.order = requirement2.order, requirement1.order
    db.session.commit()
    return requirement1, requirement2

def delete_requirement(requirement_id):
    requirement = db.session.get(Requirement, requirement_id)
    rtcs = db.session.execute(
        db.select(RequirementTestCase).filter_by(requirement_id=requirement_id)
    ).scalars().all()
    for rtc in rtcs:
        db.session.delete(rtc)
    db.session.delete(requirement)
    db.session.commit()

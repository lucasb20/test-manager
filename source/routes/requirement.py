from flask import Blueprint, render_template, request, redirect, url_for, g
from db import db, Requirement, TestCase, RequirementTestCase
from decorators import admin_required

bp = Blueprint('requirement', __name__, url_prefix='/requirement')

@bp.route('/')
@admin_required
def index():
    if not g.project:
        return redirect(url_for('project.select', next=url_for('requirement.index')))
    requirements = db.session.execute(
        db.select(Requirement).filter_by(project_id=g.project.id).order_by(Requirement.order.asc())
    ).scalars().all()
    return render_template('requirement/index.html', requirements=requirements)

@bp.route('/<int:requirement_id>')
@admin_required
def detail(requirement_id):
    requirement = db.get_or_404(Requirement, requirement_id)
    testcases = db.session.execute(
        db.select(TestCase).join(RequirementTestCase).filter(
            RequirementTestCase.requirement_id == requirement.id
        ).order_by(TestCase.order.asc())
    ).scalars().all()
    return render_template('requirement/detail.html', requirement=requirement, testcases=testcases)

@bp.route('/<int:requirement_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit(requirement_id):
    requirement = db.get_or_404(Requirement, requirement_id)
    if request.method == 'POST':
        requirement.title = request.form['title']
        requirement.description = request.form['description']
        requirement.priority = request.form['priority']
        db.session.commit()
        return redirect(url_for('requirement.detail', requirement_id=requirement.id))
    return render_template('requirement/edit.html', requirement=requirement)

@bp.route('/create', methods=['GET', 'POST'])
@admin_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        priority = request.form['priority']
        requirement = Requirement(title=title, description=description, priority=priority, project_id=g.project.id)
        db.session.add(requirement)
        db.session.commit()
        return redirect(url_for('requirement.detail', requirement_id=requirement.id))
    return render_template('requirement/create.html')

@bp.route('/<int:requirement_id>/delete', methods=['POST'])
@admin_required
def delete(requirement_id):
    requirement = db.get_or_404(Requirement, requirement_id)
    db.session.delete(requirement)
    db.session.commit()
    return redirect(url_for('requirement.index'))

@bp.route('/reorder', methods=['GET'])
@admin_required
def reorder():
    requirements = db.session.execute(
        db.select(Requirement).filter_by(project_id=g.project.id).order_by(Requirement.order.asc())
    ).scalars().all()
    for index, req in enumerate(requirements):
        req.order = index + 1
    db.session.commit()
    return render_template('requirement/reorder.html', requirements=requirements)

@bp.route('/<int:requirement_id1>/<int:requirement_id2>', methods=['POST'])
@admin_required
def change_order(requirement_id1, requirement_id2):
    requirement1 = db.get_or_404(Requirement, requirement_id1)
    requirement2 = db.get_or_404(Requirement, requirement_id2)
    requirement1.order, requirement2.order = requirement2.order, requirement1.order
    db.session.commit()
    return redirect(url_for('requirement.reorder'))

@bp.route('/<int:requirement_id>/associate/', methods=['GET', 'POST'])
@admin_required
def associate(requirement_id):
    requirement = db.get_or_404(Requirement, requirement_id)
    associated_ids = db.session.execute(
        db.select(RequirementTestCase.test_case_id).filter_by(requirement_id=requirement.id)
        ).scalars().all()
    testcases = db.session.execute(
        db.select(TestCase).filter_by(project_id=g.project.id).order_by(TestCase.order.asc())
    ).scalars().all()
    if request.method == 'POST':
        testcase_ids = request.form.getlist('testcase_ids')
        for testcase in testcases:
            if str(testcase.id) in testcase_ids and testcase.id not in associated_ids:
                association = RequirementTestCase(requirement_id=requirement.id, test_case_id=testcase.id)
                db.session.add(association)
            elif str(testcase.id) not in testcase_ids and testcase.id in associated_ids:
                db.session.execute(
                    db.delete(RequirementTestCase).filter_by(requirement_id=requirement.id, test_case_id=testcase.id)
                )
        db.session.commit()
        return redirect(url_for('requirement.detail', requirement_id=requirement.id))
    return render_template('requirement/associate.html', requirement=requirement, testcases=testcases, associated_ids=associated_ids)
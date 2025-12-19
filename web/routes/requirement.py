from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, g
from db import db, Requirement, RequirementTestCase, TestCase
from decorators import perm_to_view_required, perm_to_edit_required
from forms import RequirementForm

bp = Blueprint('requirement', __name__, url_prefix='/requirement')

@bp.route('/')
@perm_to_view_required
def index():
    requirements = db.session.execute(
        db.select(Requirement).filter_by(project_id=g.project.id).order_by(Requirement.order.asc())
    ).scalars().all()
    return render_template('requirement/index.html', requirements=requirements)

@bp.route('/<int:requirement_id>')
@perm_to_view_required
def detail(requirement_id):
    requirement = db.get_or_404(Requirement, requirement_id)
    testcases = db.session.execute(
        db.select(TestCase).join(RequirementTestCase).filter(
            RequirementTestCase.requirement_id == requirement_id
        ).order_by(TestCase.order.asc())
    ).scalars().all()
    return render_template('requirement/detail.html', requirement=requirement, testcases=testcases)

@bp.route('/create', methods=['GET', 'POST'])
@perm_to_edit_required
def create():
    form = RequirementForm(request.form)
    if request.method == 'POST' and form.validate():
        requirement = Requirement(title=form.title.data, description=form.description.data, priority=form.priority.data, project_id=g.project.id)
        requirement.order = requirement.last_order + 1
        db.session.add(requirement)
        db.session.commit()
        return redirect(url_for('requirement.detail', requirement_id=requirement.id))
    titles = db.session.execute(
        db.select(Requirement.title).filter_by(project_id=g.project.id)
    ).scalars().all()
    return render_template('requirement/create.html', form=form, titles=titles)

@bp.route('/<int:requirement_id>/edit', methods=['GET', 'POST'])
@perm_to_edit_required
def edit(requirement_id):
    requirement = db.get_or_404(Requirement, requirement_id)
    form = RequirementForm(request.form, obj=requirement)
    if request.method == 'POST' and form.validate():
        requirement.title = form.title.data
        requirement.description = form.description.data
        requirement.priority = form.priority.data
        requirement.updated_at = datetime.now()
        db.session.commit()
        return redirect(url_for('requirement.detail', requirement_id=requirement_id))
    return render_template('requirement/edit.html', form=form)

@bp.route('/<int:requirement_id>/delete', methods=['POST'])
@perm_to_edit_required
def delete(requirement_id):
    requirement = db.get_or_404(Requirement, requirement_id)
    db.session.delete(requirement)
    db.session.commit()
    return redirect(url_for('requirement.index'))

@bp.route('/reorder', methods=['GET'])
@perm_to_edit_required
def reorder():
    requirements = db.session.execute(
        db.select(Requirement).filter_by(project_id=g.project.id).order_by(Requirement.order.asc())
    ).scalars().all()
    for index, req in enumerate(requirements):
        req.order = index + 1
    db.session.commit()
    return render_template('requirement/reorder.html', requirements=requirements)

@bp.route('/<int:requirement_id1>/<int:requirement_id2>', methods=['POST'])
@perm_to_edit_required
def change_order(requirement_id1, requirement_id2):
    requirement1 = db.get_or_404(Requirement, requirement_id1)
    requirement2 = db.get_or_404(Requirement, requirement_id2)
    requirement1.order, requirement2.order = requirement2.order, requirement1.order
    db.session.commit()
    return redirect(url_for('requirement.reorder'))

@bp.route('/<int:requirement_id>/associate/', methods=['GET', 'POST'])
@perm_to_edit_required
def associate(requirement_id):
    requirement = db.get_or_404(Requirement, requirement_id)
    associated_ids = db.session.execute(
        db.select(RequirementTestCase.test_case_id).filter_by(requirement_id=requirement_id)
    ).scalars().all()
    testcases = db.session.execute(
        db.select(TestCase).filter_by(project_id=g.project.id).order_by(TestCase.order.asc())
    ).scalars().all()
    if request.method == 'POST':
        testcase_ids = request.form.getlist('testcase_ids')
        for testcase in testcases:
            if str(testcase.id) in testcase_ids and testcase.id not in associated_ids:
                db.session.add(RequirementTestCase(requirement_id=requirement.id, test_case_id=testcase.id))
            elif str(testcase.id) not in testcase_ids and testcase.id in associated_ids:
                db.session.execute(
                    db.delete(RequirementTestCase).filter_by(requirement_id=requirement.id, test_case_id=testcase.id)
                )
        db.session.commit()
        return redirect(url_for('requirement.detail', requirement_id=requirement_id))
    return render_template('requirement/associate.html', requirement=requirement, testcases=testcases, associated_ids=associated_ids)

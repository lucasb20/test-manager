from flask import Blueprint, render_template, request, redirect, url_for, g
from db import db, Requirement, RequirementTestCase, TestCase
from decorators import perm_to_view_required, perm_to_edit_required
from forms import RequirementForm

bp = Blueprint('requirement', __name__, url_prefix='/requirement')

@bp.route('/')
@perm_to_view_required
def index():
    requirements = db.session.execute(db.select(Requirement).filter_by(project_id=g.project.id).order_by(Requirement.order.asc())).scalars().all()
    return render_template('requirement/index.html', requirements=requirements)

@bp.route('/<int:requirement_id>')
@perm_to_view_required
def detail(requirement_id):
    requirement = db.get_or_404(Requirement, requirement_id)
    testcases = db.session.execute(db.select(TestCase).join(RequirementTestCase).filter(RequirementTestCase.requirement_id == requirement_id).order_by(TestCase.order.asc())).scalars().all()
    return render_template('requirement/detail.html', requirement=requirement, testcases=testcases)

@bp.route('/create', methods=['GET', 'POST'])
@perm_to_edit_required
def create():
    form = RequirementForm(request.form)
    if request.method == 'POST' and form.validate():
        requirement = Requirement(
            title=form.title.data,
            description=form.description.data,
            type=form.type.data,
            priority=form.priority.data,
            project_id=g.project.id
        )
        requirement.order = requirement.last_order + 1
        db.session.add(requirement)
        db.session.flush()
        tcs_ids = request.form.getlist('testcases_ids')
        for tc_id in tcs_ids:
            db.session.add(RequirementTestCase(requirement_id=requirement.id, test_case_id=tc_id))
        db.session.commit()
        return redirect(url_for('requirement.detail', requirement_id=requirement.id))
    titles = db.session.execute(db.select(Requirement.title).filter_by(project_id=g.project.id)).scalars().all()
    testcases = db.session.execute(db.select(TestCase).filter_by(project_id=g.project.id).order_by(TestCase.order.asc())).scalars().all()
    return render_template('requirement/create.html', form=form, titles=titles, testcases=testcases)

@bp.route('/<int:requirement_id>/edit', methods=['GET', 'POST'])
@perm_to_edit_required
def edit(requirement_id):
    requirement = db.get_or_404(Requirement, requirement_id)
    form = RequirementForm(request.form, obj=requirement)
    testcases = db.session.execute(db.select(TestCase).filter_by(project_id=g.project.id).order_by(TestCase.order.asc())).scalars().all()
    associated_ids = db.session.execute(db.select(RequirementTestCase.test_case_id).filter_by(requirement_id=requirement_id)).scalars().all()
    if request.method == 'POST' and form.validate():
        requirement.title = form.title.data
        requirement.description = form.description.data
        requirement.type = form.type.data
        requirement.priority = form.priority.data
        db.session.flush()
        tcs_ids = request.form.getlist('testcases_ids')
        for tc in testcases:
            if str(tc.id) in tcs_ids and tc.id not in associated_ids:
                db.session.add(RequirementTestCase(requirement_id=requirement.id, test_case_id=tc.id))
            elif str(tc.id) not in tcs_ids and tc.id in associated_ids:
                db.session.execute(db.delete(RequirementTestCase).filter_by(requirement_id=requirement.id, test_case_id=tc.id))
        db.session.commit()
        return redirect(url_for('requirement.detail', requirement_id=requirement_id))
    return render_template('requirement/edit.html', form=form, testcases=testcases, associated_ids=associated_ids)

@bp.route('/<int:requirement_id>/delete', methods=['POST'])
@perm_to_edit_required
def delete(requirement_id):
    requirement = db.get_or_404(Requirement, requirement_id)
    db.session.delete(requirement)
    db.session.commit()
    requirements = db.session.execute(db.select(Requirement).filter_by(project_id=g.project.id).order_by(Requirement.order.asc())).scalars().all()
    for index, req in enumerate(requirements):
        req.order = index + 1
    db.session.commit()
    return redirect(url_for('requirement.index'))

@bp.route('/reorder', methods=['GET'])
@perm_to_edit_required
def reorder():
    requirements = db.session.execute(db.select(Requirement).filter_by(project_id=g.project.id).order_by(Requirement.order.asc())).scalars().all()
    return render_template('requirement/reorder.html', requirements=requirements)

@bp.route('/<int:requirement_id1>/<int:requirement_id2>', methods=['POST'])
@perm_to_edit_required
def change_order(requirement_id1, requirement_id2):
    requirement1 = db.get_or_404(Requirement, requirement_id1)
    requirement2 = db.get_or_404(Requirement, requirement_id2)
    requirement1.order, requirement2.order = requirement2.order, requirement1.order
    db.session.commit()
    return redirect(url_for('requirement.reorder'))

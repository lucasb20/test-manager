from flask import Blueprint, render_template, request, redirect, url_for, g, flash, Response
from db import db, TestCase, Requirement, RequirementTestCase
from decorators import perm_to_view_required, perm_to_edit_required
from utils import create_csv, normalize_steps
from datetime import datetime, date


bp = Blueprint('testcase', __name__, url_prefix='/testcase')

@bp.route('/')
@perm_to_view_required
def index():
    testcases = db.session.execute(
        db.select(TestCase).filter_by(project_id=g.project.id).order_by(TestCase.order.asc())
    ).scalars().all()
    return render_template('testcase/index.html', testcases=testcases)

@bp.route('/<int:testcase_id>')
@perm_to_view_required
def detail(testcase_id):
    testcase = db.get_or_404(TestCase, testcase_id)
    requirements = db.session.execute(
        db.select(Requirement).join(RequirementTestCase).filter(RequirementTestCase.test_case_id == testcase_id)
    ).scalars().all()
    return render_template('testcase/detail.html', testcase=testcase, requirements=requirements)

@bp.route('/<int:testcase_id>/edit', methods=['GET', 'POST'])
@perm_to_edit_required
def edit(testcase_id):
    testcase = db.get_or_404(TestCase, testcase_id)
    if request.method == 'POST':
        testcase.title = request.form['title']
        testcase.preconditions = request.form['preconditions']
        testcase.steps = normalize_steps(request.form['steps'])
        testcase.expected_result = request.form['expected_result']
        testcase.is_functional = request.form['functional'] == 'functional'
        testcase.is_automated = request.form.get('automation') == 'on'
        testcase.updated_at = datetime.now()
        db.session.commit()
        return redirect(url_for('testcase.detail', testcase_id=testcase.id))
    return render_template('testcase/edit.html', testcase=testcase)

@bp.route('/create', methods=['GET', 'POST'])
@perm_to_edit_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        preconditions = request.form['preconditions']
        steps = normalize_steps(request.form['steps'])
        expected_result = request.form['expected_result']
        functional = request.form['functional'] == 'functional'
        automation = request.form['automation'] == 'on'
        testcase = TestCase(title=title, preconditions=preconditions, steps=steps, expected_result=expected_result, project_id=g.project.id, is_functional=functional, is_automated=automation)
        testcase.order = testcase.last_order + 1
        db.session.add(testcase)
        db.session.commit()
        flash(f'{testcase.code_with_prefix} created successfully.')
        return redirect(url_for('testcase.index'))
    return render_template('testcase/create.html')

@bp.route('/<int:testcase_id>/delete', methods=['POST'])
@perm_to_edit_required
def delete(testcase_id):
    testcase = db.get_or_404(TestCase, testcase_id)
    db.session.delete(testcase)
    db.session.commit()
    return redirect(url_for('testcase.index'))

@bp.route('/reorder', methods=['GET'])
@perm_to_edit_required
def reorder():
    testcases = db.session.execute(
        db.select(TestCase).filter_by(project_id=g.project.id).order_by(TestCase.order.asc())
    ).scalars().all()
    for index, tc in enumerate(testcases):
        tc.order = index + 1
    db.session.commit()
    return render_template('testcase/reorder.html', testcases=testcases)

@bp.route('/<int:testcase_id1>/<int:testcase_id2>', methods=['POST'])
@perm_to_edit_required
def change_order(testcase_id1, testcase_id2):
    testcase1 = db.get_or_404(TestCase, testcase_id1)
    testcase2 = db.get_or_404(TestCase, testcase_id2)
    testcase1.order, testcase2.order = testcase2.order, testcase1.order
    db.session.commit()
    return redirect(url_for('testcase.reorder'))

@bp.route('/<int:testcase_id>/associate', methods=['GET', 'POST'])
@perm_to_edit_required
def associate(testcase_id):
    testcase = db.get_or_404(TestCase, testcase_id)
    requirements = db.session.execute(
        db.select(Requirement).filter_by(project_id=g.project.id)
    ).scalars().all()
    associated_ids = db.session.execute(
        db.select(RequirementTestCase.requirement_id).filter_by(test_case_id=testcase_id)
    ).scalars().all()
    if request.method == 'POST':
        requirement_ids = request.form.getlist('requirement_ids')
        for req in requirements:
            if str(req.id) in requirement_ids and req.id not in associated_ids:
                association = RequirementTestCase(requirement_id=req.id, test_case_id=testcase_id)
                db.session.add(association)
            elif str(req.id) not in requirement_ids and req.id in associated_ids:
                association = db.session.execute(
                    db.delete(RequirementTestCase).filter_by(requirement_id=req.id, test_case_id=testcase_id)
                )
        db.session.commit()
        return redirect(url_for('testcase.detail', testcase_id=testcase_id))
    return render_template('testcase/associate.html', testcase=testcase, requirements=requirements, associated_ids=associated_ids)

@bp.route('/export', methods=['GET'])
@perm_to_view_required
def export():
    testcases = db.session.execute(
        db.select(TestCase).filter_by(project_id=g.project.id).order_by(TestCase.order.asc())
    ).scalars().all()
    data = [("ID", "Title", "Requirements", "Preconditions", "Steps", "Expected Result", "Type", "Automated")]
    for tc in testcases:
        data.append((tc.code_with_prefix, tc.title, tc.requirements_codes, tc.preconditions, tc.steps, tc.expected_result, tc.functional, tc.automation))
    csv_data = create_csv(data)
    filename = f"testcases_{g.project.name.casefold()}_{date.today()}.csv"
    response = Response(
        csv_data,
        mimetype='text/csv',
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )
    return response
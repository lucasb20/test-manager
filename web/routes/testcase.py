from flask import Blueprint, render_template, request, redirect, url_for, g, flash, Response
from services.testcase import create_testcase, get_testcases, get_testcase, edit_testcase, delete_testcase, update_orders, update_pair
from services.requirement import get_requirements
from services.associate import create_associations_to_testcase, get_requirements_for_testcase, get_associated_requirement_ids
from decorators import perm_to_view_required, perm_to_edit_required
from utils import create_csv
from datetime import date


bp = Blueprint('testcase', __name__, url_prefix='/testcase')

@bp.route('/')
@perm_to_view_required
def index():
    testcases = get_testcases(g.project.id)
    return render_template('testcase/index.html', testcases=testcases)

@bp.route('/<int:testcase_id>')
@perm_to_view_required
def detail(testcase_id):
    testcase = get_testcase(testcase_id)
    requirements = get_requirements_for_testcase(testcase_id)
    return render_template('testcase/detail.html', testcase=testcase, requirements=requirements)

@bp.route('/<int:testcase_id>/edit', methods=['GET', 'POST'])
@perm_to_edit_required
def edit(testcase_id):
    if request.method == 'POST':
        title = request.form['title']
        preconditions = request.form['preconditions']
        steps = request.form['steps']
        expected_result = request.form['expected_result']
        is_functional = request.form['functional'] == 'functional'
        is_automated = request.form.get('automation') == 'on'
        testcase = edit_testcase(testcase_id, title, preconditions, steps, expected_result, is_functional, is_automated)
        return redirect(url_for('testcase.detail', testcase_id=testcase.id))
    testcase = get_testcase(testcase_id)
    return render_template('testcase/edit.html', testcase=testcase)

@bp.route('/create', methods=['GET', 'POST'])
@perm_to_edit_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        preconditions = request.form['preconditions']
        steps = request.form['steps']
        expected_result = request.form['expected_result']
        functional = request.form['functional'] == 'functional'
        automation = request.form.get('automation') == 'on'
        testcase = create_testcase(title, preconditions, steps, expected_result, g.project.id, functional, automation)
        flash(f'{testcase.code_with_prefix} created successfully.')
        return redirect(url_for('testcase.index'))
    return render_template('testcase/create.html')

@bp.route('/<int:testcase_id>/delete', methods=['POST'])
@perm_to_edit_required
def delete(testcase_id):
    delete_testcase(testcase_id)
    return redirect(url_for('testcase.index'))

@bp.route('/reorder', methods=['GET'])
@perm_to_edit_required
def reorder():
    testcases = update_orders(g.project.id)
    return render_template('testcase/reorder.html', testcases=testcases)

@bp.route('/<int:testcase_id1>/<int:testcase_id2>', methods=['POST'])
@perm_to_edit_required
def change_order(testcase_id1, testcase_id2):
    update_pair(testcase_id1, testcase_id2)
    return redirect(url_for('testcase.reorder'))

@bp.route('/<int:testcase_id>/associate', methods=['GET', 'POST'])
@perm_to_edit_required
def associate(testcase_id):
    testcase = get_testcase(testcase_id)
    requirements = get_requirements(g.project.id)
    associated_ids = get_associated_requirement_ids(testcase_id)
    if request.method == 'POST':
        requirement_ids = request.form.getlist('requirement_ids')
        create_associations_to_testcase(testcase_id, requirement_ids)
        flash('Requirements associated successfully.')
        return redirect(url_for('testcase.detail', testcase_id=testcase_id))
    return render_template('testcase/associate.html', testcase=testcase, requirements=requirements, associated_ids=associated_ids)

@bp.route('/export', methods=['GET'])
@perm_to_view_required
def export():
    testcases = get_testcases(g.project.id)
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
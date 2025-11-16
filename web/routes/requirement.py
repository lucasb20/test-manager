from flask import Blueprint, render_template, request, redirect, url_for, g, flash
from services.requirement import create_requirement, get_requirements, get_requirement, edit_requirement, delete_requirement, update_orders, update_pair
from services.associate import create_associations_to_requirement, get_associated_testcase_ids, get_testcases_for_requirement
from services.testcase import get_testcases
from decorators import perm_to_view_required, perm_to_edit_required


bp = Blueprint('requirement', __name__, url_prefix='/requirement')

@bp.route('/')
@perm_to_view_required
def index():
    if not g.project:
        return redirect(url_for('project.select', next=url_for('requirement.index')))
    requirements = get_requirements(g.project.id)
    return render_template('requirement/index.html', requirements=requirements)

@bp.route('/<int:requirement_id>')
@perm_to_view_required
def detail(requirement_id):
    requirement = get_requirement(requirement_id)
    testcases = get_testcases_for_requirement(requirement_id)
    return render_template('requirement/detail.html', requirement=requirement, testcases=testcases)

@bp.route('/<int:requirement_id>/edit', methods=['GET', 'POST'])
@perm_to_edit_required
def edit(requirement_id):
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        priority = request.form['priority']
        edit_requirement(requirement_id, title, description, priority)
        flash('Requirement updated successfully.')
        return redirect(url_for('requirement.detail', requirement_id=requirement_id))
    requirement = get_requirement(requirement_id)
    return render_template('requirement/edit.html', requirement=requirement)

@bp.route('/create', methods=['GET', 'POST'])
@perm_to_edit_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        priority = request.form['priority']
        requirement = create_requirement(title, description, priority, g.project.id)
        flash(f'{requirement.code_with_prefix} created successfully.')
        return redirect(url_for('requirement.detail', requirement_id=requirement.id))
    return render_template('requirement/create.html')

@bp.route('/<int:requirement_id>/delete', methods=['POST'])
@perm_to_edit_required
def delete(requirement_id):
    delete_requirement(requirement_id)
    return redirect(url_for('requirement.index'))

@bp.route('/reorder', methods=['GET'])
@perm_to_edit_required
def reorder():
    requirements = update_orders(g.project.id)
    return render_template('requirement/reorder.html', requirements=requirements)

@bp.route('/<int:requirement_id1>/<int:requirement_id2>', methods=['POST'])
@perm_to_edit_required
def change_order(requirement_id1, requirement_id2):
    update_pair(requirement_id1, requirement_id2)
    return redirect(url_for('requirement.reorder'))

@bp.route('/<int:requirement_id>/associate/', methods=['GET', 'POST'])
@perm_to_edit_required
def associate(requirement_id):
    requirement = get_requirement(requirement_id)
    if request.method == 'POST':
        testcase_ids = request.form.getlist('testcase_ids')
        create_associations_to_requirement(requirement_id, testcase_ids)
        flash('Test cases associated successfully.')
        return redirect(url_for('requirement.detail', requirement_id=requirement.id))
    associated_ids = get_associated_testcase_ids(requirement_id)
    testcases = get_testcases(g.project.id)
    return render_template('requirement/associate.html', requirement=requirement, testcases=testcases, associated_ids=associated_ids)
from datetime import date
from flask import Blueprint, render_template, request, g, redirect, url_for, session, send_file, flash
from sqlalchemy.exc import IntegrityError
from services.project import create_project, delete_project, edit_project, get_project, get_projects, ProjectForm
from services.requirement import get_requirements, create_requirement
from services.testcase import get_testcases, create_testcase
from services.associate import create_associations_with_codes
from decorators import login_required, perm_to_view_required, perm_to_manage_required
from utils import create_json, import_json


bp = Blueprint('project', __name__, url_prefix='/project')

@bp.route('/')
@login_required
def index():
    projects = get_projects(g.user)
    return render_template('project/index.html', projects=projects)

@bp.route('/select', methods=['GET', 'POST'])
@login_required
def select():
    next_url = request.form.get('next')
    if request.method == 'POST':
        project_id = request.form['project_id']
        project = get_project(project_id)
        session['project_id'] = project.id
        return redirect(next_url or url_for('project.index'))
    projects = get_projects(g.user)
    return render_template('project/select.html', projects=projects)

@bp.route('/<int:project_id>')
@perm_to_view_required
def detail(project_id):
    project = get_project(project_id)
    return render_template('project/detail.html', project=project)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = ProjectForm(request.form)
    if request.method == 'POST' and form.validate():
        try:
            project = create_project(form.name.data, form.description.data, g.user.id)
            return redirect(url_for('project.detail', project_id=project.id))
        except IntegrityError as e:
            flash('Project with this name already exists.')
    return render_template('project/create.html', form=form)

@bp.route('/<int:project_id>/edit', methods=['GET', 'POST'])
@perm_to_manage_required
def edit(project_id):
    form = ProjectForm(request.form)
    if request.method == 'POST' and form.validate():
        try:
            edit_project(project_id, form.name.data, form.description.data)
            return redirect(url_for('project.detail', project_id=project_id))
        except IntegrityError as e:
            flash('Project with this name already exists.')
    project = get_project(project_id)
    form.name.data = project.name
    form.description.data = project.description
    return render_template('project/edit.html', form=form, project=project)

@bp.route('/<int:project_id>/delete', methods=['POST'])
@perm_to_manage_required
def delete(project_id):
    delete_project(project_id)
    return redirect(url_for('project.index'))

@bp.route('/<int:project_id>/export')
@perm_to_view_required
def export(project_id):
    project = get_project(project_id)
    requirements = get_requirements(project_id)
    testcases = get_testcases(project_id)
    project_data = {
        'name': project.name,
        'description': project.description,
        'requirements': [
            {
                'id': req.code_with_prefix,
                'title': req.title,
                'description': req.description,
                'priority': req.priority,
                'created_at': req.created_at.isoformat(),
            } for req in requirements
        ],
        'testcases': [
            {
                'id': tc.code_with_prefix,
                'title': tc.title,
                'requirements': tc.requirements_codes,
                'preconditions': tc.preconditions,
                'steps': tc.steps,
                'expected_result': tc.expected_result,
                'is_functional': tc.is_functional,
                'is_automated': tc.is_automated,
                'created_at': tc.created_at.isoformat()
            } for tc in testcases
        ]
    }
    buffer = create_json(project_data)
    filename = f"{project.name.casefold()}_{date.today()}.json"
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/json'
    )

@bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_project():
    if request.method == 'POST':
        file = request.files['file']
        if not file or not file.filename.endswith('.json'):
            flash('No file selected or incorrect file type.')
        else:
            data = import_json(file)
            project = create_project(
                name=data['name'],
                description=data.get('description', ''),
                owner_id=g.user.id
            )
            for req_data in data.get('requirements', []):
                create_requirement(
                    project_id=project.id,
                    title=req_data.get('title'),
                    description=req_data.get('description', ''),
                    priority=req_data.get('priority')
                )
            for tc_data in data.get('testcases', []):
                tc = create_testcase(
                    project_id=project.id,
                    title=tc_data.get('title'),
                    preconditions=tc_data.get('preconditions', ''),
                    steps=tc_data.get('steps', ''),
                    expected_result=tc_data.get('expected_result', ''),
                    is_functional=tc_data.get('is_functional', True),
                    is_automated=tc_data.get('is_automated', False)
                )
                create_associations_with_codes(tc.id, tc_data.get('requirements', ''))
            flash('Project imported successfully.')
            return redirect(url_for('project.index'))
    return render_template('project/import.html')

@bp.before_app_request
def load_project():
    project_id = session.get('project_id')
    if project_id is None:
        g.project = None
    else:
        g.project = get_project(project_id)

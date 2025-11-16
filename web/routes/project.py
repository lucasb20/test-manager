from flask import Blueprint, render_template, request, g, redirect, url_for, session, send_file, flash
from services.project import create_project, delete_project, edit_project, get_project, get_projects
from services.requirement import get_requirements, create_requirement
from services.testcase import get_testcases, create_testcase
from services.associate import create_associations_with_codes
from decorators import login_required, perm_to_view_required, perm_to_manage_required
from utils import create_json, import_json
from datetime import date


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
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        project = create_project(name, description, g.user.id)
        return redirect(url_for('project.detail', project_id=project.id))
    return render_template('project/create.html')

@bp.route('/<int:project_id>/edit', methods=['GET', 'POST'])
@perm_to_manage_required
def edit(project_id):
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        edit_project(project_id, name, description)
        return redirect(url_for('project.detail', project_id=project_id))
    project = get_project(project_id)
    return render_template('project/edit.html', project=project)

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
                    title=req_data['title'],
                    description=req_data.get('description', ''),
                    priority=req_data.get('priority')
                )
            for tc_data in data.get('testcases', []):
                tc = create_testcase(
                    project_id=project.id,
                    title=tc_data['title'],
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
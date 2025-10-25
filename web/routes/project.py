from flask import Blueprint, render_template, request, g, redirect, url_for, session
from db import db, User, Project, ProjectMember
from decorators import login_required, perm_to_view_required, perm_to_manage_required

bp = Blueprint('project', __name__, url_prefix='/project')


@bp.route('/')
@login_required
def index():
    if g.user.is_admin:
        projects = db.session.execute(db.select(Project)).scalars()
    else:
        projects = db.session.execute(
            db.select(Project).join(ProjectMember).filter(ProjectMember.user_id == g.user.id)
        ).scalars()
    return render_template('project/index.html', projects=projects)

@bp.route('/select', methods=['GET', 'POST'])
@login_required
def select():
    next_url = request.form.get('next')
    if request.method == 'POST':
        project_id = request.form['project_id']
        project = db.get_or_404(Project, project_id)
        session['project_id'] = project.id
        return redirect(next_url or url_for('project.index'))
    if g.user.is_admin:
        projects = db.session.execute(db.select(Project)).scalars().all()
    else:
        projects = db.session.execute(
            db.select(Project).join(ProjectMember).filter(ProjectMember.user_id == g.user.id)
        ).scalars().all()
    return render_template('project/select.html', projects=projects)

@bp.route('/<int:project_id>')
@login_required
def detail(project_id):
    project = db.get_or_404(Project, project_id)
    manager = db.get_or_404(User, project.manager_id)
    return render_template('project/detail.html', project=project, manager=manager)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        project = Project(name=name, description=description, manager_id=g.user.id)
        db.session.add(project)
        db.session.commit()
        project_member = ProjectMember(project_id=project.id, user_id=g.user.id, role="manager")
        db.session.add(project_member)
        db.session.commit()
        return redirect(url_for('project.detail', project_id=project.id))
    return render_template('project/create.html')

@bp.route('/<int:project_id>/edit', methods=['GET', 'POST'])
@perm_to_manage_required
def edit(project_id):
    project = db.get_or_404(Project, project_id)
    if request.method == 'POST':
        project.name = request.form['name']
        project.description = request.form['description']
        db.session.commit()
        return redirect(url_for('project.detail', project_id=project.id))
    return render_template('project/edit.html', project=project)

@bp.route('/<int:project_id>/delete', methods=['POST'])
@perm_to_manage_required
def delete(project_id):
    project = db.get_or_404(Project, project_id)
    project_members = db.session.execute(
        db.select(ProjectMember).filter_by(project_id=project.id)
    ).scalars()
    for member in project_members:
        db.session.delete(member)
    db.session.delete(project)
    db.session.commit()
    return redirect(url_for('project.index'))

@bp.before_app_request
def load_project():
    project_id = session.get('project_id')
    if project_id is None:
        g.project = None
    else:
        g.project = db.one_or_404(db.select(Project).filter_by(id=project_id))
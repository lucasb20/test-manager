from datetime import date
from flask import Blueprint, render_template, request, g, redirect, url_for, session, send_file, flash
from sqlalchemy.exc import IntegrityError
from decorators import login_required, perm_to_view_required, perm_to_manage_required
from db import db, Project, ProjectMember, Requirement, RequirementTestCase, TestCase, Bug, BugTestCase
from utils import create_json, import_json
from forms import ProjectForm

bp = Blueprint('project', __name__, url_prefix='/project')

@bp.route('/')
@login_required
def index():
    projects = db.session.execute(db.select(Project).join(ProjectMember).filter(ProjectMember.user_id == g.user.id)).scalars().all()
    return render_template('project/index.html', projects=projects)

@bp.route('/select', methods=['GET', 'POST'])
@login_required
def select():
    if request.method == 'POST':
        session['project_id'] = request.form['project_id']
        return redirect(request.args.get('next') or url_for('project.index'))
    projects = db.session.execute(db.select(Project).join(ProjectMember).filter(ProjectMember.user_id == g.user.id)).scalars().all()
    return render_template('project/select.html', projects=projects)

@bp.route('/<int:project_id>')
@perm_to_view_required
def detail(project_id):
    project = db.get_or_404(Project, project_id)
    total_reqs = db.session.execute(db.select(db.func.count()).select_from(Requirement).filter_by(project_id=project.id)).scalar()
    total_tcs = db.session.execute(db.select(db.func.count()).select_from(TestCase).filter_by(project_id=project.id)).scalar()
    total_bugs = db.session.execute(db.select(db.func.count()).select_from(Bug).filter_by(project_id=project.id)).scalar()
    data = {
        "total_reqs": total_reqs,
        "total_tcs": total_tcs,
        "total_bugs": total_bugs
    }
    return render_template('project/detail.html', project=project, data=data)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = ProjectForm(request.form)
    if request.method == 'POST' and form.validate():
        try:
            project = Project(
                name=form.name.data,
                description=form.description.data,
                manager_id=g.user.id
            )
            db.session.add(project)
            db.session.flush()
            db.session.add(ProjectMember(project_id=project.id, user_id=g.user.id, role="manager"))
            db.session.commit()
            return redirect(url_for('project.detail', project_id=project.id))
        except IntegrityError:
            db.session.rollback()
            flash('Project with this name already exists.')
    return render_template('project/create.html', form=form)

@bp.route('/<int:project_id>/edit', methods=['GET', 'POST'])
@perm_to_manage_required
def edit(project_id):
    project = db.get_or_404(Project, project_id)
    form = ProjectForm(request.form, obj=project)
    if request.method == 'POST' and form.validate():
        try:
            project.name = form.name.data
            project.description = form.description.data
            db.session.commit()
            return redirect(url_for('project.detail', project_id=project_id))
        except IntegrityError:
            flash('Project with this name already exists.')
    return render_template('project/edit.html', form=form)

@bp.route('/<int:project_id>/delete', methods=['POST'])
@perm_to_manage_required
def delete(project_id):
    project = db.get_or_404(Project, project_id)
    db.session.delete(project)
    db.session.commit()
    return redirect(url_for('project.index'))

@bp.route('/<int:project_id>/export')
@perm_to_view_required
def export(project_id):
    project = db.get_or_404(Project, project_id)
    requirements = db.session.execute(db.select(Requirement).filter_by(project_id=project_id).order_by(Requirement.order.asc())).scalars().all()
    testcases = db.session.execute(db.select(TestCase).filter_by(project_id=project_id).order_by(TestCase.order.asc())).scalars().all()
    bugs = db.session.execute(db.select(Bug).filter_by(project_id=project_id).order_by(Bug.order.asc())).scalars().all()
    project_data = {
        'name': project.name,
        'description': project.description,
        'requirements': {
            req.code_with_prefix: {
                'title': req.title,
                'description': req.description,
                'type': req.type,
                'priority': req.priority
            } for req in requirements
        },
        'testcases': {
            tc.code_with_prefix: {
                'title': tc.title,
                'requirements': ', '.join(tc.requirements_codes),
                'preconditions': tc.preconditions,
                'steps': tc.steps,
                'expected_result': tc.expected_result
            } for tc in testcases
        },
        'bugs': {
            bug.code_with_prefix:{
                'title': bug.title,
                'description': bug.description,
                'testcases': ', '.join(bug.testcases_codes),
                'is_closed': bug.is_closed,
                'priority': bug.priority
            } for bug in bugs
        }
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
            try:
                project = Project(
                    name=data.get('name'),
                    description=data.get('description', ''),
                    manager_id=g.user.id
                )
                db.session.add(project)
                db.session.flush()
                project_member = ProjectMember(project_id=project.id, user_id=g.user.id, role="manager")
                db.session.add(project_member)
                reqs = {}
                order = 1
                for code, req_data in data.get('requirements', {}).items():
                    req = Requirement(
                        project_id=project.id,
                        title=req_data.get('title'),
                        description=req_data.get('description', ''),
                        type=req_data.get('type'),
                        priority=req_data.get('priority', 'high'),
                        order=order
                    )
                    db.session.add(req)
                    reqs[code] = req
                    order += 1
                db.session.flush()
                tcs = {}
                order = 1
                for code, tc_data in data.get('testcases', {}).items():
                    tc = TestCase(
                        project_id=project.id,
                        title=tc_data.get('title'),
                        preconditions=tc_data.get('preconditions'),
                        steps=tc_data.get('steps'),
                        expected_result=tc_data.get('expected_result'),
                        order=order
                    )
                    db.session.add(tc)
                    tcs[code] = tc
                    db.session.flush()
                    for req_code in tc_data.get('requirements', '').split(', '):
                        if req_code in reqs:
                            rtc = RequirementTestCase(
                                requirement_id=reqs[req_code].id,
                                test_case_id=tc.id
                            )
                            db.session.add(rtc)
                    order += 1
                order = 1
                for bug_data in data.get('bugs', {}).values():
                    bug = Bug(
                        project_id=project.id,
                        title=bug_data.get('title'),
                        description=bug_data.get('description'),
                        is_closed=bug_data.get('is_closed'),
                        priority=bug_data.get('priority'),
                        order=order
                    )
                    db.session.add(bug)
                    db.session.flush()
                    for tc_code in bug_data.get('testcases', '').split(', '):
                        if tc_code in tcs:
                            db.session.add(BugTestCase(bug_id=bug.id, test_case_id=tcs[tc_code].id))
                    order += 1
                db.session.commit()
                return redirect(url_for('project.detail', project_id=project.id))
            except IntegrityError:
                db.session.rollback()
                flash('Project with this name already exists.')
    return render_template('project/import.html')

@bp.before_app_request
def load_project():
    project_id = session.get('project_id')
    if project_id is None:
        g.project = None
    else:
        g.project = db.session.get(Project, project_id)

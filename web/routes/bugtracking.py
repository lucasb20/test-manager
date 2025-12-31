from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, g
from db import db, Bug, TestCase, BugTestCase
from decorators import perm_to_view_required, perm_to_edit_required
from forms import BugForm

bp = Blueprint('bugtracking', __name__, url_prefix='/bugtracking')

@bp.route('/')
@perm_to_view_required
def index():
    bugs = db.session.execute(
        db.select(Bug).order_by(Bug.created_at.desc())
    ).scalars().all()
    priority = {"High": 0, "Medium": 1, "Low": 2}
    status = {"Open": 0, "Progress": 0, "Closed": 2}
    bugs.sort(key=lambda b: ((status.get(b.status, 3)), priority.get(b.priority, 3)))
    return render_template('bugtracking/index.html', bugs=bugs)

@bp.route('/create', methods=['GET', 'POST'])
@perm_to_edit_required
def create():
    form = BugForm(request.form)
    if request.method == 'POST' and form.validate():
        bug = Bug(title=form.title.data, description=form.description.data, status=form.status.data, priority=form.priority.data, reported_by=g.user.id, project_id=g.project.id)
        bug.order = bug.last_order + 1
        db.session.add(bug)
        db.session.commit()
        return redirect(url_for('bugtracking.detail,', bug_id=bug.id))
    return render_template('bugtracking/create.html', form=form)

@bp.route('/<int:bug_id>')
@perm_to_view_required
def detail(bug_id):
    bug = db.get_or_404(Bug, bug_id)
    testcases = db.session.execute(
        db.select(TestCase).join(BugTestCase).filter(BugTestCase.bug_id == bug_id)
    ).scalars().all()
    return render_template('bugtracking/detail.html', bug=bug, testcases=testcases)

@bp.route('/<int:bug_id>/edit', methods=['GET', 'POST'])
@perm_to_edit_required
def edit(bug_id):
    bug = db.get_or_404(Bug, bug_id)
    form = BugForm(request.form, obj=bug)
    if request.method == 'POST' and form.validate():
        bug.title = form.title.data
        bug.description = form.description.data
        bug.status = form.status.data
        bug.priority = form.priority.data
        bug.updated_at = datetime.now()
        db.session.commit()
        return redirect(url_for('bugtracking.detail', bug_id=bug.id))
    return render_template('bugtracking/edit.html', form=form)

@bp.route('/<int:bug_id>/delete', methods=['POST'])
@perm_to_edit_required
def delete(bug_id):
    bug = db.get_or_404(Bug, bug_id)
    db.session.delete(bug)
    db.session.commit()
    return redirect(url_for('bugtracking.index'))

@bp.route('/<int:bug_id>/associate', methods=['GET', 'POST'])
@perm_to_edit_required
def associate(bug_id):
    bug = db.get_or_404(Bug, bug_id)
    associated_ids = db.session.execute(
        db.select(BugTestCase.test_case_id).filter(BugTestCase.bug_id == bug_id)
    ).scalars().all()
    testcases = db.session.execute(
        db.select(TestCase).filter(TestCase.project_id == g.project.id)
    ).scalars().all()
    if request.method == 'POST':
        testcases_ids = request.form.getlist('testcase_ids')
        for tc in testcases:
            if str(tc.id) in testcases_ids and tc.id not in associated_ids:
                db.session.add(BugTestCase(bug_id=bug.id, test_case_id=tc.id))
            elif str(tc.id) not in testcases_ids and tc.id in associated_ids:
                db.session.execute(db.delete(BugTestCase).where(BugTestCase.bug_id == bug.id, BugTestCase.test_case_id == tc.id))
        db.session.commit()
        return redirect(url_for('bugtracking.detail', bug_id=bug.id))
    return render_template('bugtracking/associate.html', bug=bug, testcases=testcases, associated_ids=associated_ids)

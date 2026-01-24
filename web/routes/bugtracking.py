from flask import Blueprint, render_template, request, redirect, url_for, g
from db import db, Bug, TestCase, BugTestCase
from decorators import perm_to_view_required, perm_to_edit_required
from forms import BugForm

bp = Blueprint('bugtracking', __name__, url_prefix='/bugtracking')

@bp.route('/')
@perm_to_view_required
def index():
    bugs = db.session.execute(db.select(Bug).filter_by(project_id=g.project.id).order_by(Bug.created_at.desc())).scalars().all()
    priority = {'high': 0, 'medium': 1, 'low': 2}
    status = {'open': 0, 'progress': 0, 'closed': 1}
    bugs.sort(key=lambda b: ((status.get(b.status, 3)), priority.get(b.priority, 3)))
    open_bugs = [bug for bug in bugs if bug.status != 'closed']
    high_open_bugs = sum(1 for bug in open_bugs if bug.priority == 'high')
    medium_open_bugs = sum(1 for bug in open_bugs if bug.priority == 'medium')
    low_open_bugs = len(open_bugs) - high_open_bugs - medium_open_bugs
    data = {
        'open_bugs': len(open_bugs),
        'high_open_bugs': high_open_bugs,
        'medium_open_bugs': medium_open_bugs,
        'low_open_bugs': low_open_bugs
    }
    return render_template('bugtracking/index.html', bugs=bugs, data=data)

@bp.route('/create', methods=['GET', 'POST'])
@perm_to_edit_required
def create():
    form = BugForm(request.form)
    testcases = db.session.execute(db.select(TestCase).filter(TestCase.project_id == g.project.id)).scalars().all()
    if request.method == 'POST' and form.validate():
        bug = Bug(
            title=form.title.data,
            description=form.description.data,
            status=form.status.data,
            priority=form.priority.data,
            reported_by=g.user.id,
            project_id=g.project.id
        )
        bug.order = bug.last_order + 1
        db.session.add(bug)
        db.session.flush()
        tcs_ids = request.form.getlist('testcases_ids')
        for tc_id in tcs_ids:
            db.session.add(BugTestCase(bug_id=bug.id, test_case_id=tc_id))
        db.session.commit()
        return redirect(url_for('bugtracking.detail', bug_id=bug.id))
    return render_template('bugtracking/create.html', form=form, testcases=testcases)

@bp.route('/<int:bug_id>')
@perm_to_view_required
def detail(bug_id):
    bug = db.get_or_404(Bug, bug_id)
    testcases = db.session.execute(db.select(TestCase).join(BugTestCase).filter(BugTestCase.bug_id == bug_id)).scalars().all()
    return render_template('bugtracking/detail.html', bug=bug, testcases=testcases)

@bp.route('/<int:bug_id>/edit', methods=['GET', 'POST'])
@perm_to_edit_required
def edit(bug_id):
    bug = db.get_or_404(Bug, bug_id)
    form = BugForm(request.form, obj=bug)
    associated_ids = db.session.execute(db.select(BugTestCase.test_case_id).filter(BugTestCase.bug_id == bug_id)).scalars().all()
    testcases = db.session.execute(db.select(TestCase).filter(TestCase.project_id == g.project.id)).scalars().all()
    if request.method == 'POST' and form.validate():
        bug.title = form.title.data
        bug.description = form.description.data
        bug.status = form.status.data
        bug.priority = form.priority.data
        db.session.flush()
        tcs_ids = request.form.getlist('testcases_ids')
        for tc in testcases:
            if str(tc.id) in tcs_ids and tc.id not in associated_ids:
                db.session.add(BugTestCase(bug_id=bug.id, test_case_id=tc.id))
            elif str(tc.id) not in tcs_ids and tc.id in associated_ids:
                db.session.execute(db.delete(BugTestCase).filter_by(bug_id=bug.id, test_case_id=tc.id))
        db.session.commit()
        return redirect(url_for('bugtracking.detail', bug_id=bug.id))
    return render_template('bugtracking/edit.html', form=form, testcases=testcases, associated_ids=associated_ids)

@bp.route('/<int:bug_id>/delete', methods=['POST'])
@perm_to_edit_required
def delete(bug_id):
    bug = db.get_or_404(Bug, bug_id)
    db.session.delete(bug)
    db.session.commit()
    return redirect(url_for('bugtracking.index'))

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, g
from db import db, Bug
from decorators import perm_to_view_required, perm_to_edit_required
from forms import BugForm

bp = Blueprint('bugtracking', __name__, url_prefix='/bugtracking')

@bp.route('/')
@perm_to_view_required
def index():
    bugs = db.session.execute(
        db.select(Bug).order_by(Bug.created_at.desc())
    ).scalars().all()
    return render_template('bugtracking/index.html', bugs=bugs)

@bp.route('/create', methods=['GET', 'POST'])
@perm_to_edit_required
def create():
    form = BugForm(request.form)
    if request.method == 'POST' and form.validate():
        bug = Bug(description=form.description.data, status=form.status.data, priority=form.priority.data, reported_by=g.user.id, project_id=g.project.id)
        db.session.add(bug)
        db.session.commit()
        return redirect(url_for('bugtracking.index'))
    return render_template('bugtracking/create.html', form=form)

@bp.route('/<int:bug_id>')
@perm_to_view_required
def detail(bug_id):
    bug = db.get_or_404(Bug, bug_id)
    return render_template('bugtracking/detail.html', bug=bug)

@bp.route('/<int:bug_id>/edit', methods=['GET', 'POST'])
@perm_to_edit_required
def edit(bug_id):
    bug = db.get_or_404(Bug, bug_id)
    form = BugForm(request.form, obj=bug)
    if request.method == 'POST' and form.validate():
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
    db.session.execute(db.delete(Bug).where(Bug.id == bug_id))
    db.session.commit()
    return redirect(url_for('bugtracking.index'))

@bp.route('/reorder')
@perm_to_edit_required
def reorder():
    bugs = db.session.execute(
        db.select(Bug).order_by(Bug.order)
    ).scalars().all()
    for index, bug in enumerate(bugs):
        bug.order = index + 1
    db.session.commit()
    return redirect(url_for('bugtracking.index'))

import functools
from flask import g, redirect, url_for, flash, request
from db import db, Project, ProjectMember

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(*args, **kwargs)
    return wrapped_view

def project_selected_required(view):
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.project is None and 'project_id' not in request.view_args:
            return redirect(url_for('project.select', next=url_for(request.endpoint, **kwargs)))
        if g.project is None:
            g.project = db.get_or_404(Project, request.view_args['project_id'])
        return view(*args, **kwargs)
    return login_required(wrapped_view)

def perm_to_view_required(view):
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        role = db.session.execute(
            db.select(ProjectMember.role).filter_by(user_id=g.user.id, project_id=g.project.id)
        ).scalar()
        if role not in ('manager', 'editor', 'viewer'):
            flash('You do not have permission to view this project.')
            return redirect(request.referrer or url_for('index'))
        return view(*args, **kwargs)
    return project_selected_required(wrapped_view)

def perm_to_edit_required(view):
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        role = db.session.execute(
            db.select(ProjectMember.role).filter_by(user_id=g.user.id, project_id=g.project.id)
        ).scalar()
        if role not in ('manager', 'editor'):
            flash('You do not have permission to edit this project.')
            return redirect(request.referrer or url_for('index'))
        return view(*args, **kwargs)
    return project_selected_required(wrapped_view)

def perm_to_manage_required(view):
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        role = db.session.execute(
            db.select(ProjectMember.role).filter_by(user_id=g.user.id, project_id=g.project.id)
        ).scalar()
        if role != 'manager':
            flash('You do not have permission to manage this project.')
            return redirect(request.referrer or url_for('index'))
        return view(*args, **kwargs)
    return project_selected_required(wrapped_view)

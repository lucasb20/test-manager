from flask import Blueprint, render_template, request, redirect, url_for, g, flash
from db import db, ProjectMember, User
from decorators import perm_to_view_required, perm_to_manage_required

bp = Blueprint('member', __name__, url_prefix='/member')

@bp.route("/")
@perm_to_view_required
def index():
    members = db.session.execute(db.select(ProjectMember).filter_by(project_id=g.project.id)).scalars().all()
    return render_template("member/index.html", members=members)

@bp.route("/<int:member_id>")
@perm_to_view_required
def detail(member_id):
    member = db.get_or_404(ProjectMember, member_id)
    return render_template("member/detail.html", member=member)

@bp.route("/create", methods=["GET", "POST"])
@perm_to_manage_required
def create():
    if request.method == "POST":
        email = request.form.get("email")
        role = request.form.get("role")
        user_id = db.session.execute(db.select(User.id).filter_by(email=email)).scalar()
        member = db.session.execute(
            db.select(db.exists().where(ProjectMember.user_id == user_id, ProjectMember.project_id == g.project.id))
        ).scalar()
        error = None
        if member:
            error = 'This user is already a member of the project.'
        elif user_id:
            db.session.add(ProjectMember(project_id=g.project.id, user_id=user_id, role=role))
            db.session.commit()
            return redirect(url_for('member.index'))
        flash(error or "User with that email does not exist.")
    return render_template("member/create.html")

@bp.route("/<int:member_id>/edit", methods=["GET", "POST"])
@perm_to_manage_required
def edit(member_id):
    member = db.get_or_404(ProjectMember, member_id)
    if member.user_id in (g.user.id, g.project.manager_id):
        flash('Forbidden action.')
        return redirect(url_for('member.index'))
    if request.method == "POST":
        member.role = request.form.get("role")
        db.session.commit()
        return redirect(url_for('member.detail', member_id=member_id))
    return render_template("member/edit.html", member=member)

@bp.route("/<int:member_id>/delete", methods=["POST"])
@perm_to_manage_required
def delete(member_id):
    member = db.get_or_404(ProjectMember, member_id)
    if member.user_id == g.project.manager_id:
        flash('Forbidden action.')
    else:
        db.session.delete(member)
        db.session.commit()
    return redirect(url_for('member.index'))

@bp.route("/<int:member_id>/exit", methods=["POST"])
@perm_to_view_required
def exit_project(member_id):
    member = db.get_or_404(ProjectMember, member_id)
    if member.user_id != g.user.id or member.user_id == g.project.manager_id:
        flash('Forbidden action.')
        return redirect(url_for('member.index'))
    db.session.delete(member)
    db.session.commit()
    return redirect(url_for('project.index'))

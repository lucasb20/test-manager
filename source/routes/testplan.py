from flask import Blueprint, render_template, request, redirect, url_for, g
from db import db, TestPlan, TestCase, TestPlanCase
from decorators import admin_required


bp = Blueprint('testplan', __name__, url_prefix='/testplan')

@bp.route('/')
@admin_required
def index():
    if not g.project:
        return redirect(url_for('project.select', next=url_for('testplan.index')))
    testplans = db.session.execute(
        db.select(TestPlan).filter_by(project_id=g.project.id)
    ).scalars()
    return render_template('testplan/index.html', testplans=testplans)

@bp.route('/<int:testplan_id>')
@admin_required
def detail(testplan_id):
    testplan = db.get_or_404(TestPlan, testplan_id)
    return render_template('testplan/detail.html', testplan=testplan)

@bp.route('/<int:testplan_id>/select', methods=['GET', 'POST'])
@admin_required
def select(testplan_id):
    testcases = db.session.execute(
        db.select(TestCase).join(TestPlanCase).filter_by(test_plan_id=testplan_id)
    ).scalars()
    return render_template('testplan/select.html', testcases=testcases)

@bp.route('/<int:testplan_id>/insert', methods=['GET', 'POST'])
@admin_required
def insert(testplan_id):
    if request.method == 'POST':
        testcase_ids = request.form.getlist('testcase_ids')
        for testcase_id in testcase_ids:
            testplancase = db.session.execute(
                db.select(TestPlanCase).filter_by(test_plan_id=testplan_id, test_case_id=testcase_id)
            ).first()
            if testplancase:
                continue
            association = TestPlanCase(test_plan_id=testplan_id, test_case_id=testcase_id)
            db.session.add(association)
        db.session.commit()
        return redirect(url_for('testplan.detail', testplan_id=testplan_id))
    testcases = db.session.execute(
        db.select(TestCase).filter_by(project_id=g.project.id)
    ).scalars()
    return render_template('testplan/insert.html', testcases=testcases)

@bp.route('/<int:testplancase_id>/remove', methods=['POST'])
@admin_required
def remove(testplancase_id):
    association = db.get_or_404(TestPlanCase, testplancase_id)
    db.session.delete(association)
    db.session.commit()
    return redirect(url_for('testplan.detail', testplan_id=association.test_plan_id))

@bp.route('/create', methods=['GET', 'POST'])
@admin_required
def create():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        milestone = request.form['milestone']
        platform = request.form['platform']
        testplan = TestPlan(name=name, description=description, milestone=milestone, platform=platform, project_id=g.project.id)
        db.session.add(testplan)
        db.session.commit()
        return redirect(url_for('testplan.index'))
    return render_template('testplan/create.html')

@bp.route('/<int:testplan_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit(testplan_id):
    testplan = db.get_or_404(TestPlan, testplan_id)
    if request.method == 'POST':
        testplan.name = request.form['name']
        testplan.description = request.form['description']
        testplan.milestone = request.form['milestone']
        testplan.platform = request.form['platform']
        db.session.commit()
        return redirect(url_for('testplan.index'))
    return render_template('testplan/edit.html', testplan=testplan)

@bp.route('/<int:testplan_id>/delete', methods=['POST'])
@admin_required
def delete(testplan_id):
    testplan = db.get_or_404(TestPlan, testplan_id)
    db.session.delete(testplan)
    db.session.commit()
    return redirect(url_for('testplan.index'))
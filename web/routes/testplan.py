from flask import Blueprint, render_template, request, redirect, url_for, g
from db import db, TestPlan, TestCase, TestPlanCase
from services.testcase import get_testcases
from decorators import perm_to_view_required, perm_to_edit_required


bp = Blueprint('testplan', __name__, url_prefix='/testplan')

@bp.route('/')
@perm_to_view_required
def index():
    if not g.project:
        return redirect(url_for('project.select', next=url_for('testplan.index')))
    testplans = db.session.execute(
        db.select(TestPlan).filter_by(project_id=g.project.id)
    ).scalars().all()
    return render_template('testplan/index.html', testplans=testplans)

@bp.route('/<int:testplan_id>')
@perm_to_view_required
def detail(testplan_id):
    testplan = db.get_or_404(TestPlan, testplan_id)
    testcases = db.session.execute(
        db.select(TestCase).join(TestPlanCase).filter(
            TestPlanCase.test_plan_id == testplan_id
        ).order_by(TestPlanCase.order.asc())
    ).scalars().all()
    return render_template('testplan/detail.html', testplan=testplan, testcases=testcases)

@bp.route('/create', methods=['GET', 'POST'])
@perm_to_edit_required
def create():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        milestone = request.form['milestone']
        platform = request.form['platform']
        testplan = TestPlan(name=name, description=description, milestone=milestone, platform=platform, project_id=g.project.id)
        db.session.add(testplan)
        db.session.commit()
        return redirect(url_for('testplan.detail', testplan_id=testplan.id))
    return render_template('testplan/create.html')

@bp.route('/<int:testplan_id>/edit', methods=['GET', 'POST'])
@perm_to_edit_required
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
@perm_to_edit_required
def delete(testplan_id):
    testplan = db.get_or_404(TestPlan, testplan_id)
    db.session.delete(testplan)
    db.session.commit()
    return redirect(url_for('testplan.index'))

@bp.route('/<int:testplan_id>/associate', methods=['GET', 'POST'])
@perm_to_edit_required
def associate(testplan_id):
    testcases = get_testcases(g.project.id)
    associated_ids = db.session.execute(
        db.select(TestPlanCase.test_case_id).filter_by(test_plan_id=testplan_id)
    ).scalars().all()
    if request.method == 'POST':
        testcase_ids = request.form.getlist('testcase_ids')
        for testcase in testcases:
            if str(testcase.id) in testcase_ids and testcase.id not in associated_ids:
                association = TestPlanCase(test_plan_id=testplan_id, test_case_id=testcase.id)
                db.session.add(association)
            elif str(testcase.id) not in testcase_ids and testcase.id in associated_ids:
                association = db.session.execute(
                    db.delete(TestPlanCase).where(TestPlanCase.test_plan_id == testplan_id, TestPlanCase.test_case_id == testcase.id)
                )
        db.session.commit()
        return redirect(url_for('testplan.detail', testplan_id=testplan_id))
    return render_template('testplan/associate.html', testcases=testcases, associated_ids=associated_ids)

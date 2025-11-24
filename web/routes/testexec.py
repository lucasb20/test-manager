from flask import Blueprint, request, render_template, redirect, url_for, g, flash, Response
from db import db, TestExecution, TestResult, TestCase, TestPlanCase, TestPlan
from decorators import perm_to_view_required, perm_to_edit_required
from utils import create_csv


bp = Blueprint('testexec', __name__, url_prefix='/testexec')

@bp.route('/<int:testplan_id>', methods=['GET', 'POST'])
@perm_to_view_required
def index(testplan_id):
    testplancases = db.session.execute(
        db.select(TestPlanCase).filter_by(test_plan_id=testplan_id).order_by(TestPlanCase.order)
    ).scalars().all()
    for index, tpc in enumerate(testplancases):
        tpc.order = index + 1
    db.session.commit()
    return render_template('testexec/index.html', testplancases=testplancases, testplan_id=testplan_id)

@bp.route('/<int:testplan_id>/create', methods=['GET'])
@perm_to_edit_required
def create(testplan_id):
    testcases = db.session.execute(
        db.select(TestCase.id).join(TestPlanCase).filter(TestPlanCase.test_plan_id == testplan_id)
    ).scalars().all()
    if len(testcases) == 0:
        flash('No test cases in the test plan. Please add test cases before creating a test execution.')
        return redirect(url_for('testplan.index', testplan_id=testplan_id))
    testexec = TestExecution(test_plan_id=testplan_id, status='progress')
    db.session.add(testexec)
    db.session.commit()
    return redirect(url_for('testexec.run_case', testexec_id=testexec.id, index=0))

@bp.route('/select', methods=['GET'])
@perm_to_view_required
def select():
    testplans = db.session.execute(
        db.select(TestPlan)
    ).scalars().all()
    return render_template('testexec/select.html', testplans=testplans)

@bp.route('/<int:testplan_id>/previous', methods=['GET'])
@perm_to_view_required
def previous(testplan_id):
    testexecs = db.session.execute(
        db.select(TestExecution).filter_by(test_plan_id=testplan_id).order_by(TestExecution.created_at.desc())
    ).scalars().all()
    return render_template('testexec/previous.html', testexecs=testexecs, testplan_id=testplan_id)

@bp.route('/<int:testexec_id>/delete', methods=['POST'])
@perm_to_edit_required
def delete(testexec_id):
    testresults = db.session.execute(
        db.select(TestResult).filter_by(test_execution_id=testexec_id)
    ).scalars().all()
    for result in testresults:
        db.session.delete(result)
    testexec = db.get_or_404(TestExecution, testexec_id)
    testplan_id = testexec.test_plan_id
    db.session.delete(testexec)
    db.session.commit()
    return redirect(url_for('testexec.previous', testplan_id=testplan_id))

@bp.route('/<int:testexec_id>/<int:index>', methods=['GET', 'POST'])
@perm_to_edit_required
def run_case(testexec_id, index):
    testexec = db.get_or_404(TestExecution, testexec_id)
    if testexec.status == 'finished':
        return redirect(url_for('testexec.summary', testexec_id=testexec.id))
    testcases = db.session.execute(
        db.select(TestCase).join(TestPlanCase).filter(TestPlanCase.test_plan_id == testexec.test_plan_id).order_by(TestPlanCase.order)
    ).scalars().all()
    if index >= len(testcases):
        testexec.status = 'finished'
        db.session.commit()
        return redirect(url_for('testexec.summary', testexec_id=testexec.id))
    testcase = testcases[index]
    if request.method == 'POST':
        result = request.form['status']
        notes = request.form['notes']
        testresult = TestResult(
            test_execution_id=testexec.id,
            test_case_id=testcase.id,
            executed_by=g.user.id,
            result=result,
            notes=notes
        )
        db.session.add(testresult)
        db.session.commit()
        return redirect(url_for('testexec.run_case', testexec_id=testexec.id, index=index + 1))
    return render_template('testexec/run_case.html', testexec=testexec, testcase=testcase, index=index, total=len(testcases))

@bp.route('/<int:testexec_id>/summary', methods=['GET'])
@perm_to_view_required
def summary(testexec_id):
    testexec = db.get_or_404(TestExecution, testexec_id)
    results = db.session.execute(
        db.select(TestResult).filter_by(test_execution_id=testexec.id)
    ).scalars().all()
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.result == 'pass')
    skipped_tests = sum(1 for r in results if r.result == 'skip')
    failed_tests = total_tests - passed_tests - skipped_tests
    return render_template('testexec/summary.html', testexec=testexec, results=results, total_tests=total_tests, passed_tests=passed_tests, failed_tests=failed_tests, skipped_tests=skipped_tests)

@bp.route('/change_order/<int:testplan_id>/<int:testplancase_id1>/<int:testplancase_id2>', methods=['POST'])
@perm_to_edit_required
def change_order(testplan_id, testplancase_id1, testplancase_id2):
    testplancase1 = db.get_or_404(TestPlanCase, testplancase_id1)
    testplancase2 = db.get_or_404(TestPlanCase, testplancase_id2)
    testplancase1.order, testplancase2.order = testplancase2.order, testplancase1.order
    db.session.commit()
    return redirect(url_for('testexec.index', testplan_id=testplan_id))

@bp.route('/<int:testexec_id>/export', methods=['GET'])
@perm_to_view_required
def export(testexec_id):
    testexec = db.get_or_404(TestExecution, testexec_id)
    testplan = db.session.get(TestPlan, testexec.test_plan_id)
    results = db.session.execute(
        db.select(TestResult).filter_by(test_execution_id=testexec.id)
    ).scalars().all()
    data = [("Milestone", "Platform", "Test Case Code", "Status", "Executed By", "Executed At", "Notes")]
    for result in results:
        data.append((
            testplan.milestone,
            testplan.platform,
            result.test_case_code,
            result.result,
            result.executor,
            result.executed_at.strftime("%Y-%m-%d %H:%M"),
            result.notes
        ))
    csv_data = create_csv(data)
    filename = f"testexec_{testexec.name.casefold()}.csv"
    response = Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
    return response

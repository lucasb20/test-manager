from flask import Blueprint, request, render_template, redirect, url_for, g, flash
from db import db, TestExecution, TestResult, TestCase, TestPlanCase
from decorators import admin_required


bp = Blueprint('testexec', __name__, url_prefix='/testexec')

@bp.route('/<int:testplan_id>', methods=['GET', 'POST'])
@admin_required
def index(testplan_id):
    testexecs = db.session.execute(
        db.select(TestExecution).filter_by(test_plan_id=testplan_id).order_by(TestExecution.id.desc())
    ).scalars().all()
    return render_template('testexec/index.html', testexecs=testexecs, testplan_id=testplan_id)

@bp.route('/<int:testplan_id>/create', methods=['GET'])
@admin_required
def create(testplan_id):
    testcases = db.session.execute(
        db.select(TestCase.id).join(TestPlanCase).filter(TestPlanCase.test_plan_id == testplan_id)
    ).scalars().all()
    if len(testcases) == 0:
        flash('No test cases in the test plan. Please add test cases before creating a test execution.')
        return redirect(url_for('testplan.detail', testplan_id=testplan_id))
    testexec = TestExecution(test_plan_id=testplan_id, status='progress')
    db.session.add(testexec)
    db.session.commit()
    return redirect(url_for('testexec.run_case', testexec_id=testexec.id, index=0))

@bp.route('/<int:testexec_id>/<int:index>', methods=['GET', 'POST'])
@admin_required
def run_case(testexec_id, index):
    testexec = db.get_or_404(TestExecution, testexec_id)
    if testexec.status == 'finished':
        return redirect(url_for('testexec.summary', testexec_id=testexec.id))
    testcases = db.session.execute(
        db.select(TestCase).join(TestPlanCase).filter(TestPlanCase.test_plan_id == testexec.test_plan_id).order_by(TestCase.id)
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
@admin_required
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
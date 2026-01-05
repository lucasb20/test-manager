from flask import Blueprint, request, render_template, redirect, url_for, g, flash, Response
from decorators import perm_to_view_required, perm_to_edit_required
from forms import BugForm
from db import db, TestCase, TestSuite, TestSuiteCase, TestRun, TestResult, Bug, BugTestCase
from utils import create_csv

bp = Blueprint('testrun', __name__, url_prefix='/testrun')

@bp.route('/<int:testsuite_id>', methods=['GET', 'POST'])
@perm_to_view_required
def index(testsuite_id):
    tscs = db.session.execute(
        db.select(TestSuiteCase).filter_by(test_suite_id=testsuite_id).order_by(TestSuiteCase.order.asc())
    ).scalars().all()
    return render_template('testrun/index.html', tscs=tscs)

@bp.route('/<int:testsuite_id>/create', methods=['GET'])
@perm_to_edit_required
def create(testsuite_id):
    tcs_len = db.session.execute(
        db.select(db.func.count()).select_from(TestCase).join(TestSuiteCase).filter(TestSuiteCase.test_suite_id == testsuite_id)
    ).scalar()
    if tcs_len == 0:
        flash('No test cases in the test suite. Please add test cases before creating a test run.')
        return redirect(url_for('testsuite.detail', testsuite_id=testsuite_id))
    testrun = TestRun(test_suite_id=testsuite_id, status='progress')
    db.session.add(testrun)
    db.session.commit()
    return redirect(url_for('testrun.run_case', testrun_id=testrun.id, index=0))

@bp.route('/<int:testsuite_id>/previous', methods=['GET'])
@perm_to_view_required
def previous(testsuite_id):
    testruns = db.session.execute(
        db.select(TestRun).filter_by(test_suite_id=testsuite_id).order_by(TestRun.created_at.desc())
    ).scalars().all()
    ts_name = db.session.execute(
        db.select(TestSuite.name).filter_by(id=testsuite_id)
    ).scalar()
    return render_template('testrun/previous.html', testruns=testruns, ts_name=ts_name)

@bp.route('/<int:testrun_id>/delete', methods=['POST'])
@perm_to_edit_required
def delete(testrun_id):
    testrun = db.get_or_404(TestRun, testrun_id)
    testsuite_id = testrun.test_suite_id
    db.session.delete(testrun)
    db.session.commit()
    return redirect(url_for('testrun.previous', testsuite_id=testsuite_id))

@bp.route('/<int:testrun_id>/<int:index>', methods=['GET', 'POST'])
@perm_to_edit_required
def run_case(testrun_id, index):
    testrun = db.get_or_404(TestRun, testrun_id)
    if testrun.status == 'finished':
        return redirect(url_for('testrun.summary', testrun_id=testrun.id))
    testcases = db.session.execute(
        db.select(TestCase).join(TestSuiteCase).filter(TestSuiteCase.test_suite_id == testrun.test_suite_id).order_by(TestSuiteCase.order.asc())
    ).scalars().all()
    if index >= len(testcases):
        testrun.status = 'finished'
        db.session.commit()
        return redirect(url_for('testrun.summary', testrun_id=testrun.id))
    testcase = testcases[index]
    if request.method == 'POST':
        testresult = TestResult(
            test_run_id=testrun.id,
            test_case_id=testcase.id,
            executed_by=g.user.id,
            result=request.form['status'],
            notes=request.form['notes'],
            duration=int(request.form['duration'])
        )
        db.session.add(testresult)
        db.session.commit()
        return redirect(url_for('testrun.run_case', testrun_id=testrun.id, index=index + 1))
    return render_template('testrun/run_case.html', testrun=testrun, testcase=testcase, index=index, total=len(testcases))

@bp.route('/<int:testresult_id>/edit', methods=['GET', 'POST'])
@perm_to_edit_required
def edit_result(testresult_id):
    testresult = db.get_or_404(TestResult, testresult_id)
    if request.method == 'POST':
        testresult.result = request.form['status']
        testresult.notes = request.form['notes']
        db.session.commit()
        return redirect(url_for('testrun.summary', testrun_id=testresult.test_run_id))
    testcase = db.session.get(TestCase, testresult.test_case_id)
    return render_template('testrun/edit.html', testresult=testresult, testcase=testcase)

@bp.route('/<int:testrun_id>/summary', methods=['GET'])
@perm_to_view_required
def summary(testrun_id):
    testrun = db.get_or_404(TestRun, testrun_id)
    results = db.session.execute(
        db.select(TestResult).filter_by(test_run_id=testrun.id)
    ).scalars().all()
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.result == 'pass')
    skipped_tests = sum(1 for r in results if r.result == 'skip')
    failed_tests = total_tests - passed_tests - skipped_tests
    percent_passed = round((passed_tests / total_tests * 100), 2) if total_tests > 0 else 0
    data = {
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'failed_tests': failed_tests,
        'skipped_tests': skipped_tests,
        'total_duration': testrun.duration,
        'total_duration_min': testrun.duration // 60,
        'percent_passed': percent_passed
    }
    return render_template('testrun/summary.html', testrun=testrun, results=results, data=data)

@bp.route('/<int:testresult_id>/report_bug', methods=['GET', 'POST'])
@perm_to_edit_required
def report_bug(testresult_id):
    form = BugForm(request.form)
    testresult = db.get_or_404(TestResult, testresult_id)
    if request.method == 'POST' and form.validate():
        bug = Bug(title=form.title.data, description=form.description.data, status=form.status.data, priority=form.priority.data, reported_by=g.user.id, project_id=g.project.id)
        bug.order = bug.last_order + 1
        db.session.add(bug)
        db.session.flush()
        db.session.add(BugTestCase(bug_id=bug.id, test_case_id=testresult.test_case_id))
        db.session.commit()
        return redirect(url_for('testrun.summary', testrun_id=testresult.test_run_id))
    form.description.data = testresult.notes
    return render_template('bugtracking/create.html', form=form)

@bp.route('/change_order/<int:testsuitecase_id1>/<int:testsuitecase_id2>', methods=['POST'])
@perm_to_edit_required
def change_order(testsuitecase_id1, testsuitecase_id2):
    tsc1 = db.get_or_404(TestSuiteCase, testsuitecase_id1)
    tsc2 = db.get_or_404(TestSuiteCase, testsuitecase_id2)
    tsc1.order, tsc2.order = tsc2.order, tsc1.order
    db.session.commit()
    return redirect(url_for('testrun.index', testsuite_id=tsc1.test_suite_id))

@bp.route('/<int:testrun_id>/export', methods=['GET'])
@perm_to_view_required
def export(testrun_id):
    testrun = db.get_or_404(TestRun, testrun_id)
    results = db.session.execute(
        db.select(TestResult).filter_by(test_run_id=testrun.id)
    ).scalars().all()
    data = [("Test Case Code", "Status", "Executed By", "Executed At", "Duration", "Notes")]
    for result in results:
        data.append((
            result.testcase_code,
            result.result,
            result.executor,
            result.executed_at.strftime("%Y-%m-%d %H:%M"),
            result.duration,
            result.notes
        ))
    csv_data = create_csv(data)
    name = db.session.execute(
        db.select(TestSuite.name).filter_by(id=testrun.test_suite_id)
    ).scalar()
    filename = f"testrun_{name.casefold()}.csv"
    response = Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
    return response

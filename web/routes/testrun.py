from datetime import datetime
from flask import Blueprint, request, render_template, redirect, url_for, g, flash, Response
from decorators import perm_to_view_required, perm_to_edit_required
from forms import BugForm, TestResultForm
from db import db, TestCase, TestSuite, TestSuiteCase, TestRun, TestResult, Bug, BugTestCase
from utils import create_csv, format_datetime

bp = Blueprint('testrun', __name__, url_prefix='/testrun')

@bp.route('/<int:testsuite_id>/create', methods=['GET'])
@perm_to_edit_required
def create(testsuite_id):
    tscs = db.session.execute(db.select(TestSuiteCase).filter_by(test_suite_id=testsuite_id).order_by(TestSuiteCase.order.asc())).scalars().all()
    if len(tscs) == 0:
        flash('No test cases in the test suite. Please add test cases before creating a test run.')
        return redirect(url_for('testsuite.detail', testsuite_id=testsuite_id))
    testrun = TestRun(test_suite_id=testsuite_id)
    db.session.add(testrun)
    db.session.flush()
    for tsc in tscs:
        testresult = TestResult(
            test_run_id=testrun.id,
            test_case_id=tsc.test_case_id
        )
        db.session.add(testresult)
    db.session.commit()
    return redirect(url_for('testrun.run_case', testrun_id=testrun.id))

@bp.route('/<int:testsuite_id>/previous', methods=['GET'])
@perm_to_view_required
def previous(testsuite_id):
    testruns = db.session.execute(db.select(TestRun).filter_by(test_suite_id=testsuite_id).order_by(TestRun.created_at.desc())).scalars().all()
    ts_name = db.session.execute(db.select(TestSuite.name).filter_by(id=testsuite_id)).scalar()
    return render_template('testrun/previous.html', testruns=testruns, ts_name=ts_name)

@bp.route('/<int:testrun_id>/delete', methods=['POST'])
@perm_to_edit_required
def delete(testrun_id):
    testrun = db.get_or_404(TestRun, testrun_id)
    testsuite_id = testrun.test_suite_id
    db.session.delete(testrun)
    db.session.commit()
    return redirect(url_for('testrun.previous', testsuite_id=testsuite_id))

@bp.route('/<int:testrun_id>/run_case', methods=['GET', 'POST'])
@perm_to_edit_required
def run_case(testrun_id):
    testrun = db.get_or_404(TestRun, testrun_id)
    if 'testresult_id' in request.args:
        testresult = db.get_or_404(TestResult, request.args.get('testresult_id'))
    else:
        testresult = db.session.execute(db.select(TestResult).filter_by(test_run_id=testrun.id, executed_at=None)).scalars().first()
        if not testresult:
            return redirect(url_for('testrun.summary', testrun_id=testrun.id))
    form = TestResultForm(request.form, obj=testresult)
    if request.method == 'POST' and form.validate():
        if testresult.executed_at is None:
            testresult.executed_at = datetime.now()
            testresult.executed_by = g.user.id
            testresult.duration = int(request.form['duration'])
        testresult.status = form.status.data
        testresult.notes = form.notes.data
        db.session.commit()
        return redirect(url_for('testrun.run_case', testrun_id=testrun.id))
    testcase = db.session.get(TestCase, testresult.test_case_id)
    testresults = db.session.execute(db.select(TestResult).filter_by(test_run_id=testrun.id)).scalars().all()
    return render_template('testrun/run_case.html', form=form, testrun=testrun, testcase=testcase, testresults=testresults)

@bp.route('/<int:testrun_id>/summary', methods=['GET'])
@perm_to_view_required
def summary(testrun_id):
    testrun = db.get_or_404(TestRun, testrun_id)
    testresults = db.session.execute(db.select(TestResult).filter_by(test_run_id=testrun.id)).scalars().all()
    total_tests = len(testresults)
    passed_tests = sum(1 for r in testresults if r.status == 'pass')
    failed_tests = sum(1 for r in testresults if r.status == 'fail')
    skipped_tests = total_tests - passed_tests - failed_tests
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
    return render_template('testrun/summary.html', testrun=testrun, testresults=testresults, data=data)

@bp.route('/<int:testresult_id>/report_bug', methods=['GET', 'POST'])
@perm_to_edit_required
def report_bug(testresult_id):
    form = BugForm(request.form)
    testresult = db.get_or_404(TestResult, testresult_id)
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
        db.session.add(BugTestCase(bug_id=bug.id, test_case_id=testresult.test_case_id))
        db.session.commit()
        return redirect(url_for('testrun.run_case', testrun_id=testresult.test_run_id))
    form.description.data = testresult.notes
    return render_template('bugtracking/create.html', form=form)

@bp.route('/<int:testrun_id>/export', methods=['GET'])
@perm_to_view_required
def export(testrun_id):
    testrun = db.get_or_404(TestRun, testrun_id)
    testresults = db.session.execute(
        db.select(TestResult).filter_by(test_run_id=testrun.id)
    ).scalars().all()
    data = [("Test Case", "Status", "Executed By", "Executed At", "Duration", "Notes")]
    for testresult in testresults:
        data.append((
            testresult.testcase_code,
            testresult.status,
            testresult.executor,
            format_datetime(testresult.executed_at),
            testresult.duration,
            testresult.notes
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

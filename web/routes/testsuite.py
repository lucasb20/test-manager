from flask import Blueprint, render_template, request, redirect, url_for, g
from decorators import perm_to_view_required, perm_to_edit_required
from db import db, TestSuite, TestCase, TestSuiteCase
from forms import TestSuiteForm

bp = Blueprint('testsuite', __name__, url_prefix='/testsuite')

@bp.route('/')
@perm_to_view_required
def index():
    testsuites = db.session.execute(
        db.select(TestSuite).filter_by(project_id=g.project.id).order_by(TestSuite.created_at.desc())
    ).scalars().all()
    return render_template('testsuite/index.html', testsuites=testsuites)

@bp.route('/<int:testsuite_id>')
@perm_to_view_required
def detail(testsuite_id):
    testsuite = db.get_or_404(TestSuite, testsuite_id)
    tscs = db.session.execute(
        db.select(TestSuiteCase).filter_by(test_suite_id=testsuite_id).order_by(TestSuiteCase.order.asc())
    ).scalars().all()
    return render_template('testsuite/detail.html', testsuite=testsuite, tscs=tscs)

@bp.route('/create', methods=['GET', 'POST'])
@perm_to_edit_required
def create():
    form = TestSuiteForm(request.form)
    if request.method == 'POST' and form.validate():
        testsuite = TestSuite(name=form.name.data, description=form.description.data, project_id=g.project.id)
        db.session.add(testsuite)
        db.session.commit()
        return redirect(url_for('testsuite.detail', testsuite_id=testsuite.id))
    return render_template('testsuite/create.html', form=form)

@bp.route('/<int:testsuite_id>/edit', methods=['GET', 'POST'])
@perm_to_edit_required
def edit(testsuite_id):
    testsuite = db.get_or_404(TestSuite, testsuite_id)
    form = TestSuiteForm(request.form, obj=testsuite)
    if request.method == 'POST' and form.validate():
        testsuite.name = form.name.data
        testsuite.description = form.description.data
        db.session.commit()
        return redirect(url_for('testsuite.detail', testsuite_id=testsuite.id))
    return render_template('testsuite/edit.html', form=form)

@bp.route('/<int:testsuite_id>/delete', methods=['POST'])
@perm_to_edit_required
def delete(testsuite_id):
    testsuite = db.get_or_404(TestSuite, testsuite_id)
    db.session.delete(testsuite)
    db.session.commit()
    return redirect(url_for('testsuite.index'))

@bp.route('/<int:testsuite_id>/associate', methods=['GET', 'POST'])
@perm_to_edit_required
def associate(testsuite_id):
    testcases = db.session.execute(
        db.select(TestCase).filter_by(project_id=g.project.id).order_by(TestCase.order.asc())
    ).scalars().all()
    associated_ids = db.session.execute(
        db.select(TestSuiteCase.test_case_id).filter_by(test_suite_id=testsuite_id)
    ).scalars().all()
    if request.method == 'POST':
        testcase_ids = request.form.getlist('testcase_ids')
        last_order = db.session.execute(
            db.select(TestSuiteCase.order).filter_by(test_suite_id=testsuite_id).order_by(TestSuiteCase.order.desc()).limit(1)
        ).scalars().first() or 0
        for testcase in testcases:
            if str(testcase.id) in testcase_ids and testcase.id not in associated_ids:
                db.session.add(TestSuiteCase(test_suite_id=testsuite_id, test_case_id=testcase.id, order=last_order+1))
                last_order += 1
            elif str(testcase.id) not in testcase_ids and testcase.id in associated_ids:
                db.session.execute(
                    db.delete(TestSuiteCase).where(TestSuiteCase.test_suite_id == testsuite_id, TestSuiteCase.test_case_id == testcase.id)
                )
        db.session.commit()
        return redirect(url_for('testsuite.detail', testsuite_id=testsuite_id))
    return render_template('testsuite/associate.html', testcases=testcases, associated_ids=associated_ids)

@bp.route('/<int:testsuitecase_id1>/<int:testsuitecase_id2>/change_order', methods=['POST'])
@perm_to_edit_required
def change_order(testsuitecase_id1, testsuitecase_id2):
    tsc1 = db.get_or_404(TestSuiteCase, testsuitecase_id1)
    tsc2 = db.get_or_404(TestSuiteCase, testsuitecase_id2)
    tsc1.order, tsc2.order = tsc2.order, tsc1.order
    db.session.commit()
    return redirect(url_for('testsuite.detail', testsuite_id=tsc1.test_suite_id))

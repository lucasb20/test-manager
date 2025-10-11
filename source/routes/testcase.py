from flask import Blueprint, render_template, request, redirect, url_for, g
from db import db, TestCase
from decorators import admin_required


bp = Blueprint('testcase', __name__, url_prefix='/testcase')

@bp.route('/')
@admin_required
def index():
    if not g.project:
        return redirect(url_for('project.select', next=url_for('testcase.index')))
    testcases = db.session.execute(
        db.select(TestCase).filter_by(project_id=g.project.id)
    ).scalars()
    return render_template('testcase/index.html', testcases=testcases)

@bp.route('/<int:testcase_id>')
@admin_required
def detail(testcase_id):
    testcase = db.get_or_404(TestCase, testcase_id)
    return render_template('testcase/detail.html', testcase=testcase)

@bp.route('/<int:testcase_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit(testcase_id):
    testcase = db.get_or_404(TestCase, testcase_id)
    if request.method == 'POST':
        testcase.title = request.form['title']
        testcase.preconditions = request.form['preconditions']
        testcase.steps = request.form['steps']
        testcase.expected_result = request.form['expected_result']
        db.session.commit()
        return redirect(url_for('testcase.detail', testcase_id=testcase.id))
    return render_template('testcase/edit.html', testcase=testcase)

@bp.route('/create', methods=['GET', 'POST'])
@admin_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        preconditions = request.form['preconditions']
        steps = request.form['steps']
        expected_result = request.form['expected_result']
        testcase = TestCase(title=title, preconditions=preconditions, steps=steps, expected_result=expected_result, project_id=g.project.id)
        db.session.add(testcase)
        db.session.commit()
        return redirect(url_for('testcase.detail', testcase_id=testcase.id))
    return render_template('testcase/create.html')

@bp.route('/<int:testcase_id>/delete', methods=['POST'])
@admin_required
def delete(testcase_id):
    testcase = db.get_or_404(TestCase, testcase_id)
    db.session.delete(testcase)
    db.session.commit()
    return redirect(url_for('testcase.index'))
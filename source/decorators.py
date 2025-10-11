import functools
from flask import g, redirect, url_for, flash


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view

def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None or not g.user.is_admin:
            flash('You do not have permission to access this page.')
            return redirect(url_for('index'))
        return view(**kwargs)
    return wrapped_view
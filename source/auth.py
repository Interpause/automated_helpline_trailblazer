from flask import Blueprint, current_app, flash, g, redirect, render_template, request, session, url_for
from uuid import uuid4
from datetime import datetime
import functools,re

#is a wrapper TODO: smth along the lines of redirecting to the original page after login using referrer=url or smth
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(f"{url_for('auth.login')}?previous_url={request.path}")
        return view(**kwargs)
    return wrapped_view

def login_blocked(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is not None:
            return redirect(url_for('index'))
        return view(**kwargs)
    return wrapped_view

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
@login_blocked
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            if not re.match(r'^\S{1,20}$',username): raise ValueError('Username is invalid~') 
            if not re.match(r'^.{1,25}$',password): raise ValueError('Password is invalid~')

            if g.db_users.query.filter_by(username=username).first() is not None: raise LookupError(f'Username {username} is already registered~') #TODO: check should also look for semantically similar/lowercase same names (multilinguage support)

            user = g.db_users(
                uuid = uuid4(), #feck it i can't one-line anti-collision, not that it will ever happen
                username = username,
                passwd = password,
                created_time = datetime.utcnow()
            )
            g.db_sess.add(user) #auto-saved on request teardown

            flash('Registration successful!‌ Login now~')
            return redirect(url_for('auth.login'))

        except Exception as e:
            current_app.logger.warn(e)
            flash(e)

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
@login_blocked
def login():
    url = request.args.get('previous_url')
    if url is None: url = url_for('index')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            user = g.db_users.query.filter_by(username=username).first()
            if user is None: raise LookupError('Incorrect username.')
            elif user.passwd != password: raise ValueError('Incorrect password.') #chillax its implicitly hashed by utils
            
            session.clear()
            session['user_id'] = user.uuid #TODO: JWT Tokens or regular Session tokens. Cookies are insecure.

            flash('Login successful!')
            return redirect(url)

        except Exception as e:
            current_app.logger.warn(e)
            flash(e)
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Logout successful!')
    return redirect(url_for('index'))

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None: g.user = None
    else: 
        g.user = g.db_users.query.get(user_id) #TODO: change required after switching to tokens
        if g.user == None:
            current_app.logger.warn(f'User {user_id} does not exist!')
            session.clear()
            flash("Your account doesn't exist?")
        else: g.user.last_activity_time = datetime.utcnow()
from flask import Blueprint, flash, g, redirect, render_template, request, url_for, current_app, abort
from uuid import uuid4
from datetime import datetime
from .auth import login_required

bp = Blueprint('news', __name__,url_prefix='/news')

@bp.route("/index")
def index():
    articles = g.db_news.query.all()
    return render_template('news/news.html', articles=articles)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        try:
            if not title: raise ValueError('Title is required.')
            if len(title) > 200 or len(body) > 2000: raise ValueError('Text is too long!')
            post = g.db_posts(
                uuid = uuid4(),
                user_uuid = g.user.uuid,
                title = title,
                body = body,
                created_time = datetime.utcnow()
            )
            g.db_sess.add(post) #auto-saved on request teardown

            flash('Posted!')
            return redirect(url_for('forum.index'))

        except Exception as e:
            current_app.logger.warn(e)
            flash(e)

    return render_template('forum/create.html')

@bp.route('/<uuid:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = g.db_posts.query.get(id)
    if g.user.uuid != post.user_uuid: abort(403, 'You do not own this post!')

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        try:
            if not title: raise ValueError('Title is required.')
            post.title = title
            post.body = body
            flash('Updated!')
            return redirect(url_for('forum.index'))

        except Exception as e:
            current_app.logger.warn(e)
            flash(e)

    return render_template('forum/update.html', post=post)

@bp.route('/<uuid:id>/delete', methods=('POST',))
@login_required
def delete(id):
    post = g.db_posts.query.get(id)
    if g.user.uuid != post.user_uuid: abort(403, 'You do not own this post!')
    post.title = '(deleted)'
    post.body = ''
    post.user_uuid = '00000000-0000-0000-0000-000000000000'
    flash('Deleted!')
    return redirect(url_for('forum.index'))
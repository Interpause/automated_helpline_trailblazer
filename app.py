from source import make_app,database
from flask import render_template,g,redirect,url_for
app = make_app()

@app.route("/secret")
def test():
    return app.config['SERVER_VERSION']

@app.route("/")
def index():
    return redirect(url_for('news.index'))

#TODO: replace all filter functions with async fetching by client
#TODO: temporarily disable all forms of caching of local files for testing purposes
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

import passlib, phonenumbers

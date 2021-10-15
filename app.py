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

'''
import source
from flask import g
import pickle
app = source.make_app()
db_adder,_ = source.database.register_db(app)
raw = []
with app.app_context():
	db_adder()
	raw = g.db_news.query.all()
data = []
for news in raw:
	row = {}
	row['uuid'] = news.uuid.bytes
	row['url'] = news.url
	row['title'] = news.title
	row['picture'] = news.picture
	row['icon'] = news.icon
	row['body'] = news.body
	row['publish_time'] = news.publish_time
	data.append(row)
with open('news.pkl','wb') as f:
	pickle.dump(data,f,protocol=pickle.HIGHEST_PROTOCOL)


#server side
from sqlalchemy import MetaData,create_engine
import pickle
news = None
with open('news.pkl','rb') as f:
	news = pickle.load(f)
SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(username="Interpause",password="thisisagoodpassword",hostname="Interpause.mysql.pythonanywhere-services.com",databasename="Interpause$burdenbrother")
engine = create_engine(SQLALCHEMY_DATABASE_URI)
meta = MetaData(bind=engine)
meta.reflect()
table = meta.tables['News']
with engine.begin() as connection:
	connection.execute(table.insert(),news)
'''

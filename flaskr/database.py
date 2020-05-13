from flask import g,current_app,abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import UUIDType, PhoneNumberType, PasswordType #other cool custom types available: https://sqlalchemy-utils.readthedocs.io/en/latest/

def make_user_table(db):
    class User(db.Model):
        uuid = db.Column(UUIDType(), primary_key = True)
        username = db.Column(db.String(20), unique = True)
        passwd = db.Column(PasswordType(schemes=('pbkdf2_sha512',)), nullable = False) #automatically applies SHA512

        name = db.Column(db.String(150), nullable = True)
        phone = db.Column(PhoneNumberType(region='SG'), nullable = True)
        pdpa = db.Column(db.String(20), nullable = True)

        last_activity_time = db.Column(db.DateTime, nullable = True)
        created_time = db.Column(db.DateTime, nullable = False)
        mc_expiry_time = db.Column(db.DateTime, nullable = True)

        __tablename__ = 'Users'
        def __repr__(self): return f'<User: {self.uuid}>'
    if User.query.get('00000000-0000-0000-0000-000000000000') == None:
        from datetime import datetime
        from uuid import uuid4
        holder = User(
            uuid = '00000000-0000-0000-0000-000000000000',
            username = 'SYSTEM',
            passwd = str(uuid4()),
            created_time = datetime.utcnow()
        )
        db.session.add(holder)
    return User

def make_post_table(db):
    class Post(db.Model):
        uuid = db.Column(UUIDType(), primary_key = True)
        user_uuid = db.Column(UUIDType(),nullable = False)

        title = db.Column(db.String(200), nullable = False)
        body = db.Column(db.String(2000), nullable = True)

        created_time = db.Column(db.DateTime, nullable = False)

        __tablename__ = 'Posts'
        def __repr__(self): return f'<Post: {self.uuid}>'
    return Post

def register_db(app):
    db = SQLAlchemy(app)
    User = make_user_table(db)
    Post = make_post_table(db)
    db.create_all()
    db.session.commit()

    #@app.before_request
    def addDB():
        g.db_sess = db.session
        g.db_users = User
        g.db_posts = Post

    @app.template_filter('getUser')
    def getUser(uuid): 
        user = g.db_users.query.get(uuid)
        if user is None:
            current_app.logger.warn(f'User {uuid} does not exist!')
            abort(404, f'User {uuid} does not exist!')
        return user
            
    @app.template_filter('getPost')
    def getPost(uuid): 
        post = g.db_posts.query.get(uuid)
        if post is None:
            current_app.logger.warn(f'Post {uuid} does not exist!')
            abort(404, f'Post {uuid} does not exist!')
        return post

    @app.teardown_request
    def closeDB(error):
        sess = g.pop('db_sess',None)
        if sess is not None: sess.commit()

    return addDB
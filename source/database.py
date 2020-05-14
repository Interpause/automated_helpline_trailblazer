from flask import g,current_app,abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import UUIDType, PhoneNumberType, PasswordType, URLType #other cool custom types available: https://sqlalchemy-utils.readthedocs.io/en/latest/

def make_user_table(db):
    class User(db.Model):
        uuid = db.Column(UUIDType(), primary_key = True)
        username = db.Column(db.String(20), unique = True)
        passwd = db.Column(PasswordType(schemes=('pbkdf2_sha512',)), nullable = False) #automatically applies SHA512

        name = db.Column(db.String(150), nullable = True)
        phone = db.Column(PhoneNumberType(region='SG'), nullable = True)
        pdpa = db.Column(db.String(20), nullable = True)
        picture = db.Column(db.LargeBinary,nullable = True)

        last_activity_time = db.Column(db.DateTime, nullable = True)
        created_time = db.Column(db.DateTime, nullable = False)
        mc_expiry_time = db.Column(db.DateTime, nullable = True)

        __tablename__ = 'Users'
        def __repr__(self): return f'<User: {self.uuid}>'
    db.create_all()
    db.session.commit()
    if User.query.get('00000000-0000-0000-0000-000000000000') == None:
        from datetime import datetime
        from uuid import uuid4
        holder = User(
            uuid = '00000000-0000-0000-0000-000000000000',
            username = 'Admin',
            passwd = str(uuid4()),
            created_time = datetime.utcnow()
        )
        db.session.add(holder)
    return User

def make_news_table(db,articles,logger):
    class News(db.Model):
        uuid = db.Column(UUIDType(), primary_key = True)
        url = db.Column(db.Text, unique = True)
        title = db.Column(db.Text, nullable = False)
        picture = db.Column(URLType,nullable = True)
        icon = db.Column(URLType,nullable = True)
        body = db.Column(db.Text, nullable = False)
        publish_time = db.Column(db.DateTime, nullable = False)

        __tablename__ = 'News'
        def __repr__(self): return f'<News: {self.uuid}>'
    db.create_all()
    db.session.commit()

    urls = tuple(set(articles) - set(a[0] for a in News.query.with_entities(News.url).all()))
    if len(urls) > 0:
        from newspaper import Article,Config
        from newspaper.mthreading import NewsPool
        from uuid import uuid4
        config = Config()
        config.memoize_articles = False
        config.fetch_images = True
        config.request_timeout = 20
        config.thread_request_timeout = 20
        config.follow_meta_refresh = True
        config.MIN_WORD_COUNT = 150
        config.MIN_SENT_COUNT = 4
        config.browser_user_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'
        news_pool = NewsPool(config=config)
        articles = tuple(Article(url,config=config) for url in urls)
        news_pool.set(articles,override_threads=4)
        logger.info(f"Articles being downloaded: {urls}")
        news_pool.join()
        for article in articles:
            logger.debug(f"Processing: {article.url}")
            if article.download_state == 1:
                logger.warn(f'Failed to download: {article.url}')
                continue
            article.parse()
            try:
                db.session.add(News(
                    uuid=uuid4(),
                    url=article.url,
                    title=article.title,
                    picture=article.top_image,
                    icon=article.meta_favicon,
                    body=article.text,
                    publish_time=article.publish_date
                    ))
            except Exception as e:
                logger.warn(e)
        db.session.commit()
    return News

def make_post_table(db):
    class Post(db.Model):
        uuid = db.Column(UUIDType(), primary_key = True)
        user_uuid = db.Column(UUIDType(),nullable = False)

        title = db.Column(db.String(200), nullable = False)
        body = db.Column(db.String(2000), nullable = True)

        created_time = db.Column(db.DateTime, nullable = False)

        __tablename__ = 'Posts'
        def __repr__(self): return f'<Post: {self.uuid}>'
    db.create_all()
    db.session.commit()
    return Post

def register_db(app):
    db = SQLAlchemy(app)
    User = make_user_table(db)
    app.logger.debug(f'Users table created.')
    Post = make_post_table(db)
    app.logger.debug(f'Posts table created.')
    News = make_news_table(db,app.config['ARTICLE_URLS'],app.logger)
    app.logger.debug(f'News table created.')

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

    def addDB():
        g.db_sess = db.session
        g.db_users = User
        g.db_posts = Post
        g.db_news = News

    def closeDB(error):
        sess = g.pop('db_sess',None)
        if sess is not None: sess.commit()

    app.logger.debug(f'Database at {app.config["SQLALCHEMY_DATABASE_URI"]} registered.')
    return addDB,closeDB


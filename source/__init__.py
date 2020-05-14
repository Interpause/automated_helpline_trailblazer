from flask_minify import minify
from . import auth,database,forum,news
import functools
def setup_app(func):
    @functools.wraps(func)
    def wrapper(*args,**kwargs):
        app = func(*args,**kwargs)

        app.logger.debug("Registering hooks...")
        #minify(app=app, html=True, js=True, cssless=True) #TODO: disabled during debugging due to caching. Too aggressively removing HTML spaces. Current workaround using U+200C #&8206
        db_adder,db_closer = database.register_db(app)
        app.before_request(db_adder)
        app.teardown_appcontext(db_closer)

        app.logger.debug("Registering blueprints...")
        app.register_blueprint(auth.bp)
        app.register_blueprint(forum.bp)
        app.register_blueprint(news.bp)

        app.logger.info("Ready")
        return app
    return wrapper

from flask import Flask
import os

@setup_app
def make_app(config=None):
    app = Flask(__name__,instance_relative_config=True)
    
    #hardcoded defaults
    app.config.update(
        SQLALCHEMY_DATABASE_URI = 'sqlite+pysqlite:///'+'instance/test.db',
        SQLALCHEMY_TRACK_MODIFICATIONS = True,
        JWT_SECRET_KEY = 'lookMummyIamaSuperLongtestKeylol',
        SECRET_KEY = 'lookMummyIamaSuperLongtestKeylol',
        BOOT_HASH = str(hash("I used datetime in config.py")),
        ARTICLE_URLS = tuple(),
        SERVER_VERSION = 'Default Config Loaded'
    )
    if config is None:
        try: app.config.from_envvar('SERVER_CONFIG')
        except Exception as e:
            app.logger.error(e)
            app.logger.warn("Running using default config...")
    else: app.config.update(**config)

    try: os.makedirs(app.instance_path)
    except OSError: pass

    return app

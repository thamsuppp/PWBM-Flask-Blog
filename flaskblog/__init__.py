from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
#For hashing passwords
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flaskblog.config import Config

import dash
from flask.helpers import get_root_path
from flask_login import login_required


db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
#Tell extension where login route is located
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'


#Application Factory
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    #Add app into initialized extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    #Import and register blueprints
    from flaskblog.users.routes import users
    from flaskblog.posts.routes import posts
    from flaskblog.main.routes import main
    from flaskblog.dashapp1.routes import dash
    app.register_blueprint(users)
    app.register_blueprint(posts)
    app.register_blueprint(main)
    app.register_blueprint(dash)

    #Register dashapp in Flask app server 
    app = register_dashapps(app)

    return app

def register_dashapps(app):
    #Import layout and callbacks from dashapp1 package
    from Dash.dashapp import layout, url_base, external_stylesheets, register_callbacks, UPLOAD_DIRECTORY

    #Instantiate dashapp in current flask server app
    dashapp1 = dash.Dash(__name__,
                         server=app,
                         url_base_pathname=url_base,
                         external_stylesheets=external_stylesheets)

    dashapp1.config.suppress_callback_exceptions = True
    dashapp1.scripts.config.serve_locally = True

    dashapp1.layout = layout

    register_callbacks(dashapp1)
    _protect_dashviews(dashapp1)

    #Add download route
    @app.route("/download/<path:path>")
    def download(path):
        print('download function run')
        print(path)
        #Finds file from upload directory and places it at the route
        return send_from_directory(UPLOAD_DIRECTORY, path, as_attachment=True)

    

    return dashapp1.server


def _protect_dashviews(dashapp):
    for view_func in dashapp.server.view_functions:
        if view_func.startswith(dashapp.url_base_pathname):
            dashapp.server.view_functions[view_func] = login_required(dashapp.server.view_functions[view_func])


from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flaskblog import db, login_manager
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from flask_login import UserMixin
from datetime import datetime


#app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
#db = SQLAlchemy(app)

#migrate = Migrate(app, db, render_as_batch = True)
#manager = Manager(app)
#manager.add_command('db', MigrateCommand)

#Decorator function - extension knows that this is how you get user by ID
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    #max length of username is 20, all usernames must be unique, cannot be null
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    #One-to-many relationship between user and posts. backref - add another column to post model, so you can use author attribute in
    #Post to get user
    posts = db.relationship('Post', backref='author', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_file = db.Column(db.String(20), nullable = True)
     
#if __name__ == '__main__':
#    manager.run()
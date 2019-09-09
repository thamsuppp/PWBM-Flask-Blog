from flask import Blueprint, render_template, request
from flaskblog.models import Post

main = Blueprint('main', __name__)


#Root page of website 
@main.route('/')
def home():
    #From the URL link, get the page to return, default value of 1
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=10)
    return render_template('home.html', posts = posts)


@main.route('/about')
def about():
    return render_template('about.html', title='About')

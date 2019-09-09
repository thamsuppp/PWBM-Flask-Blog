from flask import Blueprint, render_template, url_for, flash, redirect, request, abort
from flask_login import current_user, login_required
from flaskblog import db
from flaskblog.models import Post
from flaskblog.posts.forms import PostForm
from flaskblog.posts.utils import save_picture

from Dash.dashapp import UPLOAD_DIRECTORY
import os


posts = Blueprint('posts', __name__)



@posts.route('/post/new', methods = ['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        
        picture_file = None
        print(form.picture.data)
        #If there is picture data, change profile picture
        if form.picture.data:
            print('form.picture.data has the picture')

            picture_file = save_picture(form.picture.data)
        #Create post and add to database
        post = Post(title=form.title.data, content=form.content.data, author=current_user, image_file=picture_file)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('main.home'))
    return render_template('create_post.html', title='New Post', form=form, legend='New Post')

@posts.route('/post/<int:post_id>')
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)


#If user routed here from Dash app, (secretly) post his post in database and display it in same style as update post


@posts.route('/post/post_from_dash', methods = ['GET', 'POST'])
@login_required
def post_from_dash():
    ###Get string from txt file

    #Get newest txt file from the folder
    def newest_file(path):
        files = os.listdir(path)
        paths = [os.path.join(path, basename) for basename in files if basename.endswith('.txt')]
        return max(paths, key = os.path.getctime)

    #Read from newest txt file 
    file = open(newest_file(UPLOAD_DIRECTORY), 'r')
    if file.mode == 'r':
        contents = file.read()


    #Take newest png file as the image
    image_file = 'graph.png'
    

    ###Post post using string data from txt file
    form = PostForm()
    #2 problems: 1) Post automatically posted when you go to this page 
    if form.validate_on_submit():
        #Save graph in post_images

        post = Post(title=form.title.data, content=form.content.data, author=current_user, image_file=image_file)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('main.home'))
    ###Get existing post data and put as form data
    else:
        form.title.data = 'Dash Post'
        form.content.data = contents
        return render_template('create_post.html', title='Create Post', form=form, legend='Create Post')


@posts.route('/post/<int:post_id>/update', methods = ['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    #Check that current user is author of the post
    if post.author != current_user:
        abort(403) #Forbidden
    form = PostForm()
    #Get existing post data
    
    #Update post if form validates
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated', 'success')
        return redirect(url_for('posts.post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
        form.picture.data = post.image_file
    return render_template('create_post.html', title='Update Post', form=form, legend='Update Post')


@posts.route('/post/<int:post_id>/delete', methods = ['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    #Check that current user is author of the post
    if post.author != current_user:
        abort(403) #Forbidden
    
    #Delete post from db
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted', 'success')
    return redirect(url_for('main.home'))


import os
import secrets
from flask import url_for, current_app


#Saves new image into static folder
def save_picture(form_picture):
    #Create random file name of 8 hexadecimal characters
    random_hex = secrets.token_hex(8)
    #Get file extension
    _, f_ext = os.path.splitext(form_picture.filename)
    #Get filename of picture to save
    picture_fn = random_hex + f_ext
    #Tell Python where to save pictures - app.root_path gives path till the app directory
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)
    form_picture.save(picture_path)

    return picture_fn
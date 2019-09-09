
from flask import Blueprint, render_template, Flask, session, redirect, url_for, escape, request
from flask_login import login_required
from Dash.dashapp import url_base

dash = Blueprint('dash', __name__)

@dash.route('/dash/app')
@login_required
def dashboard():
    return render_template('dashapp.html', title='Dashboard', dash_url = url_base)

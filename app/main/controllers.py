from flask import render_template, request, redirect, url_for
from . import main_bp

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/need_to_login')
def index_with_error():
    return render_template('index.html', error = "Please, login first.")

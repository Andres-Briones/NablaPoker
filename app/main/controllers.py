from flask import render_template, request, redirect, url_for
from . import main_bp

@main_bp.route('/')
def index():
    return render_template('index.html')

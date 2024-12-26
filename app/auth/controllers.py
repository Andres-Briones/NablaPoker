from flask import  render_template, request, redirect, url_for, session, current_app, flash
from app.utils.db import query_db, execute_db
from app.utils.wrappers import render_template_flash

from . import auth_bp

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not password:
            flash("Username and password are required", "error")
            return render_template_flash('register.html', error="Username and password are required")

        existing_user = query_db("SELECT * FROM users WHERE username = ?", (username,), one=True)
        if existing_user:
            flash("Username already taken", "error")
            return render_template_flash('register.html', error="Username already taken")

        execute_db("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        user = query_db("SELECT * FROM users WHERE username = ?", (username,), one=True)
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['db_path'] = current_app.config['HANDS_DATABASE']
        flash("Registered succesfully")
        return '', 200, {'HX-Refresh': 'true'} # Exit the pop by returning nothing and refresh the page to load data in session
    return render_template('register.html')

# This funcion expects to be called within a hx-get or hx-post with target #popup
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = query_db("SELECT * FROM users WHERE username = ? AND password = ?", (username, password), one=True)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['db_path'] = current_app.config['HANDS_DATABASE']
            flash("Login succesfull")
            return '', 200, {'HX-Refresh': 'true'} # Exit the pop by returning nothing and refresh the page to load data in session

        else:
            flash("Invalid credentials", "error")
            return render_template_flash('login.html', error="Invalid credentials")
    elif request.headers.get('HX-Request') == 'true':
        return render_template('login.html')
    else :
        return redirect('/')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Logout succesfull")
    return '', 200, {'HX-Refresh': 'true'}


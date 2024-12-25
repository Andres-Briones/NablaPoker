from flask import  render_template, request, redirect, url_for, session, current_app
from app.utils.db import query_db, execute_db

from . import auth_bp

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not password:
            return render_template('register.html', error="Username and password are required")

        existing_user = query_db("SELECT * FROM users WHERE username = ?", (username,), one=True)
        if existing_user:
            return render_template('register.html', error="Username already taken")

        execute_db("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        user = query_db("SELECT * FROM users WHERE username = ?", (username,), one=True)
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['db_path'] = current_app.config['HANDS_DATABASE']
        return redirect('/')
    return render_template('register.html')

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
            return redirect('/')
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


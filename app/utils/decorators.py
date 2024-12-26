from functools import wraps
from flask import redirect, url_for, session, flash, request, abort
from app.utils.wrappers import render_template_flash

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session: 
            flash("You need to login first", 'error') 
            if request.headers.get('HX-Request') == 'true':
                return render_template_flash('login.html')
            session['redirect_message'] = 'need_to_login'
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function

def htmx_required(f):
    """Ensure the route is accessed via an HTMX request or redirect to the referrer."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.headers.get('HX-Request') != 'true':  # Check if the request is HTMX
            # Redirect to the referring page if not HTMX
            last_page = request.headers.get('Referer')
            if last_page:
                return redirect(last_page)
            session['redirect_message'] = 'htmx_needed'
            return redirect('/')
            #abort(400, description="This route requires an HTMX request, and no referrer was provided.")  # Fallback
        return f(*args, **kwargs)
    return decorated_function

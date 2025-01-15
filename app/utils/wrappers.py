from flask import render_template

def render_template_flash(template_name, **context):
    rendered_template = render_template(template_name, **context)
    flash_template = render_template('flash_messages.html') 
    return rendered_template + flash_template

def render_flash():
    return render_template('flash_messages.html') 


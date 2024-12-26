from app import create_app

app = create_app()

@app.route('/exit_popup')
def exit_popup():
    return ''

if __name__ == '__main__':
    app.run("0.0.0.0", port=5187, debug=True)

from flask import render_template
from flask_sock import Sock
import json

sock = Sock()

@sock.route('/echo')
def echo(ws):
    print("WebSocket connected")  # Check if this prints in the logs
    while True:
        data = json.loads(ws.receive())
        message=data["message"]
        if message == 'close':
            break
        
        message_template = render_template('_messages.html', message=message)
        ws.send(message_template)

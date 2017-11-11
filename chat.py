#!/bin/env python
from app import create_app, socketio
# socketio is an object of the SocketIO interface
# runs from the __init__ python app
app = create_app(debug=True)

if __name__ == '__main__':
    socketio.run(app, host='192.168.0.7')

import eventlet
eventlet.monkey_patch(thread=False) 
from app.extensions import socketio
from app import create_app


app = create_app() # Production
if __name__ == '__main__': # Local development
    socketio.run(app, port=5001, debug=True)
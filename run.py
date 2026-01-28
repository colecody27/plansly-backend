from app.extensions import socketio
from app import create_app


app = create_app()
if __name__ == '__main__':
    # with app.app_context():
        # app.run(debug=True, port=5001)
    socketio.run(app, port=5001, debug=True)
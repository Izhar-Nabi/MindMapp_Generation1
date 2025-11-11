import logging
from flask_socketio import SocketIO

socketio = SocketIO()

class SocketIOHandler(logging.Handler):
    def emit(self, record):
        # Only emit logs from the main application
        if record.name == 'root':
            log_entry = self.format(record)
            socketio.emit('log', {'data': log_entry})

def setup_logging(app):
    # Configure logging to a file
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        filename='app.log',
                        filemode='w')

    # Get the root logger
    logger = logging.getLogger()
    
    # Create a SocketIO handler for your application's logs
    socketio_handler = SocketIOHandler()
    socketio_handler.setLevel(logging.INFO)
    
    # Add the handler to the root logger
    logger.addHandler(socketio_handler)
    
    # Initialize SocketIO with the Flask app
    socketio.init_app(app)
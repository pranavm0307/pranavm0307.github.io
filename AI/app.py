# app.py - Complete Flask Chatbot Application

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import datetime
import time
import uuid
from ai import analyze_input, generate_response

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Store conversations in memory (use database in production)
conversations = {}

@app.route('/')
def index():
    """Serve the main chat interface"""
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return {'status': 'healthy', 'timestamp': datetime.datetime.now().isoformat()}

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected: {request.sid}")
    emit('status', {'message': 'Connected to chatbot server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Client disconnected: {request.sid}")

@socketio.on('send_message')
def handle_message(data):
    """Handle incoming messages from client"""
    try:
        # Extract message data
        user_id = request.sid  # Use session ID as user ID
        message = data.get('message', '').strip()
        
        if not message:
            emit('error', {'message': 'Empty message received'})
            return
        
        print(f"Received message from {user_id}: {message}")
        
        # Initialize conversation history for new users
        if user_id not in conversations:
            conversations[user_id] = []
        
        # Store user message
        user_message_data = {
            'role': 'user',
            'content': message,
            'timestamp': datetime.datetime.now().isoformat()
        }
        conversations[user_id].append(user_message_data)
        
        # Emit typing indicator
        emit('bot_typing', {'typing': True})
        
        # Simulate processing time
        time.sleep(1)
        
        try:
            # Analyze user input
            print("Analyzing input...")
            analysis = analyze_input(message, user_id)
            print(f"Analysis result: {analysis}")
            
            # Generate AI response
            print("Generating response...")
            response_data = generate_response(analysis, message, user_id)
            print(f"Response generated: {response_data['text'][:100]}...")
            
            # Store AI response
            ai_message_data = {
                'role': 'assistant',
                'content': response_data['text'],
                'confidence': response_data['confidence'],
                'intent': response_data['intent'],
                'timestamp': datetime.datetime.now().isoformat()
            }
            conversations[user_id].append(ai_message_data)
            
            # Send response to client
            emit('bot_typing', {'typing': False})
            emit('receive_message', {
                'message': response_data['text'],
                'confidence': round(response_data['confidence'] * 100),
                'intent': response_data['intent'],
                'timestamp': response_data['timestamp']
            })
            
        except Exception as ai_error:
            print(f"AI processing error: {ai_error}")
            emit('bot_typing', {'typing': False})
            emit('receive_message', {
                'message': "I'm having trouble processing that right now. Could you try rephrasing your question?",
                'confidence': 50,
                'intent': 'error',
                'timestamp': datetime.datetime.now().isoformat()
            })
            
    except Exception as e:
        print(f"Error handling message: {e}")
        emit('error', {'message': 'Server error occurred'})

@socketio.on('get_conversation_history')
def handle_get_history():
    """Send conversation history to client"""
    user_id = request.sid
    if user_id in conversations:
        emit('conversation_history', {'history': conversations[user_id]})
    else:
        emit('conversation_history', {'history': []})

@socketio.on('clear_conversation')
def handle_clear_conversation():
    """Clear conversation history"""
    user_id = request.sid
    if user_id in conversations:
        conversations[user_id] = []
    emit('conversation_cleared', {'message': 'Conversation history cleared'})

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    print("🤖 Starting Dynamic AI Chatbot Server...")
    print("📡 Server will be available at: http://localhost:5000")
    print("🔗 Or try: http://127.0.0.1:5000")
    print("⚡ Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Run the Flask app with SocketIO
    socketio.run(
        app, 
        debug=True, 
        host='0.0.0.0', 
        port=5000,
        allow_unsafe_werkzeug=True  # For development only
    )
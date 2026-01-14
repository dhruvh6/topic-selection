from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import mysql.connector
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_classroom_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# --- DATABASE CONFIG ---
db_config = {
    'host': 'localhost',
    'user': 'root',      # CHANGE THIS
    'password': 'root', # CHANGE THIS
    'database': 'topic_selection_db'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/reset', methods=['POST'])
def reset_db():
    data = request.json
    # Simple hardcoded admin password
    if data.get('password') != 'admin123':
        return jsonify({'success': False, 'message': 'Invalid Password'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE topics SET group_number = NULL, selected_at = NULL")
    conn.commit()
    cursor.close()
    conn.close()
    
    # Broadcast reset to all clients
    socketio.emit('reset_event')
    return jsonify({'success': True})

# --- SOCKET EVENTS ---

@socketio.on('connect')
def handle_connect():
    """Send current state of all topics to the newly connected user."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT topic_number, group_number FROM topics")
    topics = cursor.fetchall()
    cursor.close()
    conn.close()
    emit('initial_state', topics)

@socketio.on('select_topic')
def handle_selection(data):
    group_num = data['group_number']
    topic_num = data['topic_number']

    # Validation 1: Group Number Range
    try:
        group_num = int(group_num)
        if not (1 <= group_num <= 35):
            emit('error_message', {'msg': 'Invalid Group Number (1-35 only)'})
            return
    except ValueError:
        emit('error_message', {'msg': 'Invalid Group Number'})
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    # Validation 2: Has this group already selected a topic?
    cursor.execute("SELECT topic_number FROM topics WHERE group_number = %s", (group_num,))
    existing = cursor.fetchone()
    if existing:
        emit('error_message', {'msg': f'Group {group_num} has already taken Topic {existing[0]}!'})
        cursor.close()
        conn.close()
        return

    # Validation 3 & Action: Try to take the topic ATOMICALLY
    # We use rowcount to check if the update actually happened (handling race conditions)
    cursor.execute("""
        UPDATE topics 
        SET group_number = %s, selected_at = NOW() 
        WHERE topic_number = %s AND group_number IS NULL
    """, (group_num, topic_num))
    
    rows_affected = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()

    if rows_affected > 0:
        # Success: Broadcast to everyone (including sender)
        socketio.emit('update_tile', {'topic_number': topic_num, 'group_number': group_num})
    else:
        # Failure: Topic was taken milliseconds ago by someone else
        emit('error_message', {'msg': 'Topic already taken!'})

if __name__ == '__main__':
    # host='0.0.0.0' allows other computers on the network to access it
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
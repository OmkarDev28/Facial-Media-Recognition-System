
from flask import Flask, request, render_template, jsonify, url_for, session, redirect, flash
import face_recognition
import sqlite3
import os
import pickle
import numpy as np
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

# --- Configuration ---
USER_DATA_DIR = 'user_data' 
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MATCH_TOLERANCE = 0.55 
DATABASE = 'main_app.db' # Central database for users and storage keys

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_super_secret_key_change_this_later' 
app.config['USER_DATA_DIR'] = USER_DATA_DIR
app.config['DATABASE'] = DATABASE

# --- Central Database Setup (Users & Storages) ---

def get_main_db():
    db = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    return db

def init_main_db():
    """Initializes the central database."""
    db = get_main_db()
    cursor = db.cursor()
    # Table for user accounts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    # Table to link storage keys to users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS storages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            storage_key TEXT UNIQUE NOT NULL,
            owner_username TEXT NOT NULL,
            FOREIGN KEY (owner_username) REFERENCES users (username)
        )
    ''')
    db.commit()
    db.close()

# --- Helper Functions for Shared Storage ---

def get_storage_path(storage_key):
    return os.path.join(app.config['USER_DATA_DIR'], storage_key)

def get_storage_db_path(storage_key):
    return os.path.join(get_storage_path(storage_key), 'photolib.db')

def get_storage_upload_folder(storage_key):
    return os.path.join(get_storage_path(storage_key), 'uploads')

def init_storage(storage_key):
    """Creates the necessary folders and database for a new storage key."""
    storage_path = get_storage_path(storage_key)
    if not os.path.exists(storage_path):
        os.makedirs(get_storage_upload_folder(storage_key))
        db = sqlite3.connect(get_storage_db_path(storage_key))
        cursor = db.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS faces (id INTEGER PRIMARY KEY AUTOINCREMENT, image_path TEXT NOT NULL, encoding BLOB NOT NULL)')
        cursor.execute('CREATE TABLE IF NOT EXISTS photos (id INTEGER PRIMARY KEY AUTOINCREMENT, path TEXT UNIQUE NOT NULL)')
        db.commit()
        db.close()
        print(f"Initialized new storage for key: {storage_key}")

# --- Storage-Specific Database Functions ---

def get_storage_db(storage_key):
    return sqlite3.connect(get_storage_db_path(storage_key))

def add_photo_to_db(storage_key, image_path):
    db = get_storage_db(storage_key)
    db.execute('INSERT OR IGNORE INTO photos (path) VALUES (?)', (image_path,))
    db.commit()

def count_storage_images(storage_key):
    db = get_storage_db(storage_key)
    count = db.execute('SELECT COUNT(id) FROM photos').fetchone()[0]
    return count

def add_face_encoding(storage_key, image_path, encoding):
    db = get_storage_db(storage_key)
    db.execute('INSERT INTO faces (image_path, encoding) VALUES (?, ?)', (image_path, pickle.dumps(encoding)))
    db.commit()

def get_all_encodings(storage_key):
    db = get_storage_db(storage_key)
    db.row_factory = sqlite3.Row
    rows = db.execute('SELECT image_path, encoding FROM faces').fetchall()
    known_encodings = [pickle.loads(row['encoding']) for row in rows]
    known_paths = [row['image_path'] for row in rows]
    return known_paths, known_encodings

# --- General Helper Functions ---

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_and_store_faces(storage_key, image_path):
    try:
        image = face_recognition.load_image_file(image_path)
        face_locations = face_recognition.face_locations(image, model="hog")
        face_encodings = face_recognition.face_encodings(image, face_locations)
        if face_encodings:
            for encoding in face_encodings:
                add_face_encoding(storage_key, image_path, encoding)
            return len(face_encodings)
        return 0
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return -1

# --- Flask Routes ---

@app.route('/')
def main_app():
    if 'username' not in session: return redirect(url_for('login'))
    if 'storage_key' not in session: return redirect(url_for('select_storage'))
    
    storage_key = session['storage_key']
    image_count = count_storage_images(storage_key)
    return render_template('index.html', username=session['username'], storage_key=storage_key, image_count=image_count)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_main_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if user and check_password_hash(user['password_hash'], password):
            session['username'] = user['username']
            return redirect(url_for('select_storage'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_main_db()
        
        if db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone():
            flash('Username already exists. Please choose another.', 'error')
        else:
            hashed_password = generate_password_hash(password)
            db.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, hashed_password))
            db.commit()
            flash('Account created successfully! You can now log in.', 'success')
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/select_storage', methods=['GET'])
def select_storage():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('select_storage.html')

@app.route('/create_storage', methods=['POST'])
def create_storage():
    if 'username' not in session: return redirect(url_for('login'))
    
    new_key = uuid.uuid4().hex
    db = get_main_db()
    db.execute('INSERT INTO storages (storage_key, owner_username) VALUES (?, ?)', (new_key, session['username']))
    db.commit()
    
    init_storage(new_key)
    session['storage_key'] = new_key
    flash(f'Your new storage has been created! Share this key with others: {new_key}', 'success')
    return redirect(url_for('main_app'))

@app.route('/access_storage', methods=['POST'])
def access_storage():
    if 'username' not in session: return redirect(url_for('login'))
    
    key = request.form.get('storage_key')
    db = get_main_db()
    
    if not key or not db.execute('SELECT id FROM storages WHERE storage_key = ?', (key,)).fetchone():
        flash('Invalid or non-existent storage key.', 'error')
        return redirect(url_for('select_storage'))
    
    session['storage_key'] = key
    return redirect(url_for('main_app'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('storage_key', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'storage_key' not in session: return jsonify({'error': 'Authentication required.'}), 401
    
    storage_key = session['storage_key']
    if 'files' not in request.files: return jsonify({'error': 'No file part'}), 400
    
    files = request.files.getlist('files')
    faces_found_total = 0
    
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(get_storage_upload_folder(storage_key), filename)
            file.save(filepath)
            add_photo_to_db(storage_key, filepath)
            faces_found = process_and_store_faces(storage_key, filepath)
            if faces_found > 0: faces_found_total += faces_found

    image_count = count_storage_images(storage_key)
    return jsonify({'message': f'{faces_found_total} new faces stored.', 'image_count': image_count})

@app.route('/search', methods=['POST'])
def search_face():
    if 'storage_key' not in session: return jsonify({'error': 'Authentication required.'}), 401
    storage_key = session['storage_key']
    if 'selfie' not in request.files: return jsonify({'error': 'No selfie file provided'}), 400
    file = request.files['selfie']
    if not file: return jsonify({'error': 'Invalid file type for selfie'}), 400

    try:
        selfie_image = face_recognition.load_image_file(file)
        selfie_face_locations = face_recognition.face_locations(selfie_image)
        if not selfie_face_locations: return jsonify({'message': 'No face could be detected in the selfie.'})
        selfie_encoding = face_recognition.face_encodings(selfie_image, selfie_face_locations)[0]

        known_paths, known_encodings = get_all_encodings(storage_key)
        if not known_encodings: return jsonify({'message': 'This storage is empty. Please upload photos first.'})

        matches = face_recognition.compare_faces(known_encodings, selfie_encoding, tolerance=MATCH_TOLERANCE)
        matched_image_paths = set()
        for i, match in enumerate(matches):
            if match:
                relative_path = os.path.relpath(known_paths[i], start=get_storage_path(storage_key))
                url_path = url_for('send_user_file', path=os.path.join(storage_key, relative_path))
                matched_image_paths.add(url_path)
        
        if matched_image_paths: return jsonify({'matches': list(matched_image_paths)})
        else: return jsonify({'message': 'No matches found for your selfie.'})
    except Exception as e:
        print(f"An error occurred during search: {e}")
        return jsonify({'error': 'An internal error occurred.'}), 500

from flask import send_from_directory
@app.route('/user_data/<path:path>')
def send_user_file(path):
    return send_from_directory(app.config['USER_DATA_DIR'], path)

if __name__ == '__main__':
    init_main_db()
    if not os.path.exists(USER_DATA_DIR):
        os.makedirs(USER_DATA_DIR)
    app.run(debug=True, port=5001)

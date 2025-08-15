# app.py
# --- Main Flask Web Application ---

from flask import Flask, request, render_template, jsonify, url_for
import face_recognition
import sqlite3
import os
import pickle
import numpy as np
from werkzeug.utils import secure_filename

# --- Configuration ---
UPLOAD_FOLDER = 'static/uploads'
DATABASE = 'photolib.db'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
# Lower tolerance means stricter matches
MATCH_TOLERANCE = 0.55 

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- Database Functions ---

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    """Initializes the database and creates the table if it doesn't exist."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS faces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT NOT NULL,
                encoding BLOB NOT NULL
            )
        ''')
        db.commit()
        print("Database initialized.")

def add_face_encoding(image_path, encoding):
    """Adds a face encoding to the database."""
    db = get_db()
    # Serialize the numpy array for storage
    serialized_encoding = pickle.dumps(encoding)
    db.execute('INSERT INTO faces (image_path, encoding) VALUES (?, ?)',
               (image_path, serialized_encoding))
    db.commit()

def get_all_encodings():
    """Retrieves all face encodings from the database."""
    db = get_db()
    cursor = db.execute('SELECT image_path, encoding FROM faces')
    rows = cursor.fetchall()
    
    known_encodings = []
    known_paths = []
    for row in rows:
        known_paths.append(row['image_path'])
        # Deserialize the encoding back into a numpy array
        known_encodings.append(pickle.loads(row['encoding']))
        
    return known_paths, known_encodings

# --- Helper Functions ---

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_and_store_faces(image_path):
    """Loads an image, finds faces, and stores their encodings in the DB."""
    try:
        print(f"Processing {image_path} for faces...")
        image = face_recognition.load_image_file(image_path)
        # Using 'hog' for speed. Change to 'cnn' for higher accuracy if you have a GPU.
        face_locations = face_recognition.face_locations(image, model="hog")
        face_encodings = face_recognition.face_encodings(image, face_locations)

        if face_encodings:
            for encoding in face_encodings:
                add_face_encoding(image_path, encoding)
            print(f"  -> Found and stored {len(face_encodings)} face(s).")
            return len(face_encodings)
        else:
            print("  -> No faces found in this image.")
            return 0
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return -1


# --- Flask Routes ---

@app.route('/', methods=['GET'])
def index():
    """Renders the main page."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handles uploading of new library photos."""
    if 'files' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    files = request.files.getlist('files')
    faces_found_total = 0
    
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Process the uploaded image for faces
            faces_found = process_and_store_faces(filepath)
            if faces_found > 0:
                faces_found_total += faces_found

    return jsonify({'message': f'Files uploaded successfully. Found and stored {faces_found_total} new faces.'})

@app.route('/search', methods=['POST'])
def search_face():
    """Handles the selfie upload and searches for matches."""
    if 'selfie' not in request.files:
        return jsonify({'error': 'No selfie file provided'}), 400
        
    file = request.files['selfie']
    if not file or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type for selfie'}), 400

    try:
        # Load the uploaded selfie
        selfie_image = face_recognition.load_image_file(file)
        selfie_face_locations = face_recognition.face_locations(selfie_image)
        
        if not selfie_face_locations:
            return jsonify({'message': 'No face could be detected in the selfie.'})
            
        selfie_encoding = face_recognition.face_encodings(selfie_image, selfie_face_locations)[0]

        # Retrieve all encodings from the database
        known_paths, known_encodings = get_all_encodings()
        
        if not known_encodings:
            return jsonify({'message': 'The photo library is empty. Please upload photos first.'})

        # Compare the selfie with all known faces
        matches = face_recognition.compare_faces(known_encodings, selfie_encoding, tolerance=MATCH_TOLERANCE)
        
        matched_image_paths = set()
        for i, match in enumerate(matches):
            if match:
                # Convert file path to a URL
                url_path = url_for('static', filename=os.path.join('uploads', os.path.basename(known_paths[i])))
                matched_image_paths.add(url_path)
        
        if matched_image_paths:
            return jsonify({'matches': list(matched_image_paths)})
        else:
            return jsonify({'message': 'No matches found for your selfie in the library.'})

    except Exception as e:
        print(f"An error occurred during search: {e}")
        return jsonify({'error': 'An internal error occurred during the search.'}), 500


# --- Main Execution ---
if __name__ == '__main__':
    # Create necessary folders and initialize DB on first run
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    init_db()
    # Runs the web server
    app.run(debug=True, port=5001)
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import pymysql
import base64
import face_recognition
from io import BytesIO
import numpy as np


app = Flask(__name__)
app.secret_key = "super_secret_key"  # Replace with a secure key

# Database connection
db = pymysql.connect(
    host="localhost",
    user="root",       # Change this to your MySQL username
    password="",       # Change this to your MySQL password
    database="signup_app"
)
cursor = db.cursor()

# Global variables
encodeListKnown = []  # List of face encodings of known users
classNames = []  # List of known user names

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        photo_data = request.form['photo'].split(",")[1]  # Extract base64 data
        photo_blob = base64.b64decode(photo_data)

        # Insert data into the database
        query = "INSERT INTO users (email, password, photo) VALUES (%s, %s, %s)"
        try:
            cursor.execute(query, (email, password, photo_blob))
            db.commit()

            # Add this user to the known face encodings list
            new_user_photo = face_recognition.load_image_file(BytesIO(photo_blob))
            new_user_encoding = face_recognition.face_encodings(new_user_photo)[0]
            encodeListKnown.append(new_user_encoding)
            classNames.append(email)  # Store the user's email as the name for the face

            return jsonify({"message": "Signup successful!"})
        except pymysql.IntegrityError:
            return jsonify({"error": "Email already registered!"}), 400

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        photo_data = request.form['photo'].split(",")[1]  # Extract base64 data
        login_photo = base64.b64decode(photo_data)

        # Check credentials
        query = "SELECT id, photo FROM users WHERE email = %s AND password = %s"
        cursor.execute(query, (email, password))
        user = cursor.fetchone()

        if user:
            user_id, stored_photo_blob = user

            # Convert stored photo and login photo to face_recognition-compatible format
            stored_photo = face_recognition.load_image_file(BytesIO(stored_photo_blob))
            login_photo = face_recognition.load_image_file(BytesIO(login_photo))

            # Get face encodings
            try:
                stored_encoding = face_recognition.face_encodings(stored_photo)[0]
                login_encoding = face_recognition.face_encodings(login_photo)[0]
            except IndexError:
                return jsonify({"error": "Face not detected in one of the photos!"}), 400

            # Compare faces
            match = face_recognition.compare_faces([stored_encoding], login_encoding)[0]

            if match:
                session['user_id'] = user_id
                # Add this user to the known face encodings list for future recognition
                encodeListKnown.append(stored_encoding)
                classNames.append(email)  # Store the user's email as the name for the face
                return jsonify({"success": True, "redirect_url": url_for('index')})
            else:
                return jsonify({"success": False, "redirect_url": url_for('login')})
        else:
            return jsonify({"success": False, "redirect_url": url_for('login')})

    return render_template('login.html')

@app.route('/verify', methods=['POST'])
def verify():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized access!"}), 401

    user_id = session['user_id']
    photo_data = request.form['photo'].split(",")[1]  # Extract base64 data
    verification_photo = base64.b64decode(photo_data)

    # Fetch stored photo for the logged-in user
    query = "SELECT photo FROM users WHERE id = %s"
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()

    if not result:
        return jsonify({"error": "User not found!"}), 404

    stored_photo_blob = result[0]

    # Convert photos to face_recognition-compatible format
    stored_photo = face_recognition.load_image_file(BytesIO(stored_photo_blob))
    verification_photo = face_recognition.load_image_file(BytesIO(verification_photo))

    # Get face encodings
    try:
        stored_encoding = face_recognition.face_encodings(stored_photo)[0]
        verification_encoding = face_recognition.face_encodings(verification_photo)[0]
    except IndexError:
        return jsonify({"error": "Face not detected in one of the photos!"}), 400

    # Compare faces
    match = face_recognition.compare_faces([stored_encoding], verification_encoding)[0]

    if match:
        return jsonify({"success": True, "message": "Verification successful!", "redirect_url": url_for('live_recognition')})
    else:
        return jsonify({"success": False, "message": "Face mismatch! Access denied."})

@app.route('/live_recognition')
def live_recognition():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('live_recognition.html')

@app.route('/verify_live', methods=['POST'])
def verify_live():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized access!"}), 401

    # Get the current user's photo from the database or session
    user_id = session['user_id']
    if 'stored_encoding' not in session:
        # Fetch stored photo from the database
        query = "SELECT photo FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"error": "User not found!"}), 404

        stored_photo_blob = result[0]

        # Decode and process stored photo
        try:
            stored_photo = face_recognition.load_image_file(BytesIO(stored_photo_blob))
            stored_encoding = face_recognition.face_encodings(stored_photo)
            if not stored_encoding:
                return jsonify({"error": "No face detected in stored photo!"}), 400
            stored_encoding = stored_encoding[0]
            session['stored_encoding'] = stored_encoding.tolist()  # Cache encoding in session
        except Exception as e:
            return jsonify({"error": f"Error processing stored photo: {str(e)}"}), 500
    else:
        # Use cached encoding from session
        stored_encoding = np.array(session['stored_encoding'])  # Convert back to numpy array

    # Get the incoming image from the request
    try:
        data = request.get_json()
        if 'photo' not in data:
            return jsonify({"error": "Photo data missing!"}), 400

        photo_data = data['photo'].split(',')[1]  # Extract base64 data
        incoming_image = base64.b64decode(photo_data)

        # Decode and process incoming photo
        incoming_photo = face_recognition.load_image_file(BytesIO(incoming_image))
        incoming_encoding = face_recognition.face_encodings(incoming_photo)
        if not incoming_encoding:
            return jsonify({"error": "No face detected in incoming photo!"}), 400
        incoming_encoding = incoming_encoding[0]
    except Exception as e:
        return jsonify({"error": f"Error processing incoming photo: {str(e)}"}), 400

    # Compare the incoming face encoding with the stored one
    try:
        match = face_recognition.compare_faces([stored_encoding], incoming_encoding)[0]
    except Exception as e:
        return jsonify({"error": f"Error during face comparison: {str(e)}"}), 500

    # Check if matched user matches the session user
    if match:
        return jsonify({"success": True, "user": session.get('username', 'User Identified')})
    else:
        return jsonify({"success": False, "user": "Unknown"})
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    # Clear the session
    session.clear()

    # If it's an API-based system, return a JSON response
    if request.is_json:
        return jsonify({"success": True, "message": "Logged out successfully!"})

    # Otherwise, redirect to the login page
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)



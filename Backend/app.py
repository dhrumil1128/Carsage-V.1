import os
import json
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_cors import CORS
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# === Configuration ===
# Define paths for car recommendation system
CAR_DATA_PATH = r'C:\Users\Dhrumil\Desktop\New folder\Car Recommandation System\CARS_1.csv'
MODEL_PATH = r'C:\Users\Dhrumil\Desktop\New folder\Car Recommandation System\best_car_model.keras'
CLASS_INDICES_PATH = r'C:\Users\Dhrumil\Desktop\New folder\Car Recommandation System\class_indices.json'
UPLOAD_FOLDER = r'C:\Users\Dhrumil\Desktop\New folder\Car Recommandation System\uploads'
TEMPLATE_FOLDER = r'C:\Users\Dhrumil\Desktop\New folder\Car Recommandation System\Frontend'

# Initialize Flask app
app = Flask(__name__, template_folder=TEMPLATE_FOLDER)
CORS(app)  # Enable Cross-Origin Resource Sharing

# Configure upload folder
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# === Flask-SQLAlchemy Configuration ===
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///feedback.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and mail extensions
db = SQLAlchemy(app)
mail = Mail(app)

# === Feedback Model ===
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    feedback = db.Column(db.Text, nullable=False)

# === Load Car Recommendation Data ===
try:
    car_data = pd.read_csv(CAR_DATA_PATH)
    print("Car recommendation data loaded successfully!")
except Exception as e:
    print(f"Error loading car recommendation data: {e}")
    exit()

# === Load the Trained Model ===
try:
    model = load_model(MODEL_PATH)
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    exit()

# === Load Class Indices ===
try:
    with open(CLASS_INDICES_PATH, 'r', encoding='utf-8') as f:
        class_indices = json.load(f)
    car_classes = {v: k for k, v in class_indices.items()}
    print("Class indices loaded successfully!")
except Exception as e:
    print(f"Error loading class indices: {e}")
    exit()

# === Helper Functions ===
def preprocess_image(image_path):
    try:
        img = image.load_img(image_path, target_size=(224, 224))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = img_array / 255.0
        return img_array
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

def predict_car(image_path):
    try:
        img_array = preprocess_image(image_path)
        if img_array is None:
            return "Error in image preprocessing."
        predictions = model.predict(img_array)
        predicted_class_index = np.argmax(predictions)
        predicted_class_name = car_classes.get(predicted_class_index, "Unknown")
        return predicted_class_name
    except Exception as e:
        print(f"Error in prediction: {e}")
        return "Unknown"

# === Routes ===

# Feedback submission route
@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    feedback = data.get('feedback')

    if not name or not email or not feedback:
        return jsonify({'error': 'All fields are required!'}), 400

    new_feedback = Feedback(name=name, email=email, feedback=feedback)
    try:
        db.session.add(new_feedback)
        db.session.commit()

        message = Message(
            subject=f"Feedback from {name}",
            recipients=[os.getenv('MAIL_USERNAME')],
            body=f"Name: {name}\nEmail: {email}\nFeedback:\n{feedback}"
        )
        mail.send(message)

        return jsonify({'message': 'Feedback submitted successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Home route
@app.route('/')
def home():
    return render_template('Service2.html')

# Car recommendation route
@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        user_input = request.json
        seating_capacity = float(user_input.get('seatingCapacity', 0))
        fuel_type = user_input.get('fuelType', '').capitalize()
        starting_price = int(user_input.get('startingPrice', 0))
        ending_price = int(user_input.get('endingPrice', 0))
        transmission_type = user_input.get('transmissionType', '').capitalize()
        body_type = user_input.get('bodyType', '').capitalize()

        filtered_data = car_data[
            (car_data['seating_capacity'] >= seating_capacity) &
            (car_data['fuel_type'] == fuel_type) &
            (car_data['starting_price'] >= starting_price) &
            (car_data['ending_price'] <= ending_price) &
            (car_data['transmission_type'] == transmission_type) &
            (car_data['body_type'] == body_type)
        ]

        recommendations = filtered_data.to_dict(orient='records')
        return jsonify({"recommendations": recommendations})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Car prediction route
@app.route('/predict', methods=['POST'])
def predict():
    try:
        if 'carImage' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['carImage']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        filepath = os.path.abspath(filepath)
        file.save(filepath)

        predicted_car = predict_car(filepath)
        return jsonify({"predicted_car": predicted_car})
    except Exception as e:
        return jsonify({"error": "Prediction failed due to an internal error"}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

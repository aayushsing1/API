from flask import Flask, request, jsonify, url_for
from flask_cors import CORS
from g4f.client import Client
from pymongo import MongoClient
import random
from flask_mail import Mail, Message
import string


application = Flask(__name__)
CORS(application)  # Enable CORS for all routes

client = Client()

# MongoDB configuration
uri = 'mongodb+srv://asdevlopers02:6fXfDFKNImSUAiKJ@cluster0.us8nw6q.mongodb.net/'

db_client = MongoClient(uri)
db = db_client['user_database']
users_collection = db['users']

application.config['MAIL_SERVER'] = 'smtp.gmail.com'
application.config['MAIL_PORT'] = 587
application.config['MAIL_USE_TLS'] = True
application.config['MAIL_USE_SSL'] = False
application.config['MAIL_USERNAME'] = 'himanshu.k822887@gmail.com'
application.config['MAIL_PASSWORD'] = 'vqeq nzsi hlzx sohb'
application.config['MAIL_DEFAULT_SENDER'] = 'BrainWave'

mail = Mail(application)

@application.route('/')
def open():
    return 'API Request Success'

@application.route('/generate_response', methods=['POST'])
def generate_response():
    content = request.json.get('content')
    
    if not content:
        return jsonify({"error": "Content not provided"}), 400

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": content}],
        )
        generated_response = response.choices[0].message.content

        return jsonify({"response": generated_response}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@application.route('/generate_gpt', methods=['POST'])
def generate_gpt():
    content = request.json.get('content')
    
    if not content:
        return jsonify({"error": "Content not provided"}), 400

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": content}],
        )
        generated_response = response.choices[0].message.content

        return jsonify({"response": generated_response}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Signup API
@application.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data['username']
    email = data['email']
    password = data['password']

    if users_collection.find_one({'email': email}):
        return jsonify({'message': 'Username already exists'}), 400

    # Insert user into the database
    user = {'username': username, 'email':email, 'password': password}
    users_collection.insert_one(user)

    return jsonify({'message': 'User created successfully'}), 201

# Login API
@application.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data['email']
    password = data['password']

    user = users_collection.find_one({'email': email})
    username = user['username']
    print(username)

    if not user or user['password'] != password:
        return jsonify({'message': 'Invalid username or password'}), 401
    
    return jsonify({'message': 'Login successful', 'username': user['username']}), 200


# API endpoint for getting user profile
@application.route('/get_profile', methods=['GET'])
def get_profile():
    username = request.args.get('username')

    # Query MongoDB for user with provided username
    user_data = users_collection.find_one({'username': username}, {'_id': 0})
    if user_data:
        return jsonify(user_data), 200
    else:
        return jsonify({'error': 'User not found'}), 404
    
# API endpoint for updating user password
@application.route('/update_password', methods=['POST'])
def update_password():
    # Extract username and new password from form data
    username = request.form.get('username')
    new_password = request.form.get('new_password')
    
    # Update user's password in MongoDB
    result = users_collection.update_one({'username': username}, {'$set': {'password': new_password}})
    
    if result.modified_count > 0:
        return jsonify({'message': 'Password updated successfully'}), 200
    else:
        return jsonify({'error': 'User not found'}), 404


def send_email(email, email_subject, email_content):
    try:
        msg = Message(email_subject, sender=application.config['MAIL_USERNAME'], recipients=[email])
        msg.body = email_content
        mail.send(msg)
        print("Email sent successfully!")
    except Exception as e:
        print("Failed to send email:", e)


# Generate a random password
def generate_password(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))


@application.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.json
    email = data.get('email')

    if not email:
        return jsonify({'message': 'Email is required'}), 400

    user = users_collection.find_one({'email': email})
    if not user:
        return jsonify({'message': 'User with this email does not exist'}), 404

    new_password = generate_password()

    users_collection.update_one({'email': email}, {'$set': {'password': new_password}})

    # Send an email to the user with the new password
    email_subject = 'Password Reset'
    email_content = f'Your new password is: {new_password}. Please reset your password after logging in.'
    send_email(email, email_subject, email_content)

    return jsonify({'message': 'Password reset successful. Check your email for the new password.'}), 200


if __name__ == '__main__':
    application.run()
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
from dotenv import load_dotenv
from db import get_db_connection
load_dotenv()

app = Flask(__name__)
CORS(app)

AZURE_API_KEY = os.getenv("AZURE_API_KEY")
AZURE_API_URL = os.getenv("AZURE_API_URL")

# === SIGNUP API ===
@app.route('/api/users/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    name = data.get("name")

    if not email or not password or not name:
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if user already exists
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"error": "User already exists"}), 400

    # Insert new user record
    cursor.execute(
        "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
        (name, email, password)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "User registered successfully"})

# === LOGIN API ===
@app.route('/api/users/login', methods=['POST'])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        return jsonify({"message": "Login successful", "user": user})
    else:
        return jsonify({"message": "Invalid credentials"}), 401

# === AZURE OPENAI CHAT API ===
@app.route('/api/ai/chat', methods=['POST'])
def chat_with_azure():
    user_message = request.json.get("message")

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_API_KEY
    }

    body = {
        "messages": [
            {"role": "system", "content": "You are ElevateU AI assistant."},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(AZURE_API_URL, headers=headers, json=body)
        response.raise_for_status()
        data = response.json()
        bot_reply = data['choices'][0]['message']['content']
        return jsonify({"response": bot_reply})

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

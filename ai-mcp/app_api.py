import asyncio
import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Ensure the root directory is in the path so python can locate main_agent
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main_agent import run_agent_turn_anonymous

# Load credentials from your local .env file
load_dotenv()
app = Flask(__name__)

# Enable CORS so your frontend HTML/JS interface can securely post data here
CORS(app)

@app.route('/', methods=['GET'])
def home_health_check():
    """
    Simple GET route so opening http://127.0.0.1:5000 in a browser 
    shows a friendly status message instead of a 404 error.
    """
    return jsonify({
        "status": "online",
        "message": "IT Help Desk Agent Backend API Bridge Engine is running successfully!",
        "endpoints": ["/chat", "/api/chat"]
    }), 200

# FIX: Accepting both routes resolves any frontend mapping mismatch safely
@app.route('/chat', methods=['POST'])
@app.route('/api/chat', methods=['POST'])
def chat_endpoint():
    """
    HTTP POST Endpoint that accepts natural language messages from the website,
    passes them into the Gemini orchestrator, and returns the AI's response.
    """
    data = request.json or {}
    user_message = data.get("message", "").strip()
    employee_id = data.get("employee_id", "E1402")

    if not user_message:
        return jsonify({"error": "Message content cannot be blank."}), 400

    try:
        # Execute the asynchronous Gemini + MCP tool pipeline within Flask's synchronous context
        ai_response = asyncio.run(run_agent_turn_anonymous(user_message, employee_id))
        return jsonify({"response": ai_response})
    except Exception as e:
        print(f"[API ERROR] Exception encountered during runtime processing: {str(e)}")
        return jsonify({"error": f"Internal server processing fault: {str(e)}"}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print(" IT Help Desk Agent Backend API Bridge Engine")
    print(" Listening actively on: http://127.0.0.1:5000")
    print("="*60 + "\n")
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
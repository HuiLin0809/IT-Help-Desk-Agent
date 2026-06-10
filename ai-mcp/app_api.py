import asyncio
import os
import sys
import re
import subprocess  # Added to launch external scripts
import atexit      # Added to ensure safe background script cleanup
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.sse import sse_client

# Ensure sibling file modules can be imported correctly
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
from main_agent import _execute_core_agent_loop

load_dotenv()

app = Flask(__name__)
CORS(app)

# Keep track of background processes so we can shut them down later
background_processes = []

def launch_background_utilities():
    """Launches mock_script.py and alert_listener.py automatically on startup."""
    python_executable = sys.executable or "python"
    
    # 1. Path to your background files
    mock_script_path = os.path.join(BASE_DIR, "mock_script.py")
    listener_script_path = os.path.join(BASE_DIR, "alert_listener.py")
    
    print("\n" + "="*60)
    print(" INITIALIZING BACKGROUND INFRASTRUCTURE SUBPROCESSES")
    print("="*60)
    
    # 2. Launch alert_listener.py (Runs continuously in the background)
    if os.path.exists(listener_script_path):
        print("📡 Launching alert_listener.py in background...")
        try:
            listener_proc = subprocess.Popen(
                [python_executable, "-m", "dotenv", "run", "python", listener_script_path],
                cwd=BASE_DIR
            )
            background_processes.append(listener_proc)
        except Exception as e:
            print(f"❌ Failed to launch alert_listener.py: {e}")
    else:
        print(f"⚠️ alert_listener.py not found at {listener_script_path}")

    # 3. Launch mock_script.py (Runs once, injects data, and exits)
    if os.path.exists(mock_script_path):
        print("⚠️ Launching mock_script.py to inject initial demo database alerts...")
        try:
            # We don't append this to tracking because it completes and exits on its own
            subprocess.Popen(
                [python_executable, "-m", "dotenv", "run", "python", mock_script_path],
                cwd=BASE_DIR
            )
        except Exception as e:
            print(f"❌ Failed to launch mock_script.py: {e}")
    else:
        print(f"⚠️ mock_script.py not found at {mock_script_path}")
        
    print("="*60 + "\n")

def cleanup_background_processes():
    """Terminals background tasks safely when Flask closes to prevent orphaned memory loops."""
    print("\nStopping background utility engines...")
    for proc in background_processes:
        if proc.poll() is None:  # Check if it's still running
            proc.terminate()
            print(f"Terminated process PID: {proc.pid}")

# Register the cleanup hook with Python's exit controller
atexit.register(cleanup_background_processes)


@app.route('/', methods=['GET'])
def health():
    return jsonify({"status": "online", "engine": "Flask Core Gateway"}), 200

@app.route('/chat', methods=['POST'])
@app.route('/api/chat', methods=['POST'])
def handle_chat_route():
    data = request.json or {}
    user_message = data.get("message", "").strip()
    employee_id = data.get("employee_id", "").strip()
    
    if not employee_id:
        id_match = re.search(r"\b[A-Za-z]\d+\b", user_message)
        if id_match:
            employee_id = id_match.group(0).upper()
        else:
            employee_id = "E1402"
            
    if not user_message:
        return jsonify({"error": "Empty strings are invalid payloads."}), 400
        
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def stream_context_to_server():
            async with sse_client("http://127.0.0.1:8000/sse") as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    return await _execute_core_agent_loop(session, user_message, employee_id)

        ai_response = loop.run_until_complete(stream_context_to_server())
        return jsonify({"response": ai_response})
        
    except Exception as err:
        print(f"[GATEWAY ERROR] Traceback details: {str(err)}")
        return jsonify({"error": f"Internal process generation fault: {str(err)}"}), 500

if __name__ == '__main__':
    # Launch your scripts right before Flask handles port allocation
    launch_background_utilities()
    
    print("="*60)
    print(" Booting up IT Help Desk Agent API Core Endpoint Engines")
    print("="*60)
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
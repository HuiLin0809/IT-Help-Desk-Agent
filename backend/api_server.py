import os
import os
from google import genai
from google.genai import types
from datetime import datetime, timezone
from typing import Any, Annotated

from bson import ObjectId
from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# Initialize the client specifically for Vertex AI Agent Platform services
gemini_client = genai.Client(
    api_key = "YOUR_GCP_API_KEY_HERE" # Removed for security
    http_options={"api_version": "v1"} # This forces the SDK to route via enterprise cloud endpoints
)

# Automatically find and safely pull secrets from your local .env file
load_dotenv(find_dotenv())

# Read connection string dynamically from environment variables
MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    raise RuntimeError(
        "Missing required environment variable: MONGODB_URI. "
        "Please check that it is defined inside your local .env file."
    )

client = MongoClient(MONGODB_URI)
db = client.it_helpdesk_db  # Ensuring this points to the correct master database
alerts_collection = db.System_Alerts
notifications_collection = db.User_Notifications

app = FastAPI(
    title="IT Help Desk Backend API",
    description="Postman/API endpoints for Person 4's frontend to read proactive alerts.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MockAlertRequest(BaseModel):
    employee_id: str = "E999"
    device_model: str = "Dell XPS 15"
    alert_type: str = "CRITICAL_WARNING"
    issue: str = "storage_capacity"
    reading: str = "96%"


def mongo_to_json(value: Any) -> Any:
    """Convert MongoDB ObjectId/datetime values into JSON-safe values."""
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [mongo_to_json(item) for item in value]
    if isinstance(value, dict):
        return {key: mongo_to_json(item) for key, item in value.items()}
    return value

# Add this request body schema near your other Pydantic models
class ChatMessageRequest(BaseModel):
    message: str

# Add this endpoint to handle incoming chat from the frontend
# Put this single line RIGHT ABOVE your @app.post("/chat") function to keep track of the ID state
current_session_id = None

@app.post("/chat")
def handle_chat_message(payload: ChatMessageRequest) -> dict[str, Any]:
    global current_session_id
    user_text = payload.message.strip().lower()

    # =========================================================================
    # STEP 1: RESET COMMAND (Just in case you want to restart the demo clean)
    # =========================================================================
    if "reset" in user_text or "restart" in user_text:
        current_session_id = None
        return {
            "success": True,
            "reply": "NovaDesk system reset. Session cleared. Please say 'hi' to begin.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    # =========================================================================
    # STEP 2: THE WELCOME GREETING (Forces user to provide an ID)
    # =========================================================================
    if user_text in ["hi", "hello", "hey", "good morning", "good afternoon"] and current_session_id is None:
        return {
            "success": True,
            "reply": "Welcome to NovaDesk Corporate IT Support. To retrieve your device diagnostics and history, please enter your corporate Employee ID.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    # =========================================================================
    # STEP 3: ID CHECKER (Catches when the user submits an ID)
    # =========================================================================
    # Look for an ID pattern (like e1402, 99999, id: 99999, etc.)
    if current_session_id is None:
        if "99999" in user_text or "unknown" in user_text:
            # DO NOT save this ID. Completely block them right here.
            return {
                "success": True,
                "reply": "System Alert: Employee ID is not registered in our database. Access Denied. Please contact HR or your IT Department to register your device tracker.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        elif "e1402" in user_text or "1402" in user_text:
            current_session_id = "E1402"
            return {
                "success": True,
                "reply": "Employee ID: E1402 successfully verified. Connected to MongoDB asset register. Found: Dell Corporate Laptop. What hardware or system performance issue are you experiencing today?",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            # If they typed something random without giving a proper ID first
            return {
                "success": True,
                "reply": "Access restricted. Please enter a valid registered Employee ID to access corporate IT diagnostics.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    # =========================================================================
    # STEP 4: VERIFIED IT SUPPORT FLOW (Only works AFTER E1402 is verified)
    # =========================================================================
    if current_session_id == "E1402":
        if "fan" in user_text or "loud" in user_text or "overheating" in user_text:
            ai_response = (
                "NovaDesk Diagnostics: I detect a sustained 92% CPU load on your Dell asset, causing the fan to run at max RPM. You also had an old report about flickering screen."
                "Please open Task Manager to check for rogue background processes. If the loud noise and overheating persist, "
                "type 'create ticket' so I can schedule a physical thermal paste and screen replacement with our IT assistant physically."
            )
        elif "ticket" in user_text or "fix" in user_text:
            ai_response = (
                "Escalation Protocol Initiated. Ticket #TK-88341 has been automatically generated in your name (Employee ID: E1402). "
                "Priority: HIGH. Assigned to Hardware Maintenance Team. You will receive an email confirmation shortly."
            )
        else:
            ai_response = f"NovaDesk is listening (Employee ID: E1402). Please describe your laptop symptoms, or type 'create ticket' to escalate."
            
        return {
            "success": True,
            "reply": ai_response,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "IT Help Desk Backend API"}


@app.post(
    "/mock-alert",
    responses={500: {"description": "MongoDB insert failed"}}
)
def create_mock_alert(alert: MockAlertRequest) -> dict[str, Any]:
    """Insert a mock telemetry alert into System_Alerts for Postman testing."""
    document = {
        "employee_id": alert.employee_id,
        "device_model": alert.device_model,
        "alert_type": alert.alert_type,
        "issue": alert.issue,
        "reading": alert.reading,
        "status": "UNREAD",
        "timestamp": datetime.now(timezone.utc),
        "source": "Postman API",
    }

    try:
        result = alerts_collection.insert_one(document)
    except PyMongoError as exc:
        raise HTTPException(status_code=500, detail=f"MongoDB insert failed: {exc}") from exc

    return {
        "success": True,
        "message": "Mock alert inserted. If alert_listener.py is running, it will create a User_Notifications record.",
        "alert_id": str(result.inserted_id),
    }


@app.get(
    "/notifications/{employee_id}",
    responses={500: {"description": "MongoDB read failed"}}
)
def get_notifications(
    employee_id: str,
    status: Annotated[str | None, Query(description="Use ALL to return every status.")] = "UNREAD",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> dict[str, Any]:
    """Return proactive messages for Person 4's frontend."""
    query: dict[str, Any] = {"employee_id": employee_id}
    if status and status.upper() != "ALL":
        query["status"] = status.upper()

    try:
        documents = list(
            notifications_collection.find(query)
            .sort("created_at", -1)
            .limit(limit)
        )
    except PyMongoError as exc:
        raise HTTPException(status_code=500, detail=f"MongoDB read failed: {exc}") from exc

    return {
        "employee_id": employee_id,
        "count": len(documents),
        "notifications": mongo_to_json(documents),
    }


@app.patch(
    "/notifications/{notification_id}/read",
    responses={
        400: {"description": "Invalid notification_id"},
        404: {"description": "Notification not found"},
        500: {"description": "MongoDB update failed"}
    }
)
def mark_notification_read(notification_id: str) -> dict[str, Any]:
    """Mark one frontend notification as READ after the UI displays it."""
    try:
        object_id = ObjectId(notification_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid notification_id.") from exc

    try:
        result = notifications_collection.update_one(
            {"_id": object_id},
            {"$set": {"status": "READ", "read_at": datetime.now(timezone.utc)}},
        )
    except PyMongoError as exc:
        raise HTTPException(status_code=500, detail=f"MongoDB update failed: {exc}") from exc

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found.")

    return {"success": True, "notification_id": notification_id, "status": "READ"}


@app.get(
    "/alerts/recent",
    responses={500: {"description": "MongoDB read failed"}}
)
def get_recent_alerts(
    limit: Annotated[int, Query(ge=1, le=100)] = 20
) -> dict[str, Any]:
    """Return recent raw System_Alerts records for Postman/demo verification."""
    try:
        documents = list(alerts_collection.find().sort("timestamp", -1).limit(limit))
    except PyMongoError as exc:
        raise HTTPException(status_code=500, detail=f"MongoDB read failed: {exc}") from exc

    return {"count": len(documents), "alerts": mongo_to_json(documents)}
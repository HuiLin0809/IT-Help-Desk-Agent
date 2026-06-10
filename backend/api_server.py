import os
from datetime import datetime, timezone
from typing import Any, Annotated

from bson import ObjectId
from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.errors import PyMongoError

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
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from google import genai
from pymongo import MongoClient


load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if not MONGODB_URI:
    raise RuntimeError("Missing required environment variable: MONGODB_URI")


def build_fallback_message(device, issue, reading):
    """Create a demo-safe proactive message when Gemini is unavailable."""
    device_text = device or "your device"
    issue_text = str(issue or "a system health warning").replace("_", " ")
    reading_text = reading or "a critical level"
    return (
        f"Hey! I noticed {device_text} is reporting {issue_text} at {reading_text}. "
        "This could affect your work soon; would you like me to guide you through a quick fix?"
    )


def save_frontend_notification(
    alerts_collection,
    notifications_collection,
    alert_data,
    employee,
    device,
    issue,
    reading,
    message_text,
):
    """Save the proactive message so Person 4's frontend can display it."""
    now = datetime.now(timezone.utc)
    notification_document = {
        "employee_id": employee,
        "device_model": device,
        "alert_id": alert_data.get("_id"),
        "alert_type": alert_data.get("alert_type"),
        "issue": issue,
        "reading": reading,
        "message": message_text,
        "status": "UNREAD",
        "created_at": now,
        "source": "Proactive Alert Listener",
    }
    notification_result = notifications_collection.insert_one(notification_document)

    alerts_collection.update_one(
        {"_id": alert_data.get("_id")},
        {
            "$set": {
                "status": "PROCESSED",
                "ai_message": message_text,
                "notification_id": notification_result.inserted_id,
                "processed_at": now,
            }
        },
    )

    return notification_result.inserted_id


def listen_for_alerts():
    print("Starting MongoDB Change Stream Listener with AI Brain...")

    ai_client = genai.Client()

    db_client = MongoClient(MONGODB_URI)
    db = db_client["it_helpdesk_db"]
    alerts_collection = db.System_Alerts
    notifications_collection = db.User_Notifications

    print("Watching for new system alerts 24/7. Press Ctrl+C to stop.")

    try:
        with alerts_collection.watch() as stream:
            for change in stream:
                if change["operationType"] != "insert":
                    continue

                alert_data = change["fullDocument"]
                device = alert_data.get("device_model")
                employee = alert_data.get("employee_id")
                issue = alert_data.get("issue")
                reading = alert_data.get("reading")

                print("\nNEW ALERT DETECTED IN MILLISECONDS!")
                print(f"   Device: {device}")
                print(f"   Employee: {employee}")
                print(f"   Warning: {issue} hit {reading}")
                print("\nWaking up Gemini AI Brain to proactively message user...")

                prompt = f"""
                Act as a friendly, proactive IT Help Desk Agent.
                You just received a critical background system alert for Employee {employee}'s {device} laptop.
                The specific issue is: {issue} is currently at {reading}.

                Write a short, polite, proactive chat message (1-2 sentences maximum) to send to the user.
                Warn them about the issue before their computer crashes, and offer to guide them through a fix.
                Do not sound like a robot; sound like a helpful human IT worker.
                """

                try:
                    response = ai_client.models.generate_content(
                        model=GEMINI_MODEL,
                        contents=prompt,
                    )
                    message_text = (response.text or "").strip()
                except Exception as exc:
                    print(f"Gemini unavailable, using fallback message: {exc}")
                    message_text = build_fallback_message(device, issue, reading)

                if not message_text:
                    message_text = build_fallback_message(device, issue, reading)

                notification_id = save_frontend_notification(
                    alerts_collection=alerts_collection,
                    notifications_collection=notifications_collection,
                    alert_data=alert_data,
                    employee=employee,
                    device=device,
                    issue=issue,
                    reading=reading,
                    message_text=message_text,
                )

                print("\nAI GENERATED MESSAGE TO USER:")
                print(f"   \"{message_text}\"")
                print(f"   Saved frontend notification _id: {notification_id}")
                print("-" * 60)

    except KeyboardInterrupt:
        print("\nStopping listener.")
    finally:
        db_client.close()


if __name__ == "__main__":
    listen_for_alerts()

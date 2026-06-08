import os
import time
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv


# Load your existing MongoDB connection string
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    raise RuntimeError("Missing required environment variable: MONGODB_URI")

def trigger_mock_alert():
    print("Starting Mock Telemetry Utility...")
    
    # Connect to your Atlas cluster
    client = MongoClient(MONGODB_URI)
    db = client["it_helpdesk_db"]
    
    # We will send the alert to a new collection specifically for telemetry alerts
    alerts_collection = db.System_Alerts 
    
    # Build the mock error document exactly as outlined in the hackathon plan
    mock_error_document = {
        "employee_id": "E999",
        "device_model": "Dell XPS 15",
        "alert_type": "CRITICAL_WARNING",
        "issue": "storage_capacity",
        "reading": "96%",
        "status": "UNREAD",
        "timestamp": datetime.now()
    }
    
    print("Scanning system vitals...")
    time.sleep(2)  # Pausing for 2 seconds for dramatic effect during your demo
    
    print(f"⚠️  ALERT: Storage capacity at {mock_error_document['reading']}!")
    print("📡 Transmitting error document to MongoDB Atlas...")
    
    # Insert the document into the database
    result = alerts_collection.insert_one(mock_error_document)
    
    print(f"✅ Success! Mock alert injected into database with _id: {result.inserted_id}")
    client.close()

if __name__ == "__main__":
    trigger_mock_alert()
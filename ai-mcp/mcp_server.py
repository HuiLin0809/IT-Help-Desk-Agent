import os
from datetime import datetime
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pymongo import MongoClient

load_dotenv()

# Define the FastMCP instance globally
mcp = FastMCP("IT Help Desk Agent Server")

MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise RuntimeError("Missing required environment variable: MONGODB_URI")

# Setup database connections
client = MongoClient(MONGODB_URI)
db = client["it_helpdesk_db"]

@mcp.tool()
def get_device_health(employee_id: str) -> str:
    """Retrieves the device diagnostics, hardware specifications, and alert records for an employee from MongoDB Atlas."""
    try:
        # Pointing to the correct collection from your database screenshot
        devices_col = db.System_Alerts 
        
        # Case-insensitive query to catch both 'u123' and 'U123'
        search_id = employee_id.strip()
        device = devices_col.find_one({
            "$or": [
                {"employee_id": search_id.upper()},
                {"employee_id": search_id.lower()}
            ]
        })
        
        if not device:
            return f"No registered computer infrastructure records found for Employee ID: {employee_id}"
            
        # Extracted keys updated to match your exact MongoDB document layout
        return (
            f"=== DEVICE INFORMATION FOR {employee_id.upper()} ===\n"
            f"Device Model: {device.get('device_model', 'N/A')}\n"
            f"Alert Type: {device.get('alert_type', 'N/A')}\n"
            f"Reported Issue: {device.get('issue', 'N/A')}\n"
            f"Sensor Reading: {device.get('reading', 'N/A')}\n"
            f"Alert Status: {device.get('status', 'N/A')}\n"
            f"Timestamp Logged: {device.get('timestamp', 'N/A')}\n"
        )
    except Exception as e:
        return f"Database connectivity error during check: {str(e)}"

@mcp.tool()
def escalate_hardware_ticket(employee_id: str, device_model: str, ai_diagnostic_summary: str) -> str:
    """Physically writes a new Level-2 hardware support ticket into the system database for human intervention."""
    try:
        tickets_col = db.Tickets
        new_ticket = {
            "employee_id": employee_id.upper().strip(),
            "device_model": device_model,
            "summary": ai_diagnostic_summary,
            "status": "ESCALATED",
            "tier": "Level-2 Human Tech",
            "created_at": datetime.now()
        }
        result = tickets_col.insert_one(new_ticket)
        return f"SUCCESS: High-priority hardware support ticket filed. Reference Ticket ID: {result.inserted_id}"
    except Exception as e:
        return f"Failed to log support ticket to database: {str(e)}"

if __name__ == "__main__":
    # Natively host the tool pipeline over network protocol streams on port 8000
    print("Launching FastMCP Engine Service over SSE Network Channels on port 8000...")
    mcp.run(transport='sse')
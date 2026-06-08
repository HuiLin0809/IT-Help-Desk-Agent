"""
IT Help Desk MCP Server

This server exposes MongoDB-backed tools for an AI IT Help Desk Agent.

Requirements:
    pip install "mcp[cli]" pymongo python-dotenv

Environment:
    MONGODB_URI="mongodb+srv://<user>:<password>@<cluster-url>/?retryWrites=true&w=majority"

Run:
    python it_helpdesk_mcp_server.py

Typical MCP client/router configuration:
    {
      "mcpServers": {
        "it-helpdesk-hands": {
          "command": "python",
          "args": ["/absolute/path/to/it_helpdesk_mcp_server.py"],
          "env": {
            "MONGODB_URI": "mongodb+srv://..."
          }
        }
      }
    }
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

from bson import json_util
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError
from pymongo.server_api import ServerApi


DATABASE_NAME = "IT_HelpDesk"
USERS_DEVICES_COLLECTION = "Users_Devices"
MAINTENANCE_LOGS_COLLECTION = "Maintenance_Logs"
DEFAULT_DEVICE_QUERY_LIMIT = 10


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("it_helpdesk_mcp")


load_dotenv()

mcp = FastMCP(
    name="it-helpdesk-hands",
    instructions=(
        "Tools for reading employee device health from MongoDB Atlas and "
        "escalating hardware maintenance tickets for human technicians."
    ),
)


def _require_env(name: str) -> str:
    """Return a required environment variable or fail fast with a useful error."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _create_mongo_client() -> MongoClient:
    """
    Create a MongoDB Atlas client.

    server_api=ServerApi("1") pins the driver to MongoDB Stable API v1, which is
    recommended for Atlas-backed applications that need predictable behavior.
    """
    uri = _require_env("MONGODB_URI")
    client: MongoClient = MongoClient(
        uri,
        server_api=ServerApi("1"),
        serverSelectionTimeoutMS=int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "5000")),
        connectTimeoutMS=int(os.getenv("MONGODB_CONNECT_TIMEOUT_MS", "5000")),
        retryWrites=True,
    )

    try:
        client.admin.command("ping")
    except ServerSelectionTimeoutError as exc:
        raise RuntimeError("Could not connect to MongoDB Atlas within the timeout window.") from exc
    except PyMongoError as exc:
        raise RuntimeError("MongoDB Atlas connection check failed.") from exc

    logger.info("Connected to MongoDB Atlas database %s", DATABASE_NAME)
    return client


mongo_client = _create_mongo_client()
db: Database = mongo_client[DATABASE_NAME]
users_devices: Collection = db[USERS_DEVICES_COLLECTION]
maintenance_logs: Collection = db[MAINTENANCE_LOGS_COLLECTION]


def _clean_optional_string(value: str | None, field_name: str) -> str | None:
    """Normalize optional string input from LLM tool calls."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")

    cleaned = value.strip()
    return cleaned or None


def _to_pretty_json(document: Any) -> str:
    """Serialize MongoDB/BSON values, including ObjectId and datetime, as JSON."""
    return json_util.dumps(document, indent=2, ensure_ascii=False)


@mcp.tool()
def get_device_health(employee_id: str | None = None, device_model: str | None = None) -> str:
    """
    Return employee device hardware specifications and historical health timeline.

    Args:
        employee_id: Exact employee identifier to look up.
        device_model: Exact device model to look up.

    Returns:
        A formatted JSON string containing the matching device document. If only
        device_model is supplied and multiple employees use that model, up to 10
        matching documents are returned to avoid accidentally streaming an entire
        collection to the LLM.
    """
    employee_id = _clean_optional_string(employee_id, "employee_id")
    device_model = _clean_optional_string(device_model, "device_model")

    if not employee_id and not device_model:
        return (
            "Error: Provide at least one lookup parameter: employee_id or device_model."
        )

    query: dict[str, str] = {}
    if employee_id:
        query["employee_id"] = employee_id
    if device_model:
        query["device_model"] = device_model

    try:
        if employee_id:
            document = users_devices.find_one(query)
            if document is None:
                return _to_pretty_json(
                    {
                        "found": False,
                        "message": "No device health record matched the supplied criteria.",
                        "query": query,
                    }
                )
            return _to_pretty_json(document)

        documents = list(users_devices.find(query).limit(DEFAULT_DEVICE_QUERY_LIMIT))
        return _to_pretty_json(
            {
                "found": bool(documents),
                "count": len(documents),
                "limit": DEFAULT_DEVICE_QUERY_LIMIT,
                "query": query,
                "documents": documents,
            }
        )
    except PyMongoError as exc:
        logger.exception("MongoDB read failed for query: %s", query)
        return f"Error: MongoDB read failed: {exc}"


@mcp.tool()
def escalate_hardware_ticket(
    employee_id: str,
    device_model: str,
    ai_diagnostic_summary: str,
) -> str:
    """
    Create an escalated hardware maintenance ticket for a human technician.

    Args:
        employee_id: Employee identifier associated with the faulty device.
        device_model: Device model needing human inspection or repair.
        ai_diagnostic_summary: Concise bulleted summary of failed troubleshooting
            steps and observed symptoms. This is stored directly in the ticket so
            technicians do not need to inspect chat logs.

    Returns:
        A success message containing the inserted ticket _id.
    """
    cleaned_employee_id = _clean_optional_string(employee_id, "employee_id")
    cleaned_device_model = _clean_optional_string(device_model, "device_model")
    cleaned_ai_diagnostic_summary = _clean_optional_string(
        ai_diagnostic_summary,
        "ai_diagnostic_summary",
    )

    missing_fields = [
        field_name
        for field_name, value in {
            "employee_id": cleaned_employee_id,
            "device_model": cleaned_device_model,
            "ai_diagnostic_summary": cleaned_ai_diagnostic_summary,
        }.items()
        if not value
    ]
    if missing_fields:
        return f"Error: Missing required field(s): {', '.join(missing_fields)}."

    assert cleaned_employee_id is not None
    assert cleaned_device_model is not None
    assert cleaned_ai_diagnostic_summary is not None

    ticket = {
        "employee_id": cleaned_employee_id,
        "device_model": cleaned_device_model,
        "status": "Escalated",
        "ai_diagnostic_summary": cleaned_ai_diagnostic_summary,
        "created_at": datetime.now(timezone.utc),
        "source": "AI IT Help Desk Agent",
    }

    try:
        result = maintenance_logs.insert_one(ticket)
        ticket_id = str(result.inserted_id)
        logger.info(
            "Created escalated hardware ticket %s for employee_id=%s device_model=%s",
            ticket_id,
            cleaned_employee_id,
            cleaned_device_model,
        )
        return f"Success: Escalated hardware ticket created with _id: {ticket_id}"
    except PyMongoError as exc:
        logger.exception(
            "MongoDB write failed while escalating ticket for employee_id=%s",
            cleaned_employee_id,
        )
        return f"Error: MongoDB write failed: {exc}"


if __name__ == "__main__":
    # Default stdio transport lets a router agent launch this script as a child
    # process and call get_device_health / escalate_hardware_ticket over MCP.
    mcp.run()

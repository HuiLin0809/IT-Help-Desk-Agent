#  AI IT Help Desk Agent

A fully autonomous IT Help Desk assistant powered by Gemini and MongoDB Atlas. This agent uses the **Model Context Protocol (MCP)** to securely bridge the gap between natural language processing and secure database operations.

## What It Does
Instead of making employees fill out long IT support forms, this agent allows them to simply describe their hardware issue in natural language. The AI agent acts as a router that can:
1. **Read:** Look up employee device specifications and health history directly from the database.
2. **Write:** Autonomously escalate hardware failure tickets (extracting the device model, employee ID, and writing a diagnostic summary) directly to human technicians.

## Architecture
* **The Brain:** Google `gemini-1.5-flash` (via the `google-genai` SDK)
* **The Hands:** A custom Python MCP Server exposing local tools.
* **The Memory:** MongoDB Atlas Cloud Database.

## ⚙️ How to Run Locally

### 1. Install Dependencies
Make sure you have Python installed, then run:
`pip install -r requirements.txt`

### 2. Set Up Environment Variables
Create a file named `.env` in the root directory and add your secure keys:
```text
MONGODB_URI="your_mongodb_atlas_connection_string"
GEMINI_API_KEY="your_google_ai_studio_key"
```

## To Run the Frontend
```bash
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process; .\run_all.ps1
```

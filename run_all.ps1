# IT Help Desk Agent - Complete System Automation Launcher

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " BOOTING IT HELP DESK AGENT ARCHITECTURE TIER CLUSTERS  " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# 1. Spin up the Core MCP FastMCP Tools Server on Port 8000
Write-Host "Starting Tools Host Service Tier (Port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\Users\phuah\OneDrive\Desktop\Google\IT-Help-Desk-Agent\ai-mcp; python -m dotenv run python mcp_server.py"

# Pause for 3 seconds to let the network port stabilize completely
Start-Sleep -Seconds 3

# 2. Spin up the Unified Flask API Engine Gateway on Port 5000 (Launches listener & mock script)
Write-Host "Starting Flask API Core Engine Gateway (Port 5000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\Users\phuah\OneDrive\Desktop\Google\IT-Help-Desk-Agent\ai-mcp; python -m dotenv run python app_api.py"

# 3. Spin up the Frontend User Interface Server on Port 8080
Write-Host "Launching Client Frontend Interface UI Dashboard (Port 8080)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\Users\phuah\OneDrive\Desktop\Google\IT-Help-Desk-Agent\frontend; python -m http.server 8080"

Write-Host "========================================================" -ForegroundColor Green
Write-Host "ALL SYSTEMS OPERATIONAL. DEMO ECOSYSTEM READY." -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
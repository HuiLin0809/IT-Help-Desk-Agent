document.addEventListener("DOMContentLoaded", () => {
    
    // =====================================================================
    // CORE CONNECTIONS & APPLICATION API CONFIGURATIONS
    // =====================================================================
    // Point both completely to your live FastAPI backend on port 8000
const FASTAPI_BASE_URL = "http://127.0.0.1:8000";
const FASTAPI_ALERT_URL = `${FASTAPI_BASE_URL}/mock-alert`;
const FASTAPI_CHAT_URL = `${FASTAPI_BASE_URL}/chat`; // Cleaned up syntax
    
    const currentEmployeeId = "E1402";
    const currentDeviceModel = "Dell XPS 15";
    let ticketCounter = 9082;

    // View Switcher Elements
    const btnUserView = document.getElementById("btn-user-view");
    
    const btnTechView = document.getElementById("btn-tech-view");
    const panelUserView = document.getElementById("panel-user-view");
    const panelTechView = document.getElementById("panel-tech-view");

    // Chat Form Elements
    const chatForm = document.getElementById("chat-input-form");
    const userInputField = document.getElementById("chat-user-field");
    const chatMessagesBox = document.getElementById("chat-messages-box");

    // Telemetry DOM Elements
    const txtTemp = document.getElementById("txt-temp");
    const barTemp = document.getElementById("bar-temp");
    const txtDisk = document.getElementById("txt-disk");
    const barDisk = document.getElementById("bar-disk");
    const txtFan = document.getElementById("txt-fan");
    const barFan = document.getElementById("bar-fan");

    // Simulation Trigger Elements
    const simAlertBtn = document.getElementById("sim-trigger-alert");
    const simHeatBtn = document.getElementById("sim-trigger-heat");
    const techTicketsTbody = document.getElementById("tech-tickets-tbody");
    const toastContainer = document.getElementById("alert-toast-container");

    // View Navigation Control
    btnUserView.addEventListener("click", () => {
        btnUserView.classList.add("active");
        btnTechView.classList.remove("active");
        panelUserView.classList.add("active");
        panelTechView.classList.remove("active");
    });

    btnTechView.addEventListener("click", () => {
        btnTechView.classList.add("active");
        btnUserView.classList.remove("active");
        panelTechView.classList.add("active");
        panelUserView.classList.remove("active");
    });

    // Helper: Render Chat Bubbles to Terminal Display
    const appendMessage = (sender, text, isSystem = false) => {
        const msgDiv = document.createElement("div");
        msgDiv.classList.add("message", isSystem ? "system-msg" : "user-msg");
        
        msgDiv.innerHTML = `
            <div class="avatar"><i class="fa-solid ${isSystem ? 'fa-robot' : 'fa-user'}"></i></div>
            <div class="message-body">
                <div class="sender-name">${sender}</div>
                <p>${text}</p>
            </div>
        `;
        chatMessagesBox.appendChild(msgDiv);
        chatMessagesBox.scrollTop = chatMessagesBox.scrollHeight;
    };

    // Helper: Update Diagnostics Sidebar Parameters UI Components
    const updateTelemetry = (temp, disk, fanSpeed) => {
        txtTemp.innerText = `${temp}°C`;
        barTemp.style.width = `${temp}%`;
        barTemp.className = `bar-fill ${temp > 70 ? 'danger' : temp > 50 ? 'warning' : 'success'}`;

        txtDisk.innerText = `${disk}%`;
        barDisk.style.width = `${disk}%`;
        barDisk.className = `bar-fill ${disk > 90 ? 'danger' : 'success'}`;

        txtFan.innerText = `${fanSpeed} RPM`;
        const fanPercent = Math.min((fanSpeed / 6000) * 100, 100);
        barFan.style.width = `${fanPercent}%`;
        barFan.className = `bar-fill ${fanSpeed > 5000 ? 'danger' : fanSpeed > 3000 ? 'warning' : 'success'}`;
    };

    // Helper: Inject Escalated Level-2 Records into Technician Table Viewport
    const injectTechTicket = (id, emp, asset, summaryHtml) => {
        const newRow = document.createElement("tr");
        newRow.innerHTML = `
            <td><code>TK-${id}</code></td>
            <td><strong>${emp}</strong></td>
            <td>${asset}</td>
            <td><span class="status-pill escalated">Escalated</span></td>
            <td>
                <div class="ai-summary-box">
                    ${summaryHtml}
                </div>
            </td>
            <td>Just now</td>
        `;
        techTicketsTbody.insertBefore(newRow, techTicketsTbody.firstChild);
    };

    // Helper: Spawn Toast Popups representing real-time API Server responses
    const spawnToast = (type, title, message, actionText, onAction) => {
        const toast = document.createElement("div");
        toast.className = `toast ${type === 'warning' ? 'warning-toast' : ''}`;
        toast.innerHTML = `
            <div class="toast-icon" style="color: ${type === 'danger' ? '#FF4646' : '#F1C40F'}">
                <i class="fa-solid ${type === 'danger' ? 'fa-circle-radiation' : 'fa-triangle-exclamation'}"></i>
            </div>
            <div class="toast-body">
                <h5>${title}</h5>
                <p>${message}</p>
                <div class="toast-actions">
                    <button class="toast-btn">${actionText}</button>
                    <button class="toast-btn-alt" onclick="this.parentElement.parentElement.parentElement.remove()">Dismiss</button>
                </div>
            </div>
        `;
        
        toast.querySelector(".toast-btn").addEventListener("click", () => {
            onAction();
            toast.remove();
        });
        
        toastContainer.appendChild(toast);
    };

    // =====================================================================
    // 🌐 REAL BACKEND SERVICE INTEGRATIONS (HTTP FETCH PIPELINES)
    // =====================================================================

    // User Message Processing Handler connected to Flask Orchestrator
    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const inputMessage = userInputField.value.trim();
        if (!inputMessage) return;

        // Render User Query Immediately onto screen layout
        appendMessage(`You (Employee ${currentEmployeeId})`, inputMessage, false);
        userInputField.value = "";

        // Create typing element placeholder node
        const loadingDivId = "loading-ai-msg";
        const loadingDiv = document.createElement("div");
        loadingDiv.classList.add("message", "system-msg");
        loadingDiv.id = loadingDivId;
        loadingDiv.innerHTML = `
            <div class="avatar"><i class="fa-solid fa-spinner fa-spin"></i></div>
            <div class="message-body">
                <div class="sender-name">Enterprise Grounded AI Agent</div>
                <p>Analyzing MongoDB system telemetry parameters and generating diagnostics...</p>
            </div>
        `;
        chatMessagesBox.appendChild(loadingDiv);
        chatMessagesBox.scrollTop = chatMessagesBox.scrollHeight;

        try {
            // Send payload to live Flask app_api.py endpoint on port 5000
            const response = await fetch(FLASK_CHAT_URL, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    message: inputMessage,
                    employee_id: currentEmployeeId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP Error Status: ${response.status}`);
            }

            const data = await response.json();
            
            // Remove typing element spinner
            document.getElementById(loadingDivId).remove();

            if (data.response) {
                // Render true response text parsed by your teammate's Gemini loop
                appendMessage("Enterprise Grounded AI Agent", data.response, true);
                
                // Reactive UI Telemetry Adjustment updates conditionally based on real content
                const cleanResponse = data.response.toLowerCase();
                if (cleanResponse.includes("overheat") || cleanResponse.includes("fan") || cleanResponse.includes("rpm")) {
                    updateTelemetry(74, 96, 5800);
                }
                
                // If the Gemini model called an orchestration escalation tool, display it reactively
                if (cleanResponse.includes("ticket") || cleanResponse.includes("escalat")) {
                    ticketCounter++;
                    injectTechTicket(ticketCounter, currentEmployeeId, currentDeviceModel, `
                        <ul>
                            <li><strong>Source:</strong> Autonomous Conversation Escalation</li>
                            <li><strong>User Prompt:</strong> "${inputMessage}"</li>
                            <li><strong>AI Resolution:</strong> Diagnostics completed via active MCP loop infrastructure. Hardware replacement suggested.</li>
                        </ul>
                    `);
                }
            } else {
                appendMessage("Enterprise Grounded AI Agent", `⚠️ Processing Fault: ${data.error || "Unknown response payload schema."}`, true);
            }

        } catch (error) {
            console.error("Network Fetch Failure:", error);
            document.getElementById(loadingDivId).remove();
            appendMessage("Enterprise Grounded AI Agent", "❌ Communication Error: Unable to establish an API handshake with the backend processing pipeline on Port 5000. Verify the Flask runtime environment is active.", true);
        }
    });

    // EVALUATION SIMULATION 1: Real Proactive Telemetry Post (96% Storage Capacity)
    simAlertBtn.addEventListener("click", async () => {
        try {
            const response = await fetch(FASTAPI_ALERT_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    employee_id: currentEmployeeId,
                    device_model: currentDeviceModel,
                    alert_type: "CRITICAL_WARNING",
                    issue: "storage_capacity",
                    reading: "96%"
                })
            });
            
            const result = await response.json();
            if (result.success || response.ok) {
                updateTelemetry(42, 96, 2400);
                spawnToast("warning", "MongoDB Change Stream Event", "Local system build volume is at 96% capacity, risking runtime crashes.", "Run Cache Clear", () => {
                    appendMessage(`You (Employee ${currentEmployeeId})`, "Executing recommended automated system cache clearance routine.", false);
                    setTimeout(() => {
                        appendMessage("Enterprise Grounded AI Agent", "✅ Cache allocation successfully freed. Storage space drops back to safe levels (45%).", true);
                        updateTelemetry(40, 45, 2100);
                    }, 1200);
                });
            }
        } catch (e) {
            console.error("Alert simulation inject execution failed:", e);
        }
    });

    // EVALUATION SIMULATION 2: Real Proactive Telemetry Post (Fan Bearing Failure)
    simHeatBtn.addEventListener("click", async () => {
        try {
            const response = await fetch(FASTAPI_ALERT_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    employee_id: currentEmployeeId,
                    device_model: currentDeviceModel,
                    alert_type: "CRITICAL_WARNING",
                    issue: "fan_bearing_failure",
                    reading: "5950 RPM"
                })
            });

            if (response.ok) {
                updateTelemetry(88, 45, 5950);
                spawnToast("danger", "Critical Telemetry Breach", "Hardware fan metrics report physical rotor degradation on asset Dell XPS 15.", "Escalate Ticket", () => {
                    ticketCounter++;
                    appendMessage("System Monitor Pipeline", "Critical thermal status locked. Telemetry thresholds bypassed.", false);
                    appendMessage("Enterprise Grounded AI Agent", `Automated alarm captured. Ticket <strong>TK-${ticketCounter}</strong> generated for physical fan replacement. Check Technician Dashboard.`, true);
                    
                    injectTechTicket(ticketCounter, currentEmployeeId, currentDeviceModel, `
                        <ul>
                            <li>Proactive change stream alert: Physical system telemetry breached safe operating parameters (88°C).</li>
                            <li>Rotor bearings operating at critical 5950 RPM loop without dropping temperature indexes.</li>
                            <li>Mechanical fan breakdown diagnosed autonomously via FastAPI alert infrastructure pipeline.</li>
                        </ul>
                    `);
                });
            }
        } catch (e) {
            console.error("Heat simulation execution failed:", e);
        }
    });
});
import { useState } from 'react';

export default function App() {
  // Current view toggle: 'user' view or 'tech' dashboard view
  const [currentView, setCurrentView] = useState('user');
  
  // Real-time active notification toast state (Proactive Alert)
  const [activeAlert, setActiveAlert] = useState(null);

  // Chat message history array (Reactive Flow)
  const [messages, setMessages] = useState([
    { id: 1, sender: 'agent', text: 'Hello! I am your autonomous IT Help Desk Agent. How can I assist you with your device today?' }
  ]);
  const [userInput, setUserInput] = useState('');
  const [isAgentTyping, setIsAgentTyping] = useState(false);

  // Mock Database for the Technician Dashboard (Escalated Tickets)
  const [escalatedTickets, setEscalatedTickets] = useState([
    {
      id: "TK-9821",
      user: "Ahmad Zaki",
      device: "MacBook Pro 16\" (S/N: 4421-UUM)",
      status: "Escalated",
      time: "10 mins ago",
      aiSummary: [
        "User reported severe thermal throttling during intense compilation tasks.",
        "Software remedies executed: Reset system SMC and rolled back recent system patch.",
        "Telemetry verification: Thermal state remains critical at 98°C with erratic fan RPM signatures.",
        "Diagnostic determination: Highly probable mechanical fan bearing lock. Requires physical hardware replacement."
      ]
    }
  ]);

  // ==========================================
  // HACKATHON DEMO SIMULATOR FUNCTIONS (MOCK BACKEND)
  // ==========================================
  
  // Simulates Sue Ann's Change Stream catching a 96% storage failure
  const simulateProactiveAlert = () => {
    setActiveAlert({
      id: "ALT-04",
      title: "Critical Storage Capacity Warning",
      message: "Your local runtime storage has unexpectedly peaked at 96% capacity. This baseline barrier will disrupt your upcoming programming builds and potentially crash the active system session.",
      actionText: "Execute Autonomous Cache Purge"
    });
  };

  // Simulates user sending an issue and Gemini + MCP pulling logs to reply
  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!userInput.trim()) return;

    const userMsg = { id: Date.now(), sender: 'user', text: userInput };
    setMessages(prev => [...prev, userMsg]);
    const originalInput = userInput;
    setUserInput('');
    setIsAgentTyping(true);

    // Simulate AI thinking and checking MongoDB history collections
    setTimeout(() => {
      setIsAgentTyping(false);
      
      if (originalInput.toLowerCase().includes('fan') || originalInput.toLowerCase().includes('heat')) {
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          sender: 'agent',
          text: "System Profile retrieved via MCP: I see you are operating a MacBook Pro 16\". Historical pattern matching matches a known vector: 4 identical models reported this today after the v14.4 update. I highly recommend performing a rollback of the update. Shall I guide you through this manual override?"
        }]);
      } else {
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          sender: 'agent',
          text: "I have successfully logged this transaction event in the maintenance database. I am pulling device specifications to match this anomaly with historical resolutions. Give me just one moment."
        }]);
      }
    }, 1500);
  };

  // Simulates the user accepting a proactive fix
  const acceptProactiveFix = () => {
    alert("Executing background script via MCP Server... System cache successfully wiped! Storage lowered safely to 64%.");
    setActiveAlert(null);
  };

  // Simulates an escalation push to the Technician Dashboard
  const forceManualEscalation = () => {
    const newEscalation = {
      id: `TK-${Math.floor(1000 + Math.random() * 9000)}`,
      user: "Current Active User",
      device: "Developer System Workstation",
      status: "Escalated",
      time: "Just now",
      aiSummary: [
        "User initiated manual troubleshooting via interactive console window.",
        "Automated software recovery loops terminated with non-zero exit codes.",
        "System telemetry displays unresolvable core infrastructure exceptions.",
        "Escalated automatically to Tier-2 engineering pool with full state parameters attached."
      ]
    };
    setEscalatedTickets([newEscalation, ...escalatedTickets]);
    alert("Reactive failure simulated! Ticket successfully set to 'Escalated' and pushed into the Technician Feed.");
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 font-sans flex flex-col">
      
      {/* HACKATHON DEMO CONTROL CONTROLLER PANEL (HIDDEN BACKEND MOCK ENGINE) */}
      <div className="bg-gradient-to-r from-amber-600 to-red-600 p-3 text-center text-xs font-bold tracking-wider flex justify-center items-center gap-6 shadow-md border-b border-amber-500">
        <span>⚙️ HACKATHON DEMO JURY PANEL (SIMULATE SUE ANN & NADHIRAH'S BACKEND):</span>
        <button 
          onClick={simulateProactiveAlert}
          className="bg-white text-slate-900 px-3 py-1 rounded-md hover:bg-slate-100 transition dynamic-shadow"
        >
          💥 Trigger Proactive Change Stream Alert (96% Storage)
        </button>
        <button 
          onClick={forceManualEscalation}
          className="bg-slate-900 text-white px-3 py-1 rounded-md border border-slate-700 hover:bg-slate-800 transition"
        >
          🚨 Simulate Automated Lvl-2 Ticket Escalation
        </button>
      </div>

      {/* SYSTEM HEADER NAVIGATION */}
      <header className="bg-slate-950 border-b border-slate-800 px-6 py-4 flex justify-between items-center shadow-lg">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 bg-emerald-500 rounded-full animate-ping"></div>
          <h1 className="text-lg font-extrabold tracking-tight text-white">
            IT HELP DESK <span className="text-emerald-400">AUTONOMOUS AGENT</span>
          </h1>
        </div>
        <div className="bg-slate-900 p-1 rounded-lg border border-slate-800 flex gap-1">
          <button 
            onClick={() => setCurrentView('user')}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition ${currentView === 'user' ? 'bg-emerald-500 text-slate-950 font-bold' : 'text-slate-400 hover:text-white'}`}
          >
            👤 User Portal View
          </button>
          <button 
            onClick={() => setCurrentView('tech')}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition ${currentView === 'tech' ? 'bg-emerald-500 text-slate-950 font-bold' : 'text-slate-400 hover:text-white'}`}
          >
            🛠️ Tech Dashboard ({escalatedTickets.length})
          </button>
        </div>
      </header>

      {/* PROACTIVE SYSTEM TOAST WARNING NOTIFICATION ALERT */}
      {activeAlert && (
        <div className="bg-slate-950 border-l-4 border-amber-500 m-6 p-5 rounded-r-xl shadow-2xl animate-bounce flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border border-slate-800">
          <div className="flex-1">
            <div className="flex items-center gap-2 text-amber-400 font-bold tracking-wide text-sm mb-1">
              <span className="text-lg">⚠️</span> {activeAlert.title.toUpperCase()} [DETECTED VIA CHANGE STREAMS]
            </div>
            <p className="text-slate-300 text-sm leading-relaxed">{activeAlert.message}</p>
          </div>
          <div className="flex gap-2 shrink-0">
            <button 
              onClick={acceptProactiveFix}
              className="bg-amber-500 text-slate-950 px-4 py-2 rounded-lg font-bold text-xs uppercase tracking-wider hover:bg-amber-400 transition"
            >
              {activeAlert.actionText}
            </button>
            <button 
              onClick={() => setActiveAlert(null)}
              className="text-slate-400 hover:text-white px-3 py-2 text-xs"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* CORE DISPLAY WINDOW FRAMES */}
      <main className="flex-1 p-6 max-w-7xl w-full mx-auto flex flex-col justify-stretch">
        
        {/* ==========================================
            PERSPECTIVE A: USER APPS & REACTION CHAT SCREEN
           ========================================== */}
        {currentView === 'user' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 items-stretch">
            
            {/* LEFT PROFILE PANELS: SIMULATED HARDWARE ATTRIBUTES MONITORED BY ATLAS */}
            <div className="bg-slate-950 rounded-xl p-5 border border-slate-800 flex flex-col gap-6 shadow-sm">
              <div>
                <h3 className="text-xs font-bold tracking-widest text-slate-400 uppercase mb-3">Assigned Workspace Asset</h3>
                <div className="bg-slate-900 p-4 rounded-lg border border-slate-800">
                  <div className="text-white font-bold text-sm">MacBook Pro 16-inch</div>
                  <div className="text-xs text-slate-500 font-mono mt-0.5">S/N: 4421-UUM (Group 4 Core Node)</div>
                  <div className="mt-3 flex gap-2">
                    <span className="px-2 py-0.5 bg-emerald-950 text-emerald-400 border border-emerald-800 rounded text-[10px] font-mono">MongoDB Hooked</span>
                    <span className="px-2 py-0.5 bg-slate-800 text-slate-300 rounded text-[10px] font-mono">Agent Active</span>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-xs font-bold tracking-widest text-slate-400 uppercase mb-3">Live Telemetry Diagnostics</h3>
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">CPU Thermal Core Status</span>
                      <span className="text-emerald-400 font-mono">42°C (Optimal)</span>
                    </div>
                    <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden border border-slate-800">
                      <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: '42%' }}></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">Internal Solid State Storage</span>
                      <span className={`${activeAlert ? 'text-amber-400 animate-pulse' : 'text-slate-300'} font-mono`}>{activeAlert ? '96%' : '58%'}</span>
                    </div>
                    <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden border border-slate-800">
                      <div className={`h-1.5 rounded-full transition-all duration-500 ${activeAlert ? 'bg-amber-500' : 'bg-indigo-500'}`} style={{ width: activeAlert ? '96%' : '58%' }}></div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-auto p-4 bg-slate-900/50 rounded-lg border border-dashed border-slate-800 text-xs text-slate-400 leading-relaxed">
                💡 <span className="text-slate-200 font-semibold">Hackathon Hint for Judges:</span> Type <span className="text-emerald-400 font-mono">"My laptop fan is overheating"</span> into the chat prompt to trigger the agent's reactive lookup capability!
              </div>
            </div>

            {/* MIDDLE/RIGHT CHAT INTERACTION ENGINE */}
            <div className="bg-slate-950 rounded-xl border border-slate-800 flex flex-col lg:col-span-2 overflow-hidden shadow-2xl min-h-[500px]">
              <div className="bg-slate-900/80 px-4 py-3 border-b border-slate-800 flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-emerald-400 rounded-full"></div>
                  <span className="text-sm font-semibold text-slate-200">Autonomous Core Processing Stream</span>
                </div>
                <span className="text-[10px] font-mono bg-slate-800 text-slate-400 px-2 py-0.5 rounded">MCP v1.0.0 Connected</span>
              </div>

              {/* MESSAGES TIMELINE ARRAY */}
              <div className="flex-1 p-4 overflow-y-auto space-y-4 text-sm max-h-[400px]">
                {messages.map((msg) => (
                  <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[85%] p-3 rounded-xl leading-relaxed ${msg.sender === 'user' ? 'bg-emerald-500 text-slate-950 font-medium rounded-tr-none' : 'bg-slate-900 text-slate-200 border border-slate-800 rounded-tl-none'}`}>
                      <div className="text-[10px] font-bold opacity-60 uppercase mb-1 tracking-wider">
                        {msg.sender === 'user' ? 'Employee Input' : 'Autonomous AI Agent'}
                      </div>
                      <p>{msg.text}</p>
                    </div>
                  </div>
                ))}

                {isAgentTyping && (
                  <div className="flex justify-start">
                    <div className="bg-slate-900 border border-slate-800 text-slate-400 px-4 py-3 rounded-xl rounded-tl-none flex items-center gap-2">
                      <span className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce"></span>
                      <span className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce [animation-delay:0.2s]"></span>
                      <span className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce [animation-delay:0.4s]"></span>
                      <span className="text-xs font-mono italic">Querying device documentation via Atlas indexes...</span>
                    </div>
                  </div>
                )}
              </div>

              {/* INPUT BOX FORM */}
              <form onSubmit={handleSendMessage} className="p-3 bg-slate-900/60 border-t border-slate-800 flex gap-2">
                <input 
                  type="text"
                  value={userInput}
                  onChange={(e) => setUserInput(e.target.value)}
                  placeholder="Ask a question or explain an issue..."
                  className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 font-medium"
                />
                <button 
                  type="submit"
                  className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-5 py-2 rounded-lg font-bold text-sm tracking-wide transition shrink-0"
                >
                  Send
                </button>
              </form>

            </div>
          </div>
        )}

        {/* ==========================================
            PERSPECTIVE B: LEVEL-2 ESCALATION TECHNICIAN DASHBOARD
           ========================================== */}
        {currentView === 'tech' && (
          <div className="space-y-6 flex-1">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-xl font-black text-white tracking-tight">LEVEL-2 ESCALATED DISPATCH CONSOLE</h2>
                <p className="text-xs text-slate-400 mt-1">This console displays hardware alerts compiled directly into database schemas after software automation boundaries are reached.</p>
              </div>
              <span className="px-3 py-1 bg-red-950/50 border border-red-900 text-red-400 text-xs font-mono font-bold rounded-full">
                🚨 {escalatedTickets.length} Emergency Priority Actions Required
              </span>
            </div>

            {/* LIVE DATA GRID CARDS */}
            <div className="grid grid-cols-1 gap-4">
              {escalatedTickets.map((ticket) => (
                <div key={ticket.id} className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
                  
                  {/* TICKET TOP METADATA BAR */}
                  <div className="bg-slate-900/80 border-b border-slate-800 p-4 flex flex-wrap justify-between items-center gap-3">
                    <div className="flex items-center gap-3">
                      <span className="px-2.5 py-1 bg-red-500 text-slate-950 text-xs font-black rounded-md tracking-wider">{ticket.id}</span>
                      <div>
                        <span className="text-sm font-bold text-white">{ticket.user}</span>
                        <span className="text-slate-500 text-xs ml-2 font-mono">({ticket.device})</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 text-xs">
                      <span className="text-slate-400 font-mono">{ticket.time}</span>
                      <span className="px-2.5 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800 font-semibold text-[11px]">Pending Physical Repair</span>
                    </div>
                  </div>

                  {/* HIGH VALUE PROPOSITION: AI CONDENSED CONCISE BULLETED SUMMARIES */}
                  <div className="p-5 bg-gradient-to-br from-slate-950 to-slate-900/40">
                    <div className="flex gap-2 items-center text-emerald-400 text-xs font-bold uppercase tracking-wider mb-3">
                      <span>🤖</span> GENEPATIVE AI COMPREHENSIVE BRIEFING DIRECT READ OUT [MAPPED TO DB LOG]
                    </div>
                    
                    <ul className="space-y-2.5">
                      {ticket.aiSummary.map((bullet, idx) => (
                        <li key={idx} className="flex items-start gap-3 text-sm text-slate-300 leading-relaxed">
                          <span className="text-emerald-500 select-none mt-1 text-xs">✔</span>
                          <span>{bullet}</span>
                        </li>
                      ))}
                    </ul>

                    {/* ACTION TRIGGERS */}
                    <div className="mt-5 pt-4 border-t border-slate-900 flex justify-end gap-2">
                      <button 
                        onClick={() => alert(`Reviewing diagnostics for ${ticket.id}...`)}
                        className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs rounded-lg uppercase tracking-wider transition"
                      >
                        Inspect Device Profile History
                      </button>
                      <button 
                        onClick={() => alert(`Ticket ${ticket.id} closed.`)}
                        className="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs rounded-lg uppercase tracking-wider transition"
                      >
                        Mark Hardware Swapped & Resolved
                      </button>
                    </div>

                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

      </main>

      {/* STABLE APPLICATION FOOTER BRANDING */}
      <footer className="bg-slate-950 border-t border-slate-950 py-3 text-center text-xs text-slate-600 font-mono mt-auto">
        UUM Hackathon Initiative • Group 4 Execution Ecosystem © 2026
      </footer>

    </div>
  );
}
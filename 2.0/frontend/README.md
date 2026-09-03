# KernelSense — Frontend

React + Vite frontend for the KernelSense AI-Powered Linux Operations Assistant.

---

## Quick Start

```bash
cd frontend
npm install
npm run dev
```

The app starts at `http://localhost:5173` in **mock mode** by default.

---

## Environment Variables

Copy the template:

```bash
cp .env.example .env
```

| Variable            | Default                    | Description                         |
|---------------------|----------------------------|-------------------------------------|
| `VITE_API_BASE_URL` | `http://127.0.0.1:8000`    | FastAPI backend URL                 |
| `VITE_USE_MOCK_API` | `true`                     | `true` = use mock data, no backend  |

### Mock Mode (default)

```env
VITE_USE_MOCK_API=true
```

The entire app is demonstrable without the backend running.

### Real Backend Mode

```env
VITE_USE_MOCK_API=false
VITE_API_BASE_URL=http://127.0.0.1:8000
```

---

## Project Structure

```
src/
  api/           # API service layer (NEVER import axios in components)
    client.js        # Axios instance + mock toggle
    assistantApi.js  # POST /ask, approve/reject commands, history
    systemApi.js     # GET /system/cpu|memory|storage|network|health
    processApi.js    # GET /processes
    storageApi.js    # GET /system/storage
    networkApi.js    # GET /system/network
    logsApi.js       # GET /logs
    historyApi.js    # GET /history

  mock/          # Mock data (used when VITE_USE_MOCK_API=true)
    mockAssistant.js
    mockSystem.js
    mockProcesses.js
    mockStorage.js
    mockNetwork.js
    mockLogs.js

  components/    # Reusable UI components
    StatusCard.jsx       # Generic metric card
    CommandApproval.jsx  # Command approval with risk indicator
    ToolProgress.jsx     # AI tool execution steps
    RootCauseTree.jsx    # Root cause chain visualization
    Timeline.jsx         # Event timeline

  pages/         # One component per route
    Dashboard.jsx
    Assistant.jsx
    SystemHealth.jsx
    Processes.jsx
    Storage.jsx
    Network.jsx
    Logs.jsx
    History.jsx
    Settings.jsx

  layouts/       # MainLayout with sidebar + header
  hooks/         # Custom React hooks (useAssistant, useSystemStats, …)
  styles/        # global.css + variables.css (design tokens)
```

---

## API Contracts

### POST /ask

```json
// Request
{ "query": "Why is my laptop slow?" }

// Response
{
  "request_id": "abc123",
  "intent": "SYSTEM_DIAGNOSIS",
  "response": "Your memory usage is high...",
  "tools_used": ["memory", "process"],
  "recommendations": ["Close Chrome tabs"],
  "commands": [
    {
      "id": "cmd-001",
      "command": "sudo systemctl restart NetworkManager",
      "risk_level": "MEDIUM",
      "explanation": "Restarts the network service."
    }
  ],
  "risk_level": "LOW",
  "root_cause": {
    "nodes": [{"id": "chrome", "label": "Chrome", "type": "process"}],
    "edges": [{"from": "chrome", "to": "mem"}]
  },
  "execution_steps": [
    {"tool": "cpu_check", "label": "CPU checked", "status": "done"}
  ]
}
```

### GET /system/cpu|memory|storage|network|health

All responses are normalised inside the API service layer. Components receive consistent shapes regardless of backend implementation changes.

---

## Integration with Member 1 (AI Layer)

When Member 1's AI is ready:

1. Set `VITE_USE_MOCK_API=false`
2. Verify response shape matches the contract in `assistantApi.js`
3. If field names differ, update only the `normaliseAssistantResponse()` function
4. React components remain unchanged

---

## Integration with Member 2 (Linux Backend)

When Member 2's FastAPI backend is ready:

1. Set `VITE_USE_MOCK_API=false` and `VITE_API_BASE_URL=http://127.0.0.1:8000`
2. Verify endpoint paths match what's defined in each `*Api.js` file
3. If paths differ, update only the API service files — never the components
4. If response shapes differ, update only the `normalise*()` functions

---

## Pages

| Route         | Page           | Description                                     |
|---------------|----------------|-------------------------------------------------|
| `/`           | Dashboard      | System overview, health score, charts, timeline |
| `/assistant`  | AI Assistant   | Chat, command approval, root cause viz          |
| `/health`     | System Health  | Per-category health scores                      |
| `/processes`  | Processes      | Sortable process table                          |
| `/storage`    | Storage        | Donut chart, largest dirs, recommendations      |
| `/network`    | Network        | Interface status, internet check, diagnose      |
| `/logs`       | Logs           | Filterable log viewer with AI analyze button    |
| `/history`    | History        | Query/command history with detail panel         |
| `/settings`   | Settings       | Connection config, integration status           |

---

## Architecture

```
React Components
      ↓
  Custom Hooks (useAssistant, useSystemStats, …)
      ↓
  API Service Layer (src/api/*.js)
      ↓  ↑ mock when VITE_USE_MOCK_API=true
  Axios (HTTP)
      ↓
  FastAPI Backend (Member 2)
      ↓
  AI Layer (Member 1) + Linux Tools
```

---

## Next Steps (for the team)

- **Member 2**: Start FastAPI backend, expose the API contract endpoints
- **Member 1**: Return responses matching the `assistantApi.js` contract
- **Member 3**: Set `VITE_USE_MOCK_API=false`, test with real data, fix any field normalization issues
- **Everyone**: Integrate Electron shell after browser app is stable

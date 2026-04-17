# Quick Reference Card

## GETTING STARTED (30 seconds)

### Option 1: Automated (Easiest)
```bash
# Navigate to project
cd "c:\Users\ankus\Desktop\New folder\hackathon"

# Run startup script
start.bat
```
This will:
- Check Python installation
- Install Flask dependencies
- Start API server (port 5000)
- Open frontend in browser

### Option 2: Manual
```bash
# Install dependencies
pip install flask flask-cors

# Start API server
python api_server.py

# Open in browser
http://localhost:5000/frontend/index.html
```

---

## WHERE TO FIND THINGS

| Component | Location | Port/URL |
|-----------|----------|----------|
| **Frontend** | `frontend/index.html` | `http://localhost:5000/frontend/index.html` |
| **API Server** | `api_server.py` | `http://localhost:5000/api/` |
| **HTML Template** | `frontend/index.html` | Rendered in browser |
| **Styling** | `frontend/index.css` | Auto-loaded |
| **JavaScript Logic** | `frontend/index.js` | Auto-loaded |
| **Health Check** | API | `http://localhost:5000/api/health` |

---

## USING THE FRONTEND

### Main Actions
```
1. Load Page
   └─ All 20 tickets appear in grid
   
2. Process Single Ticket
   └─ Click "Process" button on any ticket card
   └─ Wait for result
   └─ See result in table below

3. Process All Tickets
   └─ Click "Process All Tickets" button
   └─ Watch progress modal
   └─ See summary statistics
   └─ Results populate table

4. View Statistics
   └─ Scroll to Analytics section
   └─ See KPI cards (Approved, Denied, Escalated)
   └─ See confidence distribution
   └─ See tool utilization metrics

5. View Audit Log
   └─ Scroll to bottom
   └─ See paginated audit log
   └─ Check timestamps
```

### Search & Filter
```
Search Box:
  - Type ticket ID (e.g., "TKT-001")
  - Type customer email
  - Type issue keyword

Status Filter:
  - "All Tickets" - show everything
  - "Processed" - only show completed
  - "Pending" - only show not processed
```

### Keyboard Shortcuts
```
Ctrl+Shift+P  →  Process all tickets
Ctrl+R        →  Refresh statistics
```

---

## WHAT YOU'LL SEE

### 1. Hero Section
```
┌──────────────────────────────────────────────┐
│  Autonomous Support Agent                 │
│                                              │
│  Intelligent ticket resolution with         │
│  ReAct reasoning, confidence calibration,   │
│  and graceful escalation                    │
│                                              │
│  ✓ Async Processing                         │
│  ✓ Retry Logic                              │
│  ✓ Real-time Analytics                      │
└──────────────────────────────────────────────┘
```

### 2. Tickets Grid
```
┌─────────────────────┐  ┌─────────────────────┐
│ TKT-001             │  │ TKT-002             │
│ Pending             │  │ ✓ Processed         │
│                     │  │                     │
│ Customer:           │  │ Customer:           │
│ john@example.com    │  │ jane@example.com    │
│                     │  │                     │
│ Issue: Product...   │  │ Issue: Order...     │
│                     │  │ Confidence: 85%     │
│ [Process Button]    │  │ [Process Button]    │
└─────────────────────┘  └─────────────────────┘
```

### 3. Results Table
```
┌─────────┬──────────────┬────────────┬───────────┐
│ Ticket  │ Action       │ Confidence │ Tool Calls│
├─────────┼──────────────┼────────────┼───────────┤
│ TKT-001 │ Approve      │ ████████░░ 85%    │ 5     │
│ TKT-002 │ Deny         │ ██████░░░░ 60%    │ 4     │
│ TKT-003 │ Escalate     │ ████░░░░░░ 40%    │ 3     │
└─────────┴──────────────┴────────────┴───────────┘
```

### 4. Statistics Cards
```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ Total: 20   │ Approved: 7 │ Denied: 5   │ Escalated: 8│
│             │             │             │             │
│ ▓▓▓▓▓░░░░░░ │ ▓▓▓▓░░░░░░░ │ ▓▓▓░░░░░░░░ │ ▓▓▓▓░░░░░░ │
└─────────────┴─────────────┴─────────────┴─────────────┘

Confidence:
├─ Average: 0.65 ▓▓▓▓▓▓░░░░ 65%
├─ High (>0.90): 3 tickets
└─ Low (<0.70): 15 tickets

Tools:
├─ Total calls: 125
└─ Average/ticket: 6.3
```

---

## 🔌 API EXAMPLES

### Get All Tickets
```bash
curl http://localhost:5000/api/tickets

# Response:
{
  "success": true,
  "data": {
    "tickets": [...],
    "total": 20
  }
}
```

### Process Single Ticket
```bash
curl -X POST http://localhost:5000/api/process/ticket \
  -H "Content-Type: application/json" \
  -d '{"ticket_id": "TKT-001"}'

# Response:
{
  "success": true,
  "data": {
    "ticket_id": "TKT-001",
    "action": "approve_refund",
    "confidence": 0.85,
    "reasoning": "...",
    "tool_calls": 5
  }
}
```

### Get Statistics
```bash
curl http://localhost:5000/api/stats

# Response:
{
  "success": true,
  "data": {
    "total_processed": 20,
    "by_action": {
      "approve_refund": 7,
      "deny": 5,
      "escalate": 8
    },
    "confidence": {
      "average": 0.65,
      "min": 0.0,
      "max": 0.95,
      "high_count": 3,
      "low_count": 15
    },
    "tool_calls": {
      "total": 125,
      "average": 6.3
    }
  }
}
```

---

## ⚙️ CONFIGURATION

### API Server Port
**File:** `api_server.py` (last line)
```python
app.run(debug=True, host='0.0.0.0', port=5000)
#                                        ^^^^
# Change port number here if needed
```

### Auto-Refresh Interval
**File:** `frontend/index.js` (top of file)
```javascript
const REFRESH_INTERVAL = 5000;  // milliseconds
// Change to refresh more/less frequently
```

### API Timeout
**File:** `api_server.py` (initialization)
```python
agent = SupportAgent(max_retries=2, tool_timeout=5)
#                                   ^^^^^^^^^^^^
# Tool timeout in seconds
```

---

## 🐛 TROUBLESHOOTING

### "Cannot connect to API"
```
✓ Is api_server.py running?
✓ Is port 5000 free? (lsof -i :5000)
✓ Can you access http://localhost:5000/api/health?
```

### "No tickets appearing"
```
✓ Check browser console (F12) for errors
✓ Verify data/tickets.json exists
✓ Check if loadTickets() is called
```

### "Process button not working"
```
✓ Check Network tab in DevTools (F12)
✓ Look for 404 or 500 errors
✓ Check api_server.log for details
```

### "Statistics showing 0"
```
✓ Process at least one ticket first
✓ Click "Refresh Statistics" button
✓ Wait 5 seconds for auto-refresh
```

---

## COMMON TASKS

### Process All Tickets
```
1. Click "Process All Tickets" button
2. Wait for modal to show progress
3. See summary appear
4. Results auto-populate in table
5. Statistics update automatically
```

### Filter Results
```
1. Use Search box to find by ID/email/issue
2. Use Status dropdown to filter
   - "All Tickets" → Show all
   - "Processed" → Show completed
   - "Pending" → Show unprocessed
```

### Export Data
```
Right-click on Results table → Copy → Paste to Excel
(Full export feature coming in v2)
```

---

## 📱 BROWSER SUPPORT

- Chrome 90+
- Firefox 88+
- Edge 90+
- Safari 14+
- Mobile browsers (responsive design)

---

## NEXT STEPS

1. **Run it**: `start.bat`
2. **Process tickets**: Click "Process All Tickets"
3. **View results**: See them auto-populate
4. **Check analytics**: Scroll down
5. **Explore API**: Visit `/api/stats`

---

## 📞 SUPPORT

- **Documentation**: See `FRONTEND_GUIDE.md`
- **Implementation Details**: See `IMPLEMENTATION_SUMMARY.md`
- **API Logs**: Check `api_server.log`
- **Browser Console**: Press F12

---

**Remember:** If something isn't working, check the browser console (F12) and API logs!

**Happy Testing!**

# Autonomous Support Resolution Agent - Frontend Guide

## Overview

This guide explains how to set up and use the complete frontend-backend system for the Autonomous Support Resolution Agent.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│         Frontend (React-like HTML/CSS/JS)          │
│  - Modern responsive UI with Bootstrap 5            │
│  - Real-time statistics dashboard                   │
│  - Ticket management interface                      │
│  - Audit log viewer                                 │
└────────────────────┬────────────────────────────────┘
                     │
         HTTP REST API (JSON)
                     │
┌────────────────────▼────────────────────────────────┐
│         Flask API Server (Python)                   │
│  - /api/tickets - Ticket management                 │
│  - /api/process/* - Processing endpoints            │
│  - /api/results - Results retrieval                 │
│  - /api/stats - Statistics                          │
│  - /api/audit-log - Audit trail                     │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│    Autonomous Agent (support_agent.py)              │
│  - ReAct reasoning loop                             │
│  - Tool calling with retry logic                    │
│  - Confidence calibration                           │
│  - Concurrent ticket processing                     │
└─────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Install Dependencies

```bash
# Navigate to project root
cd "c:\Users\ankus\Desktop\New folder\hackathon"

# Install required packages
pip install -r requirements.txt
```

### 2. Start the API Server

```bash
# Run the Flask API server
python api_server.py

# The server will start on http://localhost:5000
# API endpoints available at http://localhost:5000/api/
```

### 3. Open the Frontend

In your web browser, navigate to:
```
http://localhost:5000/frontend/index.html
```

Or simply:
```
http://localhost:5000
```

## Frontend Features

### 1. **Ticket Management**
- View all available support tickets
- Search tickets by ID, customer email, or issue
- Filter by processing status (Processed/Pending)
- Process individual tickets with one click
- Real-time status indicators

### 2. **Batch Processing**
- Process all 20 tickets concurrently
- View real-time progress
- See completion statistics
- Track processing time and tool utilization

### 3. **Results Dashboard**
- View results in sortable table
- See action taken (Approve/Deny/Escalate)
- View confidence scores with visual indicators
- Track tool call counts
- Timestamp tracking

### 4. **Analytics & Statistics**
- Total tickets processed
- Breakdown by action type (Approve/Deny/Escalate)
- Confidence calibration metrics
  - Average confidence score
  - High confidence (>90%) count
  - Low confidence (<70%) count
- Tool utilization statistics
  - Total tool calls
  - Average per ticket

### 5. **Audit Log**
- Complete audit trail of all operations
- Paginated view with 50 entries per page
- Timestamps for all events
- Full context for debugging

### 6. **Health Monitoring**
- API connection status indicator
- Real-time health checks
- Automatic reconnection attempts

## API Endpoints

### Tickets Endpoints

**GET** `/api/tickets`
- Fetch all available tickets
- Returns: List of ticket objects with metadata

**GET** `/api/tickets/<ticket_id>`
- Fetch specific ticket details
- Returns: Single ticket object

### Processing Endpoints

**POST** `/api/process/ticket`
- Process a single ticket
- Request: `{ "ticket_id": "TKT-001" }`
- Returns: Processing result with action and confidence

**POST** `/api/process/batch`
- Process multiple tickets concurrently
- Request: `{ "ticket_ids": ["TKT-001", "TKT-002", ...] }`
- Returns: Batch statistics and summary

### Results Endpoints

**GET** `/api/results`
- Fetch all processing results
- Returns: List of result objects

**GET** `/api/results/<ticket_id>`
- Fetch result for specific ticket
- Returns: Single result object

### Statistics Endpoints

**GET** `/api/stats`
- Get real-time statistics
- Returns: Aggregated stats by action and confidence

### Audit Log Endpoints

**GET** `/api/audit-log?page=1&per_page=50`
- Fetch paginated audit logs
- Query params: page (default 1), per_page (default 50)
- Returns: Paginated log entries

### Health Endpoint

**GET** `/api/health`
- Check API server health
- Returns: Health status and metadata

## Frontend Components

### Navigation Bar
- Application title and branding
- Navigation links to main sections
- Health status indicator (green/red)

### Hero Section
- Application overview
- Key features highlight
- Quick action buttons

### Tickets Section
- Searchable ticket grid
- Status filters
- Individual ticket cards with quick actions
- Real-time processing status

### Results Section
- Results table with sorting
- Action type badges
- Confidence visualization
- Tool call counts
- View details button

### Analytics Section
- KPI cards (Total, Approved, Denied, Escalated)
- Confidence distribution chart
- Tool utilization metrics
- Real-time updates

## Usage Examples

### Example 1: Process Single Ticket
```javascript
// Frontend JavaScript
processSingleTicket('TKT-001');

// API Call
POST /api/process/ticket
{
  "ticket_id": "TKT-001"
}
```

### Example 2: Process All Tickets
```javascript
// Frontend JavaScript
processAllTickets();

// API Call
POST /api/process/batch
{
  "ticket_ids": ["TKT-001", "TKT-002", ...]
}
```

### Example 3: View Results
```javascript
// Frontend JavaScript
loadResults();

// API Call
GET /api/results
```

### Example 4: Check Statistics
```javascript
// Frontend JavaScript
updateStats();

// API Call
GET /api/stats
```

## Keyboard Shortcuts

- **Ctrl+Shift+P**: Process all tickets
- **Ctrl+R**: Refresh statistics

## Configuration

### API Server (api_server.py)
```python
# Port configuration
app.run(debug=True, host='0.0.0.0', port=5000)

# CORS settings
CORS(app)  # Enables frontend to access API

# Logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler(), logging.FileHandler('api_server.log')]
)
```

### Frontend (index.js)
```javascript
// API configuration
const API_BASE_URL = 'http://localhost:5000/api';

// Refresh interval (5 seconds)
const REFRESH_INTERVAL = 5000;
```

## Error Handling

The frontend automatically handles:
- Network errors with retry logic
- API failures with user-friendly messages
- Missing results with appropriate empty states
- Health check failures with status indicator

## Performance Optimization

1. **Async Processing**: All API calls are non-blocking
2. **Auto-refresh**: Statistics update every 5 seconds
3. **Lazy Loading**: Tickets load on demand
4. **Pagination**: Audit log is paginated (50 entries per page)
5. **Caching**: Results cached in browser state

## Security Considerations

1. **CORS**: Configured to allow frontend access
2. **Input Validation**: API validates all inputs
3. **Error Messages**: Doesn't expose sensitive information
4. **Logging**: All operations logged for audit trail

## Troubleshooting

### Issue: "Cannot connect to API"
**Solution**: 
- Ensure api_server.py is running
- Check if port 5000 is not blocked by firewall
- Verify API_BASE_URL in index.js

### Issue: "No results displayed"
**Solution**:
- Process at least one ticket first
- Check browser console for errors
- Verify API is returning data: `curl http://localhost:5000/api/results`

### Issue: "Tickets not loading"
**Solution**:
- Check if data/tickets.json exists
- Verify mock_tools.py is correctly configured
- Check api_server.log for errors

### Issue: "Frontend styling looks broken"
**Solution**:
- Clear browser cache
- Refresh page with Ctrl+Shift+R
- Check if Bootstrap CDN is accessible

## Development

### Running in Development Mode
```bash
# With debug logging
python api_server.py

# Logs will be written to api_server.log
```

### Testing API Endpoints
```bash
# Get all tickets
curl http://localhost:5000/api/tickets

# Get stats
curl http://localhost:5000/api/stats

# Check health
curl http://localhost:5000/api/health
```

### Browser Developer Tools
- Open DevTools: F12
- Network tab: Monitor API calls
- Console: Check for JavaScript errors
- Application: View stored data

## Production Deployment

For production use:

1. **Use Production WSGI Server**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 api_server:app
   ```

2. **Enable HTTPS**
   ```python
   # Use nginx/Apache reverse proxy with SSL
   ```

3. **Database**
   ```python
   # Replace in-memory storage with database
   # Use SQLAlchemy for ORM
   ```

4. **Environment Variables**
   ```python
   # Load configuration from environment
   API_PORT = os.getenv('API_PORT', 5000)
   DEBUG = os.getenv('DEBUG', False)
   ```

5. **Logging**
   ```python
   # Use structured logging
   # Send logs to centralized service
   ```

## File Structure

```
hackathon/
├── frontend/
│   ├── index.html          # Main HTML template
│   ├── index.css           # Styling
│   └── index.js            # Frontend logic
├── src/
│   ├── agent/
│   │   └── support_agent.py
│   ├── tools/
│   │   └── mock_tools.py
│   └── utils/
│       └── input_validation.py
├── api_server.py           # Flask API server
├── main.py                 # Batch processing script
└── requirements.txt        # Python dependencies
```

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review API logs: `api_server.log`
3. Check browser console for JavaScript errors
4. Verify all files are in correct locations

---

**Version**: 1.0  
**Last Updated**: April 17, 2026  
**Created for**: Agentic AI Hackathon 2026

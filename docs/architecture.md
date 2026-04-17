# System Architecture

## Overview

The Autonomous Support Resolution Agent is built using a **ReAct (Reasoning + Acting)** pattern combined with concurrent processing to autonomously resolve customer support tickets.

## Component Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                        MAIN ORCHESTRATOR                        │
│                     (main.py - Entry Point)                    │
│  - Loads 20 tickets                                            │
│  - Spawns concurrent agent tasks                              │
│  - Aggregates results                                          │
│  - Generates audit log                                         │
└────────────┬─────────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────────┐
│                    ASYNC TASK MANAGER                          │
│              (asyncio + Semaphore for concurrency)             │
│  - Max 5 concurrent tickets                                   │
│  - Gather all results                                          │
│  - Preserve order in results                                   │
└────────────┬─────────────────────────────────────────────────┘
             │
     ┌───────┴───────┬───────────┬───────────┬───────────┐
     │               │           │           │           │
     ▼               ▼           ▼           ▼           ▼
  TKT-1         TKT-2        TKT-3       TKT-4       TKT-5
  (Task 1)      (Task 2)     (Task 3)    (Task 4)    (Task 5)
     │               │           │           │           │
     └───────┬───────┴───────┬───┴───────┬──┴───────┬──┘
             │               │           │          │
             ▼               ▼           ▼          ▼
        ┌─────────────────────────────────────────────────┐
        │      SUPPORT AGENT (ReAct Loop)                │
        │    (src/agent/support_agent.py)                │
        │                                               │
        │  1. OBSERVATION:                             │
        │     - Parse ticket content                   │
        │     - Extract order ID                       │
        │     - Classify issue type                    │
        │                                               │
        │  2. THOUGHT:                                 │
        │     - Reason about policies                  │
        │     - Determine eligibility                  │
        │     - Check customer tier                    │
        │                                               │
        │  3. ACTION: Tool Calls (3+ chain)           │
        │     - get_customer()                         │
        │     - get_order()                            │
        │     - get_product()                          │
        │     - check_refund_eligibility()             │
        │     - search_knowledge_base()                │
        │     - [Execute Action]                       │
        │                                               │
        │  4. OBSERVATION: Process Results             │
        │     - Analyze tool outputs                   │
        │     - Detect inconsistencies                 │
        │                                               │
        │  5. DECISION:                                │
        │     - Apply business rules                   │
        │     - Generate confidence score              │
        │     - Choose action                          │
        │                                               │
        │  6. EXECUTE:                                 │
        │     - issue_refund() / send_reply()          │
        │     - escalate() / provide_support()         │
        │                                               │
        └──────────┬──────────────────────────────────┘
                   │
                   ▼
        ┌─────────────────────────────────────────────────┐
        │     MOCK TOOLS (Error Simulation)               │
        │    (src/tools/mock_tools.py)                   │
        │                                               │
        │ READ/LOOKUP TOOLS:                            │
        │  - get_customer(email)         [15% timeout]  │
        │  - get_order(order_id)         [10% timeout]  │
        │  - get_product(product_id)     [8% timeout]   │
        │  - search_knowledge_base()     [5% timeout]   │
        │                                               │
        │ DECISION TOOLS:                               │
        │  - check_refund_eligibility()  [20% timeout]  │
        │    (Most complex, highest failure rate)       │
        │                                               │
        │ ACTION TOOLS:                                 │
        │  - issue_refund()              [1% failure]   │
        │  - send_reply()                [1% failure]   │
        │  - escalate()                  [1% failure]   │
        │                                               │
        │ ERROR TYPES:                                  │
        │  - ToolTimeout (retryable)                    │
        │  - ToolMalformedResponse (degradable)         │
        │  - ToolError (logged, graceful)               │
        │                                               │
        └──────────┬──────────────────────────────────┘
                   │
                   ▼
        ┌─────────────────────────────────────────────────┐
        │         DATA LAYER (JSON Files)                │
        │      (data/*.json)                             │
        │                                               │
        │  - customers.json (10 profiles)               │
        │  - orders.json (20 orders)                    │
        │  - products.json (10 products)                │
        │  - tickets.json (20 tickets)                  │
        │  - knowledge-base.md (policies)               │
        │                                               │
        └─────────────────────────────────────────────────┘
```

## Data Flow

### Single Ticket Processing Flow

```
TICKET INPUT
    │
    ├─ TKT-001: "Refund request for headphones - defective"
    │
    ▼
EXTRACT INFORMATION
    ├─ ticket_id: TKT-001
    ├─ customer_email: alice.turner@email.com
    ├─ order_id: ORD-1001 (extracted from body)
    ├─ issue_type: DEFECTIVE (classified from text)
    └─ keywords: [defect, broken, stopped working]
    
    ▼
TOOL CALL 1: get_customer('alice.turner@email.com')
    ├─ Retrieves: VIP tier, 47 orders, $6840.50 lifetime value
    ├─ Decision Impact: VIP gets extended grace period
    └─ Status: SUCCESS
    
    ▼
TOOL CALL 2: get_order('ORD-1001')
    ├─ Retrieves: Delivery date, product ID, total price
    ├─ Calculates: 29 days since delivery
    ├─ Status: SUCCESS (10% timeout chance)
    └─ Decision Impact: Within return window
    
    ▼
TOOL CALL 3: get_product('P001')
    ├─ Retrieves: Category (electronics_accessories), warranty (12 months)
    ├─ Status: SUCCESS (8% timeout chance)
    └─ Decision Impact: 60-day return window applies
    
    ▼
TOOL CALL 4: check_refund_eligibility('ORD-1001')
    ├─ Calculation: 29 days < 60-day window = ELIGIBLE
    ├─ Status: SUCCESS or TIMEOUT (20% chance - most complex)
    ├─ Retry: If timeout, retry up to 2 times with backoff
    └─ Decision Impact: Confirms eligibility
    
    ▼
TOOL CALL 5: search_knowledge_base("electronics accessories warranty return")
    ├─ Retrieves: Policy sections on defective items
    ├─ Status: SUCCESS (5% timeout chance)
    └─ Decision Impact: Confirms policy coverage
    
    ▼
DECISION LOGIC
    ├─ Is item defective? YES (keywords match)
    ├─ Is within warranty? YES (29 days < 60-day window)
    ├─ Is customer tier? VIP (favorable)
    ├─ Any policy violations? NO
    ├─ High-value item? NO ($189.99 < $500)
    ├─ Edge case? NO (clear policy match)
    └─ DECISION: APPROVE_REFUND (confidence: 0.95)
    
    ▼
TOOL CALL 6: issue_refund('ORD-1001', 189.99)  [IRREVERSIBLE]
    ├─ Creates: Refund ID REF-ORD-1001-1710939045
    ├─ Specifies: Original payment method, 5-7 business days
    ├─ Status: SUCCESS (1% failure chance)
    └─ Audit: Logged as irreversible action
    
    ▼
TOOL CALL 7: send_reply('TKT-001', customer_message)
    ├─ Recipient: alice.turner@email.com
    ├─ Content: Refund details, refund ID, ETA
    ├─ Status: SUCCESS (1% failure chance)
    └─ Audit: Delivery confirmation
    
    ▼
RESOLUTION OBJECT
    ├─ ticket_id: TKT-001
    ├─ action: APPROVE_REFUND
    ├─ reasoning: "Item defective, within warranty window"
    ├─ confidence_score: 0.95
    ├─ tool_calls: [7 calls with timestamps and results]
    ├─ customer_message: [Full email body]
    └─ status: RESOLVED
```

## Concurrency Model

### Sequential vs Concurrent Execution

```
SEQUENTIAL (PENALIZED):
TKT-1 ████████ (2 sec)
TKT-2        ████████ (2 sec)
TKT-3               ████████ (2 sec)
...
Total: 40 seconds for 20 tickets

CONCURRENT (REQUIRED):
TKT-1 ████████ (2 sec)
TKT-2 ████████ (2 sec) (parallel)
TKT-3 ████████ (2 sec) (parallel)
TKT-4 ████████ (2 sec) (parallel)
TKT-5 ████████ (2 sec) (parallel)
TKT-6      ████████ (2 sec) (starts after TKT-1 completes)
...
Total: 8 seconds for 20 tickets (with max_concurrent=5)

Speedup: 5x faster
```

### Semaphore Control

```python
async def process_tickets_concurrent(ticket_ids, max_concurrent=5):
    semaphore = asyncio.Semaphore(5)  # Max 5 parallel
    
    async def process_with_semaphore(ticket_id):
        async with semaphore:  # Wait for slot
            return await self.process_ticket(ticket_id)
    
    # Launch all tasks
    tasks = [process_with_semaphore(tid) for tid in ticket_ids]
    
    # Gather all results (waits for all to complete)
    return await asyncio.gather(*tasks)
```

## Error Handling Architecture

### Retry Strategy

```
Tool Call Request
    │
    ├─ Attempt 1
    │  ├─ SUCCESS → Return result
    │  ├─ TIMEOUT → Go to Retry
    │  ├─ MALFORMED → Log and return None
    │  └─ NOT FOUND → Log and return None
    │
    ├─ Retry (if TIMEOUT)
    │  ├─ Wait 0.5 seconds (exponential backoff)
    │  ├─ Attempt 2
    │  │  ├─ SUCCESS → Return result
    │  │  ├─ TIMEOUT → Go to Retry
    │  │  └─ OTHER → Log and return None
    │  │
    │  ├─ Wait 1.0 seconds
    │  ├─ Attempt 3 (final)
    │  │  ├─ SUCCESS → Return result
    │  │  └─ FAIL → Log error
    │  │
    │  └─ Escalate ticket if critical data unavailable
    │
    └─ Continue with partial data or escalate
```

### Failure Impact Levels

```
CRITICAL (Escalate immediately if fail):
├─ get_customer (customer not found)
├─ get_order (order not found)
└─ check_refund_eligibility (decision-critical after 2 retries)

HIGH (Escalate if fail after 2 retries):
├─ get_product (product metadata)
└─ search_knowledge_base (policy lookup)

MEDIUM (Continue with partial data):
├─ Timeout on any tool (retry max 2x)
└─ Malformed response (use fallback)

LOW (Log and continue):
├─ Optional enrichment data
└─ Non-blocking tool failures
```

## State Management

### Audit Log Structure

```python
TicketResolution(
    ticket_id: str,
    action: ResolutionAction,          # APPROVE_REFUND, DENY, ESCALATE, etc.
    reasoning: str,                     # Explanation of decision
    confidence_score: float,            # 0.0 - 1.0
    tool_calls: List[ToolCall],        # Full tool call history
    customer_message: str,              # Message sent to customer
    escalation_case_id: Optional[str],  # Case ID if escalated
    status: str,                        # PENDING, RESOLVED, ESCALATED
    processed_at: datetime              # Timestamp
)

ToolCall(
    name: str,                          # Tool function name
    params: Dict[str, Any],             # Input parameters
    result: Any,                        # Output result
    error: Optional[str],               # Error message if failed
    timestamp: str,                     # When called
    retry_count: int                    # Number of retries
)
```

## Decision Tree

```
TICKET RECEIVED
    │
    ├─ Extract order ID?
    │  └─ NO → ESCALATE ("No order ID found")
    │
    └─ YES → Get Customer → Get Order → Get Product
         │
         ├─ Customer found? NO → ESCALATE
         ├─ Order found? NO → ESCALATE
         └─ Product found? NO → ESCALATE
              │
              └─ Check eligibility & analyze issue
                   │
                   ├─ Damaged on arrival? → APPROVE_REFUND (0.95)
                   ├─ Wrong item? → APPROVE_EXCHANGE (0.95)
                   │
                   ├─ Defective & in warranty? → APPROVE_REPLACEMENT (0.92)
                   ├─ Defective & <7 days? → APPROVE_REFUND (0.90)
                   │
                   ├─ Within return window & unused? → APPROVE_REFUND (0.85)
                   ├─ Within return window & change of mind? → APPROVE_REFUND (0.85)
                   │
                   ├─ VIP/Gold & change of mind & <60 days? → APPROVE_REFUND (0.85)
                   │
                   ├─ Used footwear? → DENY (0.95)
                   ├─ Used sports equipment? → DENY (0.95)
                   ├─ Past window & change of mind & standard? → DENY (0.80)
                   │
                   ├─ High-value (>$500)? → ESCALATE (0.70)
                   ├─ Edge case (near boundary)? → ESCALATE (0.60)
                   ├─ Unclear request? → ESCALATE (0.50)
                   │
                   └─ Default → ESCALATE (0.50)
```

## Integration Points

### Database Integration (Future)
```
Replace JSON files with:
├─ PostgreSQL/MongoDB for customers
├─ Order management system
├─ Product catalog API
└─ Refund/exchange payment processor
```

### LLM Integration (Optional)
```
Add for complex analysis:
├─ GPT-4 for ticket sentiment analysis
├─ Claude for policy interpretation  
└─ Fallback to deterministic logic if LLM unavailable
```

### Notification System (Future)
```
Current: send_reply() to email
Future:
├─ SMS notifications
├─ Push notifications  
├─ Slack/Teams integration
└─ SMS/WhatsApp for urgent escalations
```

### Monitoring (Future)
```
Add observability:
├─ Prometheus metrics (resolution rates, response times)
├─ CloudWatch logs
├─ Datadog APM
└─ Alert thresholds for high escalation rates
```

## Performance Characteristics

### Metrics
- **Throughput**: 20 tickets in ~8 seconds (2.5 tickets/sec)
- **Average ticket time**: 0.4 seconds
- **Tool call overhead**: ~5-10ms per call
- **Concurrency**: 5 parallel streams
- **Memory**: ~50-100 MB (depends on audit log size)
- **Tool reliability**: 85-95% (with retry recovery)

### Bottlenecks
1. check_refund_eligibility (20% timeout rate - most complex)
2. Tool retry delays (exponential backoff)
3. JSON file I/O (load data once at module level)
4. Semaphore contention (at exactly max_concurrent tasks)

### Optimization Opportunities
1. Cache tool results (same customer/order queried multiple times)
2. Batch tool calls (get multiple customers in one call)
3. Pre-load all data structures
4. Use database instead of JSON files
5. Implement decision caching

## Frontend Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   Frontend Web UI                         │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │   HTML       │  │     CSS      │  │  JavaScript  │   │  │
│  │  │              │  │              │  │              │   │  │
│  │  │ - Navigation │  │ - Gradients  │  │ - API calls  │   │  │
│  │  │ - Ticket grid│  │ - Animations │  │ - State mgmt │   │  │
│  │  │ - Results    │  │ - Responsive │  │ - Rendering  │   │  │
│  │  │ - Analytics  │  │ - Dark theme │  │ - Filtering  │   │  │
│  │  │ - Audit log  │  │ - Bootstrap  │  │ - Validation │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  │                         │                                 │  │
│  │                    HTTP/REST API Calls                   │  │
│  │                   (JSON request/response)                │  │
│  └────────────────┬────────────────────────────────────────┘  │
│                   │                                            │
└───────────────────┼──────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Flask REST API Server                       │
│                     (api_server.py)                             │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │          API Route Handlers (Flask)                     │   │
│  │                                                         │   │
│  │  GET  /api/tickets                Get all tickets      │   │
│  │  GET  /api/tickets/<id>           Get specific ticket  │   │
│  │  POST /api/process/ticket         Process 1 ticket     │   │
│  │  POST /api/process/batch          Process multiple     │   │
│  │  GET  /api/results                Get all results      │   │
│  │  GET  /api/results/<id>           Get specific result  │   │
│  │  GET  /api/stats                  Get statistics       │   │
│  │  GET  /api/audit-log              Get audit trail      │   │
│  │  GET  /api/health                 Health check         │   │
│  │                                                         │   │
│  └────────────┬──────────────────────────────────────────┘   │
│               │                                                │
│               ├─ Input Validation                             │
│               ├─ CORS Headers                                 │
│               ├─ Async Processing                             │
│               ├─ Error Handling                               │
│               └─ JSON Serialization                           │
│                   │                                            │
└───────────────────┼──────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│              Backend Agent (Python - main.py)                   │
│         (Existing ReAct loop with all tools)                    │
│                                                                 │
│  - Processes tickets using agent logic                         │
│  - Calls tools with error recovery                             │
│  - Returns structured results                                  │
│  - Maintains audit trail                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Frontend Components

#### HTML Structure (frontend/index.html)
```
index.html (260 lines)
├─ Navigation bar
│  ├─ Logo and branding
│  ├─ Nav links (Tickets, Results, Analytics)
│  └─ Health status badge
├─ Hero section
│  ├─ Title and description
│  └─ Feature badges
├─ Quick action buttons
│  ├─ Load All Tickets
│  ├─ Process All At Once
│  ├─ Process One by One
│  └─ Refresh Statistics
├─ Tickets section
│  ├─ Search and filter controls
│  └─ Ticket grid (responsive cards)
├─ Results section
│  ├─ Results table
│  └─ Sorting and pagination
├─ Analytics section
│  ├─ KPI cards (Total Processed, Success Rate, etc.)
│  ├─ Confidence distribution chart
│  ├─ Tool utilization stats
│  └─ Resolution breakdown pie chart
├─ Audit log section
│  ├─ Audit log viewer
│  └─ Pagination controls
└─ Modals and alerts
   ├─ Loading modal
   ├─ Success alerts
   └─ Error alerts
```

#### CSS Styling (frontend/index.css)
```
index.css (550 lines)
├─ Global styles
│  ├─ CSS variables (colors, spacing)
│  ├─ Dark theme colors
│  └─ Typography
├─ Component styles
│  ├─ Navigation bar
│  ├─ Buttons and badges
│  ├─ Cards and panels
│  ├─ Forms and inputs
│  └─ Modals and alerts
├─ Layout styles
│  ├─ Container and grid
│  ├─ Responsive breakpoints
│  ├─ Flexbox utilities
│  └─ Spacing utilities
├─ Animation styles
│  ├─ Transitions (0.3s cubic-bezier)
│  ├─ Loading spinner
│  ├─ Fade in/out effects
│  └─ Hover effects
├─ Bootstrap 5.3 integration
│  ├─ Grid system customization
│  ├─ Component overrides
│  └─ Utility classes
└─ Dark mode support
   ├─ Color scheme adaptations
   ├─ Gradient adjustments
   └─ Shadow treatments
```

#### JavaScript Logic (frontend/index.js)
```
index.js (550+ lines)
├─ Configuration
│  ├─ API_BASE_URL = 'http://localhost:5000/api'
│  ├─ REFRESH_INTERVAL = 5000 (5 sec)
│  └─ State management object
├─ Initialization
│  ├─ DOMContentLoaded event
│  ├─ Load tickets, results, stats
│  ├─ Setup event listeners
│  ├─ Check health
│  └─ Auto-refresh timer
├─ API Functions
│  ├─ loadTickets() - Fetch all tickets
│  ├─ loadResults() - Fetch processing results
│  ├─ processSingleTicket(id) - Process one ticket
│  ├─ processAllTickets() - Process all concurrently
│  ├─ processOneByOne() - Process sequentially
│  ├─ updateStats() - Fetch statistics
│  └─ checkHealth() - Check API health
├─ UI Functions
│  ├─ renderTickets() - Display ticket grid
│  ├─ renderResults() - Display results table
│  ├─ updateStats() - Update KPI cards
│  ├─ updateAuditLog() - Display audit log
│  └─ filterTickets() - Search and filter
├─ Modal Functions
│  ├─ showLoadingModal(title, message)
│  ├─ hideLoadingModal()
│  ├─ showAlert(message, type)
│  └─ Close alerts on timeout
├─ Utility Functions
│  ├─ formatDate(timestamp)
│  ├─ formatConfidence(score)
│  ├─ escapeHTML(text) - XSS prevention
│  └─ debounce(func, delay)
└─ Event Handlers
   ├─ Button click events
   ├─ Search input events
   ├─ Filter dropdown events
   └─ Pagination events
```

### API Endpoint Architecture

```
REST Endpoints (Flask routes)

GET /api/tickets
├─ Response: { success: true, data: { tickets: [...] } }
├─ Ticket fields: id, customer_id, order_id, subject, body, created_at
└─ Status: 200 OK

GET /api/tickets/<ticket_id>
├─ Response: { success: true, data: { ticket: {...} } }
└─ Status: 200 OK or 404 Not Found

POST /api/process/ticket
├─ Request: { ticket_id: "TKT-001" }
├─ Response: { success: true, data: { action, confidence, tool_calls } }
└─ Status: 200 OK

POST /api/process/batch
├─ Request: { ticket_ids: ["TKT-001", "TKT-002", ...] }
├─ Response: { success: true, data: { total_processed, duration_seconds, results: [...] } }
└─ Status: 200 OK

GET /api/results
├─ Response: { success: true, data: { results: [...] } }
└─ Includes: ticket_id, action, confidence, tool_calls, status

GET /api/stats
├─ Response: { success: true, data: { total_processed, approval_rate, avg_confidence, ... } }
└─ Analytics data for dashboard

GET /api/audit-log
├─ Response: { success: true, data: { log_entries: [...] } }
└─ Complete operation history with pagination

GET /api/health
├─ Response: { status: "healthy", api_version: "1.0", timestamp: "..." }
└─ Status: 200 OK
```

### Frontend-Backend Data Flow

```
User Action (Click "Process All Tickets")
    │
    ▼
JavaScript Event Handler
    │
    ├─ Validate user input
    ├─ Show loading modal
    ├─ Disable buttons
    │
    ▼
REST API Call (POST /api/process/batch)
    │
    ├─ HTTP POST with JSON body
    ├─ { ticket_ids: ["TKT-001", "TKT-002", ...] }
    ├─ Accept: application/json
    └─ CORS headers included
    
    ▼
Flask Server (api_server.py)
    │
    ├─ Parse JSON request
    ├─ Validate ticket_ids
    ├─ Spawn async tasks for each ticket
    │
    ├─ Each task:
    │  ├─ Create agent instance
    │  ├─ Call agent.process_ticket(ticket_id)
    │  ├─ Capture result with full metadata
    │  └─ Store in results dict
    │
    └─ Wait for all tasks to complete
    
    ▼
Response to Frontend (JSON)
    │
    ├─ { success: true, data: { total_processed: 20, duration_seconds: 8.2 } }
    └─ HTTP 200 OK
    
    ▼
JavaScript Handler
    │
    ├─ Hide loading modal
    ├─ Show success alert
    │
    ├─ Call loadResults()
    ├─ Call updateStats()
    └─ Call renderTickets() (show updated status)
    
    ▼
Display Updates
    │
    ├─ Results table updates (shows all resolutions)
    ├─ Ticket grid updates (shows Processed status)
    ├─ Analytics dashboard updates (new KPIs)
    └─ Audit log updates (new entries visible)
```

### Frontend Feature Highlights

```
Real-time Updates:
├─ Auto-refresh every 5 seconds
├─ Manual refresh buttons
└─ WebSocket-ready architecture (future)

Search & Filter:
├─ Client-side filtering
├─ Search by ticket ID or content
├─ Filter by status (Pending/Processed)
└─ Sort results by confidence, timestamp

Responsive Design:
├─ Mobile-first approach
├─ Breakpoints: 576px, 768px, 992px, 1200px
├─ Touch-friendly buttons
└─ Full functionality on all devices

Accessibility:
├─ Semantic HTML5
├─ ARIA labels and roles
├─ Keyboard navigation
├─ High contrast colors (dark theme)

Performance:
├─ Minimal dependencies (no external JS libraries)
├─ Vanilla JavaScript (no jQuery, React, etc.)
├─ CSS-in-single-file (minimal HTTP requests)
├─ Debounced search (reduce API calls)
└─ Pagination for large result sets
```

### State Management

```
Frontend State Object:
{
    tickets: [...],           // Array of ticket objects
    results: {...},           // Map of ticket_id -> result
    stats: {...},             // Statistics data
    auditLog: [...],          // Audit log entries
    isProcessing: false,      // Processing flag
    filters: {
        search: '',           // Search query
        status: ''            // Filter status
    }
}

State Updates:
├─ loadTickets() → updates state.tickets
├─ loadResults() → updates state.results
├─ updateStats() → updates state.stats
├─ processSingleTicket() → updates state.results[id]
└─ filterTickets() → updates state.filters
```

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

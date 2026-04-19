# 🎯 Frontend User Guide - Complete Step-by-Step

## 🚀 Access the Live Application

**Live URL:** https://hackathon2026-ankush-production.up.railway.app/

Open this link in your browser to access the Autonomous Support Resolution Agent Dashboard.

---

## 📋 Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Loading Tickets](#loading-tickets)
4. [Processing Tickets](#processing-tickets)
5. [Understanding Results](#understanding-results)
6. [Viewing Explainable Decisions](#viewing-explainable-decisions)
7. [Batch Processing](#batch-processing)
8. [Statistics & Analytics](#statistics--analytics)
9. [Troubleshooting](#troubleshooting)

---

## 🎬 Getting Started

### **Step 1: Open the Application**
```
Link: https://hackathon2026-ankush-production.up.railway.app/
Browser: Chrome, Firefox, Safari, Edge (any modern browser)
```

### **Step 2: Wait for Page to Load**
- Dashboard initializes
- Tickets automatically load from the server
- Statistics reset to zero (fresh session)
- Ready for processing

### **Step 3: See the Dashboard**
You should see:
- ✅ **Tickets list** on the left
- ✅ **Results table** on the right  
- ✅ **Statistics panel** at the top
- ✅ **Action buttons** for processing

---

## 📊 Dashboard Overview

### **Top Bar - Statistics**
```
┌─────────────────────────────────────────────────────┐
│  Total Processed: 0  │  Average Confidence: 0%     │
│  Approved: 0         │  Denied: 0    │  Escalated: 0 │
└─────────────────────────────────────────────────────┘
```

These update in **real-time** as you process tickets.

**What each means:**
- **Total Processed** - How many tickets processed in this session
- **Average Confidence** - AI confidence level (0-100%)
- **Approved/Denied/Escalated** - Decision breakdown

### **Left Panel - Tickets List**
```
┌──────────────────────┐
│  Load All Tickets    │  ← Click this first
├──────────────────────┤
│ TKT-001              │
│ TKT-002              │
│ TKT-003              │
│ ... (20 tickets)     │
└──────────────────────┘
```

- Shows all available customer tickets
- Click ticket to view details
- Details show in modal/popup

### **Right Panel - Results Table**
```
┌────────────────────────────────────────────────────┐
│ Ticket ID │ Customer │ Action  │ Confidence │ Date │
├────────────────────────────────────────────────────┤
│ (empty until you process tickets)                  │
└────────────────────────────────────────────────────┘
```

- Shows processed ticket results
- Updates as you process tickets
- Click row to see full details

### **Action Buttons**
```
┌──────────────────────┐
│ Process One by One   │  ← Process selected ticket
│ Process All At Once  │  ← Batch process all 20
│ Clear Results        │  ← Clear dashboard
└──────────────────────┘
```

---

## 📥 Loading Tickets

### **How to Load Tickets**

**Step 1:** Click **"Load All Tickets"** button in the left panel

**Step 2:** Wait for tickets to appear (should be instant)

**Step 3:** You'll see a list like:
```
✓ TKT-001 - Grace Lee: Refund Request
✓ TKT-002 - Alex Johnson: Damaged Product
✓ TKT-003 - Maria Chen: Wrong Size Delivered
✓ ... 17 more tickets
```

### **Understanding Each Ticket Card**

Click any ticket to see:

```
┌─────────────────────────────────────────┐
│ TICKET DETAILS                          │
├─────────────────────────────────────────┤
│ Ticket ID:        TKT-007               │
│ Customer Email:   grace.lee@email.com   │
│ Subject:          Changed my mind       │
│ Body:             Return USB cables     │
│ Source:           Email                 │
│ Created At:       2026-04-15 10:30 AM   │
│                                         │
│ [Process] [Close]                       │
└─────────────────────────────────────────┘
```

**Ticket Information:**
- **Ticket ID** - Unique identifier (TKT-001 to TKT-020)
- **Customer Email** - Who submitted the ticket
- **Subject** - Issue summary
- **Body** - Detailed problem description
- **Source** - How ticket came in (Email, Chat, etc.)
- **Created At** - When ticket was submitted

---

## ⚙️ Processing Tickets

### **Method 1: Process One Ticket at a Time**

#### **Step 1: Load and Select a Ticket**
- Click "Load All Tickets"
- Click any ticket in the list
- Modal shows ticket details

#### **Step 2: Click "Process" Button**
```
Modal popup shows:
┌────────────────────────────────┐
│ TICKET DETAILS                 │
│ ... ticket information ...     │
│                                │
│         [Process] [Close]      │
└────────────────────────────────┘
     ↑ Click this
```

#### **Step 3: Watch the Processing**
- Loading modal appears: **"Processing ticket..."**
- Spinner animates showing system is working
- Takes 2-5 seconds depending on API

#### **Step 4: See the Result**
- Modal closes automatically
- Result appears in **Results Table**
- Statistics update in real-time
- Confidence score displays

#### **Example Result:**
```
Ticket ID:  TKT-007
Action:     DENY
Confidence: 70%
Reasoning:  Order is outside 60-day return window
```

### **Method 2: Process All Tickets at Once**

#### **Step 1: Click "Process All At Once" Button**
```
Main dashboard:
┌──────────────────────┐
│ Process All At Once  │  ← Click here
├──────────────────────┤
```

#### **Step 2: Confirmation Modal**
```
┌─────────────────────────────┐
│ Process 20 Tickets?         │
│                             │
│ This will process all       │
│ tickets concurrently.       │
│                             │
│ [Start] [Cancel]            │
└─────────────────────────────┘
```

Click **[Start]**

#### **Step 3: Watch Progress**
- Modal shows: **"Processing all tickets..."**
- Spinner animates
- Results populate in real-time (you'll see tickets appearing in Results Table)
- Statistics update as each ticket completes

#### **Step 4: Completion**
- Modal closes when all done
- Results Table shows all 20 tickets
- Statistics fully populated
- Average processing time displayed

**Example Summary:**
```
✓ Processed: 20 tickets
✓ Duration: 15 seconds
✓ Approved: 7 tickets
✓ Denied: 8 tickets
✓ Escalated: 5 tickets
✓ Average Confidence: 78%
```

---

## 📈 Understanding Results

### **Results Table Columns**

| Column | What It Shows | Example |
|--------|---------------|---------|
| **Ticket ID** | Unique ticket identifier | TKT-007 |
| **Customer** | Customer email (abbreviated) | grace.lee@... |
| **Action** | Decision made by AI | DENY, APPROVE, ESCALATE |
| **Confidence** | How confident the AI is (0-100%) | 70% |
| **Date** | When ticket was processed | Apr 19, 2:30 PM |

### **Understanding the Actions**

| Action | Meaning | Example |
|--------|---------|---------|
| **APPROVE** ✅ | Grant the customer's request | Approve refund, replace item |
| **DENY** ❌ | Reject the customer's request | Out of return window |
| **ESCALATE** ⚠️ | Needs human review | Unusual situation, uncertain |

### **Confidence Score Interpretation**

```
90-100%  ████████████ Highly Confident - Trust the decision
70-90%   ██████████   Confident - Good decision
50-70%   ████████     Moderate - Review recommended
<50%     ████         Low - Should escalate
```

**What confidence means:**
- Based on policy clarity and evidence quality
- High = clear policy match
- Low = ambiguous situation (escalate to human)

### **Example Row**
```
TKT-007 | grace.lee@email.com | DENY | 70% | Apr 19, 2:35 PM
```

Click the row to see **full explainable decision** (see next section)

---

## 🔍 Viewing Explainable Decisions

### **Why Explainability Matters**

Every AI decision includes a **complete reasoning chain** showing:
- ✅ What information was gathered
- ✅ What policies were applied
- ✅ Why the decision was made
- ✅ Confidence breakdown

### **How to View Full Decision**

#### **Step 1: Click a Result Row**
```
Results Table:
┌─────────────────────────────────┐
│ TKT-007 | grace... | DENY | 70% │ ← Click this row
└─────────────────────────────────┘
```

#### **Step 2: Details Modal Opens**
```
┌──────────────────────────────────────────────┐
│ DECISION DETAILS - TKT-007                  │
├──────────────────────────────────────────────┤
│ Decision:         DENY                       │
│ Primary Reason:   Order outside return       │
│                   window (768 days)          │
│ Confidence:       70%                        │
│                                              │
│ [View Full Details] [Close]                  │
└──────────────────────────────────────────────┘
```

#### **Step 3: Click "View Full Details"**
```
FULL EXPLAINABLE DECISION
┌────────────────────────────────────────┐
│ Decision Type: DENY                    │
│                                        │
│ PRIMARY REASON:                        │
│ Order is outside 60-day return window  │
│ (768 days since delivery)              │
│                                        │
│ REASONING CHAIN:                       │
│ 1. ✓ Verified customer: Grace Lee     │
│    (Gold tier, verified)               │
│                                        │
│ 2. ✓ Retrieved order: ORD-1007        │
│    ($49.98, USB Cables)                │
│                                        │
│ 3. 📅 Calculated timeline:             │
│    Delivery: Jan 15, 2024              │
│    Request: April 19, 2026             │
│    Elapsed: 768 days vs 60-day policy  │
│                                        │
│ 4. ⚖️  Applied policy: INELIGIBLE      │
│    Return window expired               │
│                                        │
│ CONFIDENCE BREAKDOWN:                  │
│ • Evidence Quality:    90% (High)      │
│ • Policy Clarity:      95% (High)      │
│ • Customer History:    70% (Good)      │
│ • Overall Confidence:  70%             │
│                                        │
│ POLICY FACTORS APPLIED:                │
│ • 60-day return window policy          │
│ • Clear return eligibility rules       │
│ • Customer tier verification           │
│ • Product type considerations          │
│                                        │
│ TOOLS USED (4 total):                  │
│ ✓ get_customer()  - Verified customer │
│ ✓ get_order()     - Order details     │
│ ✓ check_refund_eligibility()          │
│ ✓ send_reply()    - Send decision     │
│                                        │
│ WARNINGS:                              │
│ (None - straightforward decision)      │
│                                        │
│ FOLLOW-UP ACTIONS:                     │
│ • Sent denial to customer              │
│ • Offered escalation option            │
│ • Suggested warranty review            │
│                                        │
│ [Close]                                │
└────────────────────────────────────────┘
```

### **Understanding Each Section**

**Decision Type**
- What decision was made: APPROVE, DENY, or ESCALATE

**Primary Reason**
- Main justification in one sentence

**Reasoning Chain**
- Step-by-step how AI reached the decision
- Shows tools used and information gathered
- Numbered 1, 2, 3, 4 for clarity

**Confidence Breakdown**
- Evidence Quality: How much facts support the decision
- Policy Clarity: How clear the policy is
- Customer History: Relevant background info
- Overall: Final confidence (0-100%)

**Policy Factors**
- Which company policies were applied
- How they influenced the decision

**Tools Used**
- get_customer: Looked up customer info
- get_order: Retrieved order details
- check_refund_eligibility: Checked if eligible
- send_reply: Notified customer

**Warnings**
- Any concerns or unusual situations
- Empty = straightforward decision

**Follow-up Actions**
- What customer will be told
- Next steps if needed

---

## 📊 Batch Processing

### **Process All 20 Tickets Together**

#### **Why Batch Process?**
- ✅ Faster - All tickets processed simultaneously
- ✅ More efficient - Better for large volumes
- ✅ Real-time stats - Watch results populate
- ✅ Better demo - Shows system capability

#### **How to Batch Process**

**Step 1:** From main dashboard, click **"Process All At Once"**

**Step 2:** Confirmation appears:
```
Process 20 tickets concurrently?
This will process all support tickets
in parallel using the autonomous agent.

[Start Processing] [Cancel]
```

Click **[Start Processing]**

**Step 3:** Watch the magic happen
```
Processing all tickets...
┌─────────────────────┐
│        ◌ ◌ ◌        │  (spinner)
│  2/20 tickets done  │
└─────────────────────┘
```

**Step 4:** Results appear in real-time
- As each ticket completes, it appears in Results Table
- Statistics update live
- Progress counter shows: "2/20", "5/20", etc.

**Step 5:** All done!
```
✓ COMPLETED
✓ 20 tickets processed
✓ 15 seconds total
✓ Results shown below
```

#### **Real-Time Updates During Batch**

Watch the **Statistics Bar** change:
```
BEFORE:
Total Processed: 0  | Approved: 0  | Denied: 0  | Escalated: 0

DURING (after 5 seconds):
Total Processed: 8  | Approved: 3  | Denied: 4  | Escalated: 1

FINAL (after 15 seconds):
Total Processed: 20 | Approved: 7  | Denied: 8  | Escalated: 5
Average Confidence: 78%
```

---

## 📈 Statistics & Analytics

### **What Statistics Show**

The **top statistics bar** displays:

| Metric | What It Means |
|--------|---------------|
| **Total Processed** | How many tickets have been handled |
| **Approved** | How many refunds/requests granted |
| **Denied** | How many requests rejected |
| **Escalated** | How many need human review |
| **Avg Confidence** | Average AI confidence (0-100%) |

### **Example Statistics After Processing 20 Tickets**

```
┌──────────────────────────────────────────────┐
│ PROCESSING SUMMARY                          │
├──────────────────────────────────────────────┤
│                                              │
│ Total Processed:    20 tickets               │
│ Processing Time:    15.3 seconds             │
│ Avg Time/Ticket:    0.77 seconds             │
│                                              │
│ DECISIONS:                                   │
│ ✅ Approved:        7 (35%)                  │
│ ❌ Denied:          8 (40%)                  │
│ ⚠️  Escalated:      5 (25%)                  │
│                                              │
│ CONFIDENCE METRICS:                          │
│ Average:            78%                      │
│ Minimum:            52%                      │
│ Maximum:            95%                      │
│ High Confidence:    15 (>90%)                │
│ Low Confidence:     2 (<70%)                 │
│                                              │
│ TOOL PERFORMANCE:                            │
│ Total Tool Calls:   80 calls                 │
│ Avg per Ticket:     4.0 calls                │
│ Success Rate:       100%                     │
│                                              │
└──────────────────────────────────────────────┘
```

### **Interpreting the Metrics**

**Decision Split (Approved vs Denied vs Escalated)**
- Healthy mix = system is calibrated correctly
- Too many escalations = system uncertain
- Too few escalations = system overconfident

**Confidence Metrics**
- 78% average = Good, balanced confidence
- High confidence (>90%) = Clear-cut decisions
- Low confidence (<70%) = Ambiguous cases

**Tool Performance**
- 4 tools per ticket = Normal (customer, order, eligibility, reply)
- 100% success = No tool failures (ideal)

---

## 🐛 Troubleshooting

### **Issue 1: Page Won't Load**

**Problem:** Blank page or connection error

**Solution:**
```
1. Refresh the page: Ctrl+R (Windows) or Cmd+R (Mac)
2. Wait 10 seconds (server might be starting)
3. Clear cache: Ctrl+Shift+Delete
4. Try different browser
5. Check: https://hackathon2026-ankush-production.up.railway.app/api/health
   (should show {"status": "healthy"})
```

### **Issue 2: Tickets Won't Load**

**Problem:** "Load All Tickets" button does nothing

**Solution:**
```
1. Wait 5 seconds (API might be starting)
2. Refresh page
3. Check browser console: F12 → Console tab
4. Look for error messages
5. Try "Clear Results" button to reset
```

### **Issue 3: "Process" Button Not Working**

**Problem:** Clicking Process doesn't do anything

**Solution:**
```
1. Make sure you clicked "Load All Tickets" first
2. Make sure you selected a ticket (modal opened)
3. Wait 3 seconds (server processing)
4. Check network: F12 → Network tab
5. Try a different ticket
6. Refresh page and retry
```

### **Issue 4: Processing Takes Too Long**

**Problem:** Spinner spins forever (>30 seconds)

**Solution:**
```
1. This is normal for first request (cold start)
2. Wait up to 60 seconds
3. If still stuck, refresh and try again
4. For batch: Process smaller groups first
5. Try at different time (server less busy)
```

### **Issue 5: Results Don't Show After Processing**

**Problem:** Clicked Process, no result appears

**Solution:**
```
1. Scroll down to Results Table
2. Click "Clear Results" then retry
3. Check if you're on same session (different tab?)
4. Try batch processing instead
5. Check API health: /api/health endpoint
```

### **Issue 6: Explainable Decision Is Empty**

**Problem:** Click result but see empty details

**Solution:**
```
1. Wait 5 seconds and refresh
2. Try a different ticket result
3. Try reprocessing the ticket
4. Check browser console for errors
5. Try "Clear Results" then reprocess
```

### **Issue 7: Statistics Don't Update**

**Problem:** Stats bar stays at zero after processing

**Solution:**
```
1. Scroll to top of page
2. Refresh page
3. Try processing one more ticket
4. Check if results table populated
   (stats calculated from results)
5. Try clearing and reprocessing
```

### **Issue 8: Browser Console Shows Errors**

**Check for common messages:**

```
"Failed to fetch from API"
→ Server might be down, check /api/health

"CORS error"
→ Refresh page, try different browser

"JSON parse error"
→ API returned invalid response, wait and retry

"Port already in use"
→ Shouldn't happen with cloud hosted
```

**How to check console:**
```
Windows: F12 → Console tab
Mac:     Cmd+Option+J → Console tab
```

---

## 💡 Pro Tips

### **Tip 1: Demo Mode**
- Process one ticket at a time to see system reasoning
- Then batch process all to show performance
- Great for presentations!

### **Tip 2: Watch Confidence Scores**
- High confidence (>90%) = Trust the decision
- Medium confidence (70-90%) = Good decision
- Low confidence (<70%) = Note the uncertainty

### **Tip 3: Read the Reasoning Chain**
- Most interesting part of the system
- Shows how AI thinks about decisions
- Perfect for explaining AI decisions to stakeholders

### **Tip 4: Compare Decisions**
- Click multiple results to see different reasoning
- See how different policies apply
- Notice how confidence varies by case

### **Tip 5: Share Results**
- Screenshot the decision details
- Share the stats summary
- Show reasoning chain to team

### **Tip 6: Use Batch Processing**
- Shows system performance
- Demonstrates concurrent processing
- Impresses with speed (20 tickets in 15 seconds)

### **Tip 7: Check Audit Log**
- Go to `/api/audit-log` endpoint
- See permanent record of all decisions
- Shows compliance/audit trail

---

## 🎯 Common Use Cases

### **Use Case 1: Single Ticket Demo**
```
1. Load tickets
2. Click one ticket
3. Show details to stakeholders
4. Click Process
5. Explain the decision
6. Click "View Full Details"
7. Walk through reasoning chain
```

### **Use Case 2: System Performance Demo**
```
1. Show empty dashboard
2. Click "Process All At Once"
3. Watch real-time updates
4. Show final statistics
5. Point out 20 tickets in 15 seconds
6. Average confidence 78%
```

### **Use Case 3: Explainability Demo**
```
1. Process one ticket
2. Click result
3. Click "View Full Details"
4. Show reasoning chain
5. Highlight policy factors
6. Explain confidence breakdown
7. Show tool justification
```

### **Use Case 4: Audit & Compliance**
```
1. Process some tickets
2. Navigate to /api/audit-log
3. Show permanent record
4. Highlight full decision data
5. Explain compliance benefits
6. Show timestamp and decision trail
```

---

## ✅ Quick Checklist

Before demoing, verify:

- [ ] Browser window is large enough
- [ ] Good internet connection
- [ ] No pop-up blockers
- [ ] JavaScript enabled
- [ ] Cleared browser cache
- [ ] Tested on your device
- [ ] Know what each button does
- [ ] Have questions ready for audience

---

## 📞 Need Help?

**System Issues:**
1. Check: https://hackathon2026-ankush-production.up.railway.app/api/health
2. Refresh the page
3. Clear browser cache
4. Try different browser
5. Contact developer

**Understanding Results:**
1. Read the explainable decision
2. Check confidence score
3. Review reasoning chain
4. Look at policy factors applied

**Demo Questions:**
1. "How does it gather information?" → Show tool calls
2. "How confident is it?" → Show confidence scores
3. "What if it's wrong?" → Show escalation for uncertain cases
4. "Can you explain the decision?" → Show reasoning chain

---

## 🎓 Learning Resources

See the main README for:
- Architecture documentation
- System design details
- LLM integration info
- Deployment guides
- Code samples

---

**Ready to demo?** Open the app and start processing! 🚀

Have fun showing off your autonomous support agent! 🎉

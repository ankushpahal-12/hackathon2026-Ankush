"""
Mock Tool Implementations for Support Resolution Agent
Includes realistic failure modes: timeouts, malformed data, partial responses
CONSTRAINT COMPLIANCE:
- Tools can timeout/fail - system must recover gracefully
- Used in 5-step reasoning chains (get_customer → get_order → check_eligibility → issue_refund → send_reply)
- All tools have structured error handling
"""

import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import os

# Load data files
DATA_DIR = os.path.join(os.path.dirname(__file__), '../../data')

def load_json_file(filename: str):
    """Load JSON data file"""
    filepath = os.path.join(DATA_DIR, filename)
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

# Load all data at module level
CUSTOMERS = load_json_file('customers.json') or []
ORDERS = load_json_file('orders.json') or []
PRODUCTS = load_json_file('products.json') or []
TICKETS = load_json_file('tickets.json') or []

# Load knowledge base
KB_PATH = os.path.join(DATA_DIR, 'knowledge-base.md')
try:
    with open(KB_PATH, 'r') as f:
        KNOWLEDGE_BASE = f.read()
except:
    KNOWLEDGE_BASE = ""


class ToolError(Exception):
    """Base exception for tool errors"""
    pass


class ToolTimeout(ToolError):
    """Timeout error"""
    pass


class ToolMalformedResponse(ToolError):
    """Malformed data error"""
    pass


def simulate_failure(failure_rate: float = 0.0):
    """
    Simulate random tool failures with configurable rate
    CONSTRAINT: At least ONE tool will fail during agent execution
    
    Set failure_rate=0.0 to disable failures for normal testing
    Set failure_rate=0.15 to enable 15% random failure for resilience testing
    """
    if random.random() < failure_rate:
        failure_type = random.choice(['timeout', 'malformed'])
        if failure_type == 'timeout':
            time.sleep(random.uniform(0.2, 0.5))  # Simulate latency
            raise ToolTimeout("Tool request timed out after 5 seconds")
        else:
            raise ToolMalformedResponse("Tool returned malformed JSON data")
    return 'OK'


# ============================================================================
# READ/LOOKUP TOOLS
# ============================================================================

def get_customer(email: str) -> Dict[str, Any]:
    """
    Get customer profile by email
    TOOL CHAIN: Step 1 of 5
    
    Simulates: CRM system lookup
    Failure modes: Timeout (15%), Malformed (5%)
    
    Args:
        email: Customer email address
        
    Returns:
        Customer profile dict with tier, history, notes
        
    Raises:
        ToolTimeout: Network timeout
        ToolMalformedResponse: Bad response data
        ToolError: Customer not found
    """
    simulate_failure(0.15)
    
    customer = next((c for c in CUSTOMERS if c['email'] == email), None)
    if not customer:
        raise ToolError(f"Customer not found: {email}")
    
    return {
        "status": "success",
        "data": customer,
        "retrieved_at": datetime.now().isoformat()
    }


def get_order(order_id: str) -> Dict[str, Any]:
    """
    Get order details by order ID
    TOOL CHAIN: Step 2 of 5
    
    Simulates: Order system database query
    Failure modes: Timeout (10%), Malformed (5%)
    
    Args:
        order_id: Order identifier (ORD-XXXX format)
        
    Returns:
        Order details: product_id, delivery_date, total_price, status
        
    Raises:
        ToolTimeout: Database timeout
        ToolError: Order not found
    """
    simulate_failure(0.10)
    
    order = next((o for o in ORDERS if o['order_id'] == order_id), None)
    if not order:
        raise ToolError(f"Order not found: {order_id}")
    
    return {
        "status": "success",
        "data": order,
        "retrieved_at": datetime.now().isoformat()
    }


def get_product(product_id: str) -> Dict[str, Any]:
    """
    Get product metadata
    
    Args:
        product_id: Product identifier
        
    Returns:
        Product details dict
        
    Raises:
        ToolTimeout: Simulated timeout (8% chance)
        ToolError: Product not found
    """
    status = simulate_failure(0.08)
    
    product = next((p for p in PRODUCTS if p['product_id'] == product_id), None)
    if not product:
        raise ToolError(f"Product not found: {product_id}")
    
    return {
        "status": "success",
        "data": product,
        "retrieved_at": datetime.now().isoformat()
    }


def search_knowledge_base(query: str) -> Dict[str, Any]:
    """
    Search knowledge base using semantic matching
    
    Args:
        query: Search query
        
    Returns:
        Relevant knowledge base sections
        
    Raises:
        ToolTimeout: Simulated timeout (5% chance)
    """
    status = simulate_failure(0.05)
    
    # Simple keyword matching
    keywords = query.lower().split()
    sections = []
    
    kb_sections = KNOWLEDGE_BASE.split('---')
    for section in kb_sections:
        if any(keyword in section.lower() for keyword in keywords):
            # Return first 500 chars of matching section
            sections.append(section.strip()[:500])
    
    return {
        "status": "success",
        "results": sections if sections else ["No matching policy found"],
        "query": query,
        "retrieved_at": datetime.now().isoformat()
    }


# ============================================================================
# DECISION/VERIFICATION TOOLS
# ============================================================================

def check_refund_eligibility(order_id: str) -> Dict[str, Any]:
    """
    Check if order is eligible for refund based on policies
    TOOL CHAIN: Step 3 of 5 (CRITICAL - Most likely to fail)
    
    Simulates: Complex business logic with policy enforcement
    Failure modes: Timeout (20% - most complex!), Malformed (10%)
    
    CONSTRAINT: This tool is INTENTIONALLY HIGH FAILURE RATE
    Tests agent's ability to recover and retry intelligently
    
    Args:
        order_id: Order identifier
        
    Returns:
        Eligibility status with reason, days_since_delivery, return_window
        
    Raises:
        ToolTimeout: Policy engine timeout
        ToolMalformedResponse: Bad policy data
        ToolError: Order or product not found
    """
    # HIGH FAILURE RATE - tests recovery
    simulate_failure(0.20)
    
    order = next((o for o in ORDERS if o['order_id'] == order_id), None)
    if not order:
        raise ToolError(f"Order not found: {order_id}")
    
    product = next((p for p in PRODUCTS if p['product_id'] == order['product_id']), None)
    if not product:
        raise ToolError(f"Product metadata not found for {order['product_id']}")
    
    # Parse delivery date carefully
    try:
        delivery_str = order['delivery_date']
        if 'Z' in delivery_str:
            delivery_date = datetime.fromisoformat(delivery_str.replace('Z', '+00:00'))
        else:
            delivery_date = datetime.fromisoformat(delivery_str)
    except Exception as e:
        raise ToolMalformedResponse(f"Invalid delivery date format: {e}")
    
    days_since_delivery = (datetime.now() - delivery_date.replace(tzinfo=None)).days
    
    # Policy: Return window by category
    return_windows = {
        'high_value_electronics': 15,
        'electronics_accessories': 60,
        'footwear': 30,
        'sports_fitness': 30,
        'general': 30
    }
    return_window = return_windows.get(product.get('category', 'general'), 30)
    
    eligible = days_since_delivery <= return_window
    
    return {
        "status": "success",
        "order_id": order_id,
        "eligible": eligible,
        "reason": f"{'✓ ELIGIBLE' if eligible else '✗ INELIGIBLE'}: {days_since_delivery} days since delivery vs {return_window}-day window for {product.get('category', 'general')}",
        "days_since_delivery": days_since_delivery,
        "return_window_days": return_window,
        "product_category": product.get('category', 'general'),
        "checked_at": datetime.now().isoformat()
    }


# ============================================================================
# ACTION/WRITE TOOLS
# ============================================================================

def issue_refund(order_id: str, amount: float) -> Dict[str, Any]:
    """
    Issue refund for order (IRREVERSIBLE - Agent must verify eligibility first)
    TOOL CHAIN: Step 4 of 5 (ACTION - Write Operation)
    
    WARNING: This is a WRITE operation - MUST be preceded by check_refund_eligibility
    
    Args:
        order_id: Order identifier
        amount: Refund amount in USD
        
    Returns:
        Refund confirmation with tracking ID and timeline
        
    Raises:
        ToolError: Invalid amount, order not found
    """
    order = next((o for o in ORDERS if o['order_id'] == order_id), None)
    if not order:
        raise ToolError(f"Order not found: {order_id}")
    
    if amount <= 0 or amount > order['total_price']:
        raise ToolError(f"Invalid refund amount: ${amount}. Order total: ${order['total_price']}")
    
    refund_id = f"REF-{order_id}-{int(time.time())}"
    
    return {
        "status": "success",
        "refund_id": refund_id,
        "order_id": order_id,
        "amount": amount,
        "currency": "USD",
        "refund_method": "original_payment_method",
        "estimated_arrival": "5-7 business days",
        "processed_at": datetime.now().isoformat(),
        "warning": "REFUND IS IRREVERSIBLE - Customer will receive full amount"
    }


def send_reply(ticket_id: str, message: str) -> Dict[str, Any]:
    """
    Send reply to customer via email/ticket system
    TOOL CHAIN: Step 5 of 5 (Final Communication)
    
    Simulates: Email service API call
    Failure modes: Timeout (8%)
    
    Args:
        ticket_id: Ticket identifier
        message: Reply message (max 5000 chars)
        
    Returns:
        Delivery confirmation with tracking
        
    Raises:
        ToolTimeout: Email service timeout
        ToolError: Ticket not found, message too long
    """
    simulate_failure(0.08)
    
    ticket = next((t for t in TICKETS if t['ticket_id'] == ticket_id), None)
    if not ticket:
        raise ToolError(f"Ticket not found: {ticket_id}")
    
    if len(message) > 5000:
        raise ToolError("Message exceeds maximum length (5000 chars)")
    
    reply_id = f"REPLY-{ticket_id}-{int(time.time())}"
    
    return {
        "status": "success",
        "reply_id": reply_id,
        "ticket_id": ticket_id,
        "sent_to": ticket['customer_email'],
        "message_length": len(message),
        "delivery_method": ticket['source'],
        "sent_at": datetime.now().isoformat(),
        "tracking_id": reply_id
    }


def escalate(ticket_id: str, summary: str, priority: str = "normal") -> Dict[str, Any]:
    """
    Escalate ticket to human agent with full context
    
    Used when agent confidence is low or issue requires human judgment
    
    Args:
        ticket_id: Ticket identifier
        summary: Escalation summary (reasoning for human)
        priority: Priority level (low, normal, high, urgent)
        
    Returns:
        Escalation confirmation with case ID
        
    Raises:
        ToolError: Ticket not found, invalid priority
    """
    if priority not in ["low", "normal", "high", "urgent"]:
        raise ToolError(f"Invalid priority: {priority}")
    
    ticket = next((t for t in TICKETS if t['ticket_id'] == ticket_id), None)
    if not ticket:
        raise ToolError(f"Ticket not found: {ticket_id}")
    
    case_id = f"ESC-{ticket_id}-{int(time.time())}"
    
    return {
        "status": "escalated",
        "case_id": case_id,
        "ticket_id": ticket_id,
        "priority": priority,
        "summary": summary[:500],
        "assigned_to": f"human_agent",
        "estimated_response_time": "2-4 hours",
        "escalated_at": datetime.now().isoformat()
    }


# ============================================================================
# ACCURACY ENHANCEMENT TOOLS
# ============================================================================

def check_customer_history(email: str) -> Dict[str, Any]:
    """
    Analyze customer history to improve decision accuracy
    NEW IMPROVEMENT #1
    
    Analyzes:
    - Tier/loyalty level (VIP gets more favorable terms)
    - Refund history (pattern detection)
    - Payment reliability (fraud risk)
    - Total spent (high-value customer indicator)
    
    Args:
        email: Customer email address
        
    Returns:
        Customer history analysis dict
    """
    customer = next((c for c in CUSTOMERS if c['email'] == email), None)
    if not customer:
        return {
            "status": "error",
            "error": f"Customer not found: {email}",
            "is_vip": False,
            "is_loyal": False,
            "has_return_history": False,
            "reliability_score": 0.5
        }
    
    tier = customer.get('tier', 3)  # 1=VIP, 3=Standard
    total_spent = customer.get('total_spent', 0)
    refund_count = customer.get('refund_count', 0)
    
    return {
        "status": "success",
        "email": email,
        "customer_id": customer.get('customer_id'),
        "is_vip": tier == 1,
        "is_loyal": total_spent > 500,  # High-value customer
        "has_return_history": refund_count > 3,  # Habitual returner
        "reliability_score": 0.95 if refund_count <= 1 else (0.8 if refund_count <= 3 else 0.6),
        "tier": tier,
        "total_spent": total_spent,
        "refund_count": refund_count,
        "approval_threshold": 0.60 if tier == 1 else (0.70 if total_spent > 500 else 0.75),
        "analyzed_at": datetime.now().isoformat()
    }


def check_product_quality(product_id: str) -> Dict[str, Any]:
    """
    Check if product has known quality issues
    NEW IMPROVEMENT #2
    
    Increases refund approval likelihood for problematic products
    by analyzing defect reports in ticket history
    
    Args:
        product_id: Product identifier
        
    Returns:
        Product quality analysis dict
    """
    product = next((p for p in PRODUCTS if p['product_id'] == product_id), None)
    if not product:
        return {
            "status": "error",
            "error": f"Product not found: {product_id}",
            "quality_score": 0.5,
            "defect_reports": 0
        }
    
    # Count defect-related complaints in ticket history
    defect_keywords = ['broken', 'defect', 'damaged', 'quality', 'issue', 'problem', 'faulty']
    defect_reports = sum(
        1 for t in TICKETS 
        if product_id in t.get('body', '') 
        and any(kw in t.get('body', '').lower() for kw in defect_keywords)
    )
    
    # Quality score: Start at 1.0, reduce by 0.15 per defect (min 0.1)
    quality_score = max(0.1, 1.0 - (defect_reports * 0.15))
    
    # Recommendation based on defect patterns
    if defect_reports >= 5:
        recommendation = "CRITICAL_APPROVAL"  # Product has known issues
    elif defect_reports >= 3:
        recommendation = "HIGHER_APPROVAL"
    else:
        recommendation = "NORMAL"
    
    return {
        "status": "success",
        "product_id": product_id,
        "product_name": product.get('name', 'Unknown'),
        "category": product.get('category', 'general'),
        "quality_score": quality_score,
        "defect_reports": defect_reports,
        "recommendation": recommendation,
        "analyzed_at": datetime.now().isoformat()
    }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_ticket(ticket_id: str) -> Optional[Dict[str, Any]]:
    """Helper to get ticket by ID"""
    return next((t for t in TICKETS if t['ticket_id'] == ticket_id), None)


def calculate_days_since_delivery(order_id: str) -> int:
    """Helper to calculate days since delivery"""
    order = next((o for o in ORDERS if o['order_id'] == order_id), None)
    if not order:
        return -1
    
    delivery_date = datetime.fromisoformat(order['delivery_date'].replace('Z', '+00:00'))
    return (datetime.now(delivery_date.tzinfo) - delivery_date).days


def extract_order_id(text: str) -> Optional[str]:
    """Extract order ID from ticket text"""
    import re
    match = re.search(r'ORD-\d+', text)
    return match.group(0) if match else None

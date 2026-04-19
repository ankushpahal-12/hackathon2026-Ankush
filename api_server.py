#!/usr/bin/env python3
"""
REST API Server for Autonomous Support Resolution Agent
Provides HTTP endpoints for frontend to interact with agent
"""

import asyncio
import json
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agent.support_agent import SupportAgent, ResolutionAction
from tools.mock_tools import TICKETS, get_ticket

# Setup Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api_server.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize agent
agent = SupportAgent(max_retries=2, tool_timeout=5)

# Store results in memory (use database in production)
processing_results = {}
audit_log = []

# Audit log file path
AUDIT_LOG_FILE = os.path.join(os.path.dirname(__file__), 'output', 'audit_log.json')

# ==================== AUDIT LOG FILE MANAGEMENT ====================

def load_audit_log_from_file():
    """Load existing audit log from JSON file"""
    global audit_log, processing_results
    try:
        if os.path.exists(AUDIT_LOG_FILE):
            with open(AUDIT_LOG_FILE, 'r') as f:
                content = f.read().strip()
                if not content:  # File is empty
                    logger.info(f"Audit log file exists but is empty. Starting fresh.")
                    audit_log = []
                    return
                
                data = json.loads(content)
                if isinstance(data, dict) and 'resolutions' in data:
                    # Load from structured audit log format
                    audit_log = data.get('resolutions', [])
                    logger.info(f"Loaded {len(audit_log)} existing audit entries from {AUDIT_LOG_FILE}")
                    
                    # NOTE: Do NOT sync cached results to processing_results on startup
                    # This allows fresh processing_results display for new sessions
                    # (Audit log persists for auditing purposes, but doesn't pre-populate results)
                    logger.info(f"Audit log loaded for reference only. Results display will be empty until new tickets are processed.")
                    
                elif isinstance(data, list):
                    # Load from simple list format
                    audit_log = data
                    logger.info(f"Loaded {len(audit_log)} existing audit entries from {AUDIT_LOG_FILE}")
        else:
            logger.info(f"Audit log file not found. Will create on first save.")
            audit_log = []
    except Exception as e:
        logger.error(f"Error loading audit log from file: {str(e)}")
        audit_log = []

def save_audit_log_to_file():
    """Save audit log to JSON file"""
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(AUDIT_LOG_FILE), exist_ok=True)
        
        # Create structured audit log object
        audit_data = {
            'session_id': 'session_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),
            'generated_at': datetime.now().isoformat(),
            'total_tickets_processed': len(audit_log),
            'resolutions': audit_log
        }
        
        # Write to file with pretty formatting
        with open(AUDIT_LOG_FILE, 'w') as f:
            json.dump(audit_data, f, indent=2)
        
        logger.info(f"Saved audit log with {len(audit_log)} entries to {AUDIT_LOG_FILE}")
    except Exception as e:
        logger.error(f"Error saving audit log to file: {str(e)}")

# Load existing audit log on startup
load_audit_log_from_file()


# ==================== TICKETS ENDPOINTS ====================

@app.route('/api/tickets', methods=['GET'])
def get_tickets():
    """Get all available tickets"""
    try:
        tickets = TICKETS
        return jsonify({
            'success': True,
            'data': {
                'tickets': tickets,
                'total': len(tickets)
            }
        }), 200
    except Exception as e:
        logger.error(f"Error fetching tickets: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/tickets/<ticket_id>', methods=['GET'])
def get_single_ticket(ticket_id):
    """Get details for a specific ticket"""
    try:
        ticket = get_ticket(ticket_id)
        if not ticket:
            return jsonify({
                'success': False,
                'error': f'Ticket {ticket_id} not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': ticket
        }), 200
    except Exception as e:
        logger.error(f"Error fetching ticket {ticket_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== PROCESSING ENDPOINTS ====================

@app.route('/api/process/ticket', methods=['POST'])
def process_single_ticket():
    """Process a single ticket"""
    try:
        data = request.json
        ticket_id = data.get('ticket_id')
        
        if not ticket_id:
            return jsonify({
                'success': False,
                'error': 'ticket_id is required'
            }), 400
        
        # CHECK FOR DUPLICATES: If ticket already processed, return existing result
        existing_entry = next((entry for entry in audit_log if entry.get('ticket_id') == ticket_id), None)
        if existing_entry:
            logger.info(f"Ticket {ticket_id} already processed. Returning existing result.")
            return jsonify({
                'success': True,
                'data': {
                    'ticket_id': ticket_id,
                    'action': existing_entry.get('action'),
                    'confidence': existing_entry.get('confidence_score'),
                    'reasoning': existing_entry.get('reasoning'),
                    'decision_reason': existing_entry.get('decision_reason', existing_entry.get('reasoning')),  # NEW
                    'tool_calls': len(existing_entry.get('tool_calls', [])),
                    'note': 'Result from previous processing (not reprocessed)'
                }
            }), 200
        
        # Get full ticket details
        ticket = get_ticket(ticket_id)
        if not ticket:
            return jsonify({
                'success': False,
                'error': f'Ticket {ticket_id} not found'
            }), 404
        
        # Process ticket (sync wrapper for async function)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            resolution = loop.run_until_complete(agent.process_ticket(ticket_id))
            
            # Create audit log entry with full ticket details
            audit_entry = {
                'ticket_id': ticket_id,
                'customer_email': ticket.get('customer_email', ''),
                'subject': ticket.get('subject', ''),
                'body': ticket.get('body', ''),
                'source': ticket.get('source', ''),
                'created_at': ticket.get('created_at', ''),
                'action': resolution.action.value,
                'reasoning': resolution.reasoning,
                'decision_reason': resolution.decision_reason,  # NEW: LLM-generated reason
                'confidence_score': resolution.confidence_score,
                'accuracy_factors': resolution.accuracy_factors,  # NEW: Include accuracy breakdown
                'processing_time_ms': 0,
                'tool_calls': [
                    {
                        'name': tool_call.name,
                        'params': tool_call.params,
                        'result': tool_call.result,
                        'timestamp': tool_call.timestamp.isoformat() if hasattr(tool_call.timestamp, 'isoformat') else str(tool_call.timestamp),
                        'duration_ms': tool_call.duration_ms,
                        'error': tool_call.error,
                        'error_type': tool_call.error_type if hasattr(tool_call, 'error_type') else None
                    }
                    for tool_call in resolution.tool_calls
                ],
                'ui_interaction': f"User clicked 'Process One by One' at {datetime.now().isoformat()}. UI displayed ticket {ticket_id} in processing state.",
                'processed_at': datetime.now().isoformat()
            }
            
            # Add to audit log
            audit_log.append(audit_entry)
            logger.info(f"✓ Added {ticket_id} to audit_log (total: {len(audit_log)})")
            
            # Save to JSON file
            save_audit_log_to_file()
            
            # Store result (for API responses)
            processing_results[ticket_id] = {
                'ticket_id': ticket_id,
                'action': resolution.action.value,
                'confidence_score': resolution.confidence_score,
                'reasoning': resolution.reasoning,
                'decision_reason': resolution.decision_reason,  # NEW: Include LLM reason
                'tool_calls': len(resolution.tool_calls),
                'timestamp': datetime.now().isoformat()
            }
            logger.info(f"✓ Added {ticket_id} to processing_results (total: {len(processing_results)})")
            
            return jsonify({
                'success': True,
                'data': {
                    'ticket_id': ticket_id,
                    'action': resolution.action.value,
                    'confidence': resolution.confidence_score,
                    'reasoning': resolution.reasoning,
                    'decision_reason': resolution.decision_reason,  # NEW: LLM-generated reason
                    'tool_calls': len(resolution.tool_calls)
                }
            }), 200
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error processing ticket {ticket_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/process/batch', methods=['POST'])
def process_batch():
    """Process multiple tickets"""
    try:
        data = request.json
        ticket_ids = data.get('ticket_ids', [t['ticket_id'] for t in TICKETS])
        
        if not ticket_ids:
            return jsonify({
                'success': False,
                'error': 'ticket_ids list is required'
            }), 400
        
        # DEDUPLICATION: Filter out already-processed tickets
        processed_ticket_ids = {entry.get('ticket_id') for entry in audit_log}
        new_ticket_ids = [tid for tid in ticket_ids if tid not in processed_ticket_ids]
        already_processed = [tid for tid in ticket_ids if tid in processed_ticket_ids]
        
        if already_processed:
            logger.info(f"Skipping {len(already_processed)} already-processed tickets: {already_processed}")
        
        if not new_ticket_ids:
            logger.info(f"All {len(ticket_ids)} tickets already processed. Returning existing results.")
            return jsonify({
                'success': True,
                'data': {
                    'total_processed': 0,
                    'duration_seconds': 0,
                    'note': f'All {len(ticket_ids)} tickets were already processed. No new processing needed.',
                    'already_processed_count': len(already_processed)
                }
            }), 200
        
        # Process tickets (sync wrapper for async function)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            start_time = datetime.now()
            resolutions = loop.run_until_complete(
                agent.process_tickets_concurrently(new_ticket_ids)
            )
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Add each resolution to audit log with full ticket details
            for resolution in resolutions:
                ticket = get_ticket(resolution.ticket_id)
                if ticket:
                    audit_entry = {
                        'ticket_id': resolution.ticket_id,
                        'customer_email': ticket.get('customer_email', ''),
                        'subject': ticket.get('subject', ''),
                        'body': ticket.get('body', ''),
                        'source': ticket.get('source', ''),
                        'created_at': ticket.get('created_at', ''),
                        'action': resolution.action.value,
                        'reasoning': resolution.reasoning,
                        'confidence_score': resolution.confidence_score,
                        'accuracy_factors': resolution.accuracy_factors,  # NEW: Include accuracy breakdown
                        'processing_time_ms': int((resolution.end_time - resolution.start_time).total_seconds() * 1000) if hasattr(resolution, 'end_time') else 0,
                        'tool_calls': [
                            {
                                'name': tool_call.name,
                                'params': tool_call.params,
                                'result': tool_call.result,
                                'timestamp': tool_call.timestamp.isoformat() if hasattr(tool_call.timestamp, 'isoformat') else str(tool_call.timestamp),
                                'duration_ms': tool_call.duration_ms,
                                'error': tool_call.error,
                                'error_type': tool_call.error_type if hasattr(tool_call, 'error_type') else None,
                                'retry_count': tool_call.retry_count if hasattr(tool_call, 'retry_count') else 0
                            }
                            for tool_call in resolution.tool_calls
                        ],
                        'ui_interaction': f"User clicked 'Process All At Once' at {start_time.isoformat()}. UI displayed ticket {resolution.ticket_id} in processing state with spinner animation.",
                        'processed_at': datetime.now().isoformat()
                    }
                    audit_log.append(audit_entry)
                
                # Store result
                processing_results[resolution.ticket_id] = {
                    'ticket_id': resolution.ticket_id,
                    'action': resolution.action.value,
                    'confidence_score': resolution.confidence_score,
                    'tool_calls': len(resolution.tool_calls)
                }
            
            # Save audit log to file
            save_audit_log_to_file()
            
            # Store results summary
            results_summary = {
                'total_processed': len(resolutions),
                'duration_seconds': duration,
                'average_time_per_ticket': duration / len(resolutions) if resolutions else 0,
                'by_action': {},
                'confidence_stats': {
                    'average': sum(r.confidence_score for r in resolutions) / len(resolutions) if resolutions else 0,
                    'min': min(r.confidence_score for r in resolutions) if resolutions else 0,
                    'max': max(r.confidence_score for r in resolutions) if resolutions else 0,
                    'high_confidence_count': sum(1 for r in resolutions if r.confidence_score > 0.90),
                    'low_confidence_count': sum(1 for r in resolutions if r.confidence_score < 0.70)
                },
                'tool_call_stats': {
                    'total_calls': sum(len(r.tool_calls) for r in resolutions),
                    'average_per_ticket': sum(len(r.tool_calls) for r in resolutions) / len(resolutions) if resolutions else 0
                },
                'timestamp': datetime.now().isoformat(),
                'note': f'Processed {len(new_ticket_ids)} new tickets. {len(already_processed)} were already processed.'
            }
            
            # Count by action
            for resolution in resolutions:
                action = resolution.action.value
                results_summary['by_action'][action] = results_summary['by_action'].get(action, 0) + 1
            
            return jsonify({
                'success': True,
                'data': results_summary
            }), 200
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error processing batch: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== RESULTS ENDPOINTS ====================

@app.route('/api/results/<ticket_id>', methods=['GET'])
def get_result(ticket_id):
    """Get processing result for a ticket"""
    try:
        if ticket_id not in processing_results:
            return jsonify({
                'success': False,
                'error': f'No results for ticket {ticket_id}'
            }), 404
        
        return jsonify({
            'success': True,
            'data': processing_results[ticket_id]
        }), 200
    except Exception as e:
        logger.error(f"Error fetching result: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/results', methods=['GET'])
def get_all_results():
    """Get all processing results"""
    try:
        return jsonify({
            'success': True,
            'data': {
                'results': list(processing_results.values()),
                'total': len(processing_results)
            }
        }), 200
    except Exception as e:
        logger.error(f"Error fetching results: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== AUDIT LOG ENDPOINTS ====================

@app.route('/api/audit-log', methods=['GET'])
def get_audit_log():
    """Get audit log"""
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Paginate
        start = (page - 1) * per_page
        end = start + per_page
        
        paginated_log = audit_log[start:end]
        
        return jsonify({
            'success': True,
            'data': {
                'logs': paginated_log,
                'total': len(audit_log),
                'page': page,
                'per_page': per_page,
                'total_pages': (len(audit_log) + per_page - 1) // per_page
            }
        }), 200
    except Exception as e:
        logger.error(f"Error fetching audit log: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== HEALTH & STATS ENDPOINTS ====================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'data': {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'processed_tickets': len(processing_results),
            'audit_log_entries': len(audit_log)
        }
    }), 200


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics"""
    try:
        if not processing_results:
            return jsonify({
                'success': True,
                'data': {
                    'total_processed': 0,
                    'message': 'No tickets processed yet'
                }
            }), 200
        
        results = list(processing_results.values())
        
        # Count by action
        action_counts = {}
        for result in results:
            action = result['action']
            action_counts[action] = action_counts.get(action, 0) + 1
        
        # Calculate confidence stats
        confidences = [r['confidence_score'] for r in results]
        
        stats = {
            'total_processed': len(results),
            'by_action': action_counts,
            'confidence': {
                'average': sum(confidences) / len(confidences),
                'min': min(confidences),
                'max': max(confidences),
                'high_count': sum(1 for c in confidences if c > 0.90),
                'low_count': sum(1 for c in confidences if c < 0.70)
            },
            'tool_calls': {
                'total': sum(r['tool_calls'] for r in results),
                'average': sum(r['tool_calls'] for r in results) / len(results)
            }
        }
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
    except Exception as e:
        logger.error(f"Error calculating stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== FRONTEND SERVING ====================

@app.route('/', methods=['GET'])
def serve_frontend_root():
    """Serve frontend at root path"""
    return send_from_directory('frontend', 'index.html')


@app.route('/frontend/', methods=['GET'])
def serve_frontend():
    """Serve frontend dashboard"""
    return send_from_directory('frontend', 'index.html')


@app.route('/frontend/<path:filename>', methods=['GET'])
def serve_frontend_static(filename):
    """Serve frontend static files (CSS, JS)"""
    return send_from_directory('frontend', filename)


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


if __name__ == '__main__':
    logger.info("Starting API server on http://localhost:5000")
    logger.info("Frontend available at http://localhost:5000/frontend/")
    app.run(debug=True, host='0.0.0.0', port=5000)

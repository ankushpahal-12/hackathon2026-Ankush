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
        
        # Process ticket (sync wrapper for async function)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            resolution = loop.run_until_complete(agent.process_ticket(ticket_id))
            
            # Store result
            processing_results[ticket_id] = {
                'ticket_id': ticket_id,
                'action': resolution.action.value,
                'confidence_score': resolution.confidence_score,
                'reasoning': resolution.reasoning,
                'tool_calls': len(resolution.tool_calls),
                'timestamp': datetime.now().isoformat()
            }
            
            # Log to audit trail
            audit_log.append({
                'ticket_id': ticket_id,
                'action': 'PROCESS',
                'result': processing_results[ticket_id],
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify({
                'success': True,
                'data': {
                    'ticket_id': ticket_id,
                    'action': resolution.action.value,
                    'confidence': resolution.confidence_score,
                    'reasoning': resolution.reasoning,
                    'tool_calls': len(resolution.tool_calls)
                }
            }), 200
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error processing ticket: {str(e)}")
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
        
        # Process tickets (sync wrapper for async function)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            start_time = datetime.now()
            resolutions = loop.run_until_complete(
                agent.process_tickets_concurrently(ticket_ids)
            )
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Store results
            results_summary = {
                'total_processed': len(resolutions),
                'duration_seconds': duration,
                'average_time_per_ticket': duration / len(resolutions),
                'by_action': {},
                'confidence_stats': {
                    'average': sum(r.confidence_score for r in resolutions) / len(resolutions),
                    'min': min(r.confidence_score for r in resolutions),
                    'max': max(r.confidence_score for r in resolutions),
                    'high_confidence_count': sum(1 for r in resolutions if r.confidence_score > 0.90),
                    'low_confidence_count': sum(1 for r in resolutions if r.confidence_score < 0.70)
                },
                'tool_call_stats': {
                    'total_calls': sum(len(r.tool_calls) for r in resolutions),
                    'average_per_ticket': sum(len(r.tool_calls) for r in resolutions) / len(resolutions)
                },
                'timestamp': datetime.now().isoformat()
            }
            
            # Count by action
            for resolution in resolutions:
                action = resolution.action.value
                results_summary['by_action'][action] = results_summary['by_action'].get(action, 0) + 1
            
            # Store individual results
            for resolution in resolutions:
                processing_results[resolution.ticket_id] = {
                    'ticket_id': resolution.ticket_id,
                    'action': resolution.action.value,
                    'confidence_score': resolution.confidence_score,
                    'tool_calls': len(resolution.tool_calls)
                }
            
            # Log to audit trail
            audit_log.append({
                'event': 'BATCH_PROCESS',
                'summary': results_summary,
                'timestamp': datetime.now().isoformat()
            })
            
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

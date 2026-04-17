// ==================== CONFIGURATION ====================
const API_BASE_URL = 'http://localhost:5000/api';
const REFRESH_INTERVAL = 5000; // 5 seconds

// ==================== STATE MANAGEMENT ====================
const state = {
    tickets: [],
    results: {},
    stats: {},
    auditLog: [],
    isProcessing: false,
    filters: {
        search: '',
        status: ''
    }
};
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Frontend initialized');
    
    // Load initial data
    await loadTickets();
    await loadResults();
    await updateStats();
    
    // Set up event listeners
    setupEventListeners();
    
    // Check health
    await checkHealth();
    
    // Set auto-refresh
    setInterval(async () => {
        await loadResults();
        await updateStats();
    }, REFRESH_INTERVAL);
});

// ==================== EVENT LISTENERS ====================
function setupEventListeners() {
    // Load all tickets
    document.getElementById('load-all-btn').addEventListener('click', async () => {
        await loadTickets();
        showAlert('All tickets loaded successfully!', 'success');
    });
    
    // Process all tickets
    document.getElementById('process-all-btn').addEventListener('click', processAllTickets);
    
    // Process one by one
    document.getElementById('process-one-by-one-btn').addEventListener('click', processOneByOne);
    
    // Refresh stats
    document.getElementById('refresh-stats-btn').addEventListener('click', updateStats);
    
    // Search and filter
    document.getElementById('ticket-search').addEventListener('input', filterTickets);
    document.getElementById('ticket-filter').addEventListener('change', filterTickets);
}

// ==================== API FUNCTIONS ====================

/**
 * Load all tickets from API
 */
async function loadTickets() {
    try {
        const response = await fetch(`${API_BASE_URL}/tickets`);
        const data = await response.json();
        
        if (data.success) {
            state.tickets = data.data.tickets;
            renderTickets();
        }
    } catch (error) {
        console.error('Error loading tickets:', error);
        showAlert('Error loading tickets', 'danger');
    }
}

/**
 * Load results from API
 */
async function loadResults() {
    try {
        const response = await fetch(`${API_BASE_URL}/results`);
        const data = await response.json();
        
        if (data.success) {
            state.results = {};
            data.data.results.forEach(result => {
                state.results[result.ticket_id] = result;
            });
            renderResults();
        }
    } catch (error) {
        console.error('Error loading results:', error);
    }
}

/**
 * Process a single ticket
 */
async function processSingleTicket(ticketId) {
    try {
        showLoadingModal(`Processing ${ticketId}...`, 'Please wait while the agent processes this ticket');
        
        const response = await fetch(`${API_BASE_URL}/process/ticket`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ ticket_id: ticketId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(`Ticket ${ticketId} processed successfully!`, 'success');
            
            // Update state
            state.results[ticketId] = {
                ticket_id: ticketId,
                action: data.data.action,
                confidence_score: data.data.confidence,
                tool_calls: data.data.tool_calls
            };
            
            renderTickets();  // Re-render to show updated status
            renderResults();
            await updateStats();
        } else {
            showAlert(`Error processing ticket: ${data.error}`, 'danger');
        }
    } catch (error) {
        console.error('Error processing ticket:', error);
        showAlert('Error processing ticket', 'danger');
    } finally {
        hideLoadingModal();
    }
}

/**
 * Process all tickets
 */
async function processAllTickets() {
    if (state.isProcessing) {
        showAlert('Processing already in progress', 'warning');
        return;
    }
    
    try {
        state.isProcessing = true;
        showLoadingModal('Processing All Tickets', 'This may take a few moments...');
        
        const response = await fetch(`${API_BASE_URL}/process/batch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                ticket_ids: state.tickets.map(t => t.ticket_id)
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const stats = data.data;
            showAlert(
                `✓ Processed ${stats.total_processed} tickets in ${stats.duration_seconds.toFixed(2)}s`,
                'success'
            );
            
            // Reload results and update stats
            await loadResults();
            renderTickets();  // Re-render tickets to show updated status
            await updateStats();
        } else {
            showAlert(`Error: ${data.error}`, 'danger');
        }
    } catch (error) {
        console.error('Error processing tickets:', error);
        showAlert('Error processing tickets', 'danger');
    } finally {
        state.isProcessing = false;
        hideLoadingModal();
    }
}

/**
 * Process tickets one by one sequentially
 */
async function processOneByOne() {
    if (state.isProcessing) {
        showAlert('Processing already in progress', 'warning');
        return;
    }
    
    if (state.tickets.length === 0) {
        showAlert('No tickets to process. Load tickets first.', 'warning');
        return;
    }
    
    try {
        state.isProcessing = true;
        const totalTickets = state.tickets.length;
        let processedCount = 0;
        
        for (const ticket of state.tickets) {
            if (!state.isProcessing) break; // Allow user to cancel
            
            processedCount++;
            showLoadingModal(
                `Processing Tickets One by One`,
                `Processing ${ticket.ticket_id} (${processedCount}/${totalTickets})...`
            );
            
            try {
                const response = await fetch(`${API_BASE_URL}/process/ticket`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ ticket_id: ticket.ticket_id })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Update state with result
                    state.results[ticket.ticket_id] = {
                        ticket_id: ticket.ticket_id,
                        action: data.data.action,
                        confidence_score: data.data.confidence,
                        tool_calls: data.data.tool_calls
                    };
                    
                    console.log(`✓ Processed ${ticket.ticket_id}`);
                } else {
                    console.error(`✗ Error processing ${ticket.ticket_id}: ${data.error}`);
                }
            } catch (error) {
                console.error(`Error processing ticket ${ticket.ticket_id}:`, error);
            }
            
            // Small delay between processing to avoid overwhelming the server
            await new Promise(resolve => setTimeout(resolve, 500));
        }
        
        // Final update
        await loadResults();
        renderTickets();
        await updateStats();
        
        showAlert(
            `✓ Processed ${processedCount} tickets one by one!`,
            'success'
        );
    } catch (error) {
        console.error('Error in one-by-one processing:', error);
        showAlert('Error processing tickets', 'danger');
    } finally {
        state.isProcessing = false;
        hideLoadingModal();
    }
}

/**
 * Update statistics
 */
async function updateStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/stats`);
        const data = await response.json();
        
        if (data.success) {
            state.stats = data.data;
            renderStats();
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

/**
 * Check API health
 */
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        if (data.success) {
            updateHealthStatus(true);
        }
    } catch (error) {
        console.error('Health check failed:', error);
        updateHealthStatus(false);
    }
}

// ==================== RENDERING FUNCTIONS ====================

/**
 * Render tickets grid
 */
function renderTickets() {
    const container = document.getElementById('tickets-container');
    const filtered = filterTicketsList();
    
    if (filtered.length === 0) {
        container.innerHTML = '<div class="col-12"><p class="text-muted text-center py-4">No tickets found</p></div>';
        return;
    }
    
    container.innerHTML = filtered.map(ticket => {
        const result = state.results[ticket.ticket_id];
        const isProcessed = !!result;
        
        return `
            <div class="col-md-6 col-lg-4">
                <div class="ticket-card ${isProcessed ? 'processed' : ''}">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <span class="ticket-id">${ticket.ticket_id}</span>
                        <span class="ticket-status ${isProcessed ? 'success' : 'pending'}">
                            ${isProcessed ? '✓ Processed' : 'Pending'}
                        </span>
                    </div>
                    
                    <p class="text-muted mb-2" style="font-size: 0.9rem;">
                        <strong>Customer:</strong> ${ticket.customer_email}
                    </p>
                    
                    <p class="text-muted mb-3" style="font-size: 0.9rem;">
                        <strong>Issue:</strong> ${ticket.subject.substring(0, 50)}...
                    </p>
                    
                    ${isProcessed ? `
                        <div class="mb-3 pb-3 border-bottom">
                            <div class="d-flex justify-content-between mb-2">
                                <span style="font-size: 0.85rem;">Action</span>
                                <strong style="font-size: 0.85rem;">${result.action}</strong>
                            </div>
                            <div class="d-flex justify-content-between">
                                <span style="font-size: 0.85rem;">Confidence</span>
                                <strong style="font-size: 0.85rem;">${(result.confidence_score * 100).toFixed(0)}%</strong>
                            </div>
                        </div>
                    ` : ''}
                    
                    <button class="btn btn-sm btn-primary w-100" onclick="processSingleTicket('${ticket.ticket_id}')">
                        <i class="fas fa-play"></i> Process
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Render results table
 */
function renderResults() {
    const tbody = document.getElementById('results-table');
    const results = Object.values(state.results);
    
    if (results.length === 0) {
        tbody.innerHTML = `
            <tr class="text-center text-muted">
                <td colspan="6" class="py-4">No results yet. Process tickets to see results.</td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = results.map(result => {
        const actionClass = {
            'approve_refund': 'success',
            'deny': 'danger',
            'escalate': 'warning'
        }[result.action] || 'secondary';
        
        return `
            <tr class="fade-in">
                <td>
                    <strong>${result.ticket_id}</strong>
                </td>
                <td>
                    <span class="badge bg-${actionClass}">
                        ${result.action.replace('_', ' ').toUpperCase()}
                    </span>
                </td>
                <td>
                    <div class="d-flex align-items-center">
                        <div style="width: 60px;">
                            <div class="progress" style="height: 6px;">
                                <div class="progress-bar" style="width: ${result.confidence_score * 100}%"></div>
                            </div>
                        </div>
                        <span class="ms-2" style="font-size: 0.9rem;">
                            ${(result.confidence_score * 100).toFixed(0)}%
                        </span>
                    </div>
                </td>
                <td>
                    <span class="badge bg-info">${result.tool_calls}</span>
                </td>
                <td>
                    <span class="badge bg-success"><i class="fas fa-check-circle"></i> Done</span>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="viewDetails('${result.ticket_id}')">
                        <i class="fas fa-eye"></i> View
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

/**
 * Render statistics
 */
function renderStats() {
    const stats = state.stats;
    
    if (!stats.total_processed || stats.total_processed === 0) {
        document.getElementById('stat-total').textContent = '0';
        document.getElementById('stat-approved').textContent = '0';
        document.getElementById('stat-denied').textContent = '0';
        document.getElementById('stat-escalated').textContent = '0';
        return;
    }
    
    // Update KPI cards
    document.getElementById('stat-total').textContent = stats.total_processed;
    document.getElementById('stat-approved').textContent = stats.by_action['approve_refund'] || 0;
    document.getElementById('stat-denied').textContent = stats.by_action['deny'] || 0;
    document.getElementById('stat-escalated').textContent = stats.by_action['escalate'] || 0;
    
    // Update confidence stats
    document.getElementById('conf-avg').textContent = stats.confidence.average.toFixed(2);
    document.getElementById('conf-avg-bar').style.width = (stats.confidence.average * 100) + '%';
    document.getElementById('conf-high').textContent = stats.confidence.high_count;
    document.getElementById('conf-low').textContent = stats.confidence.low_count;
    
    // Update tool stats
    document.getElementById('tools-total').textContent = stats.tool_calls.total;
    document.getElementById('tools-avg').textContent = stats.tool_calls.average.toFixed(1);
}

/**
 * Filter tickets list based on search and filter
 */
function filterTicketsList() {
    const search = state.filters.search.toLowerCase();
    const status = state.filters.status;
    
    return state.tickets.filter(ticket => {
        // Search filter
        const matchSearch = !search || 
            ticket.ticket_id.toLowerCase().includes(search) ||
            ticket.customer_email.toLowerCase().includes(search) ||
            ticket.subject.toLowerCase().includes(search);
        
        // Status filter
        const isProcessed = !!state.results[ticket.ticket_id];
        const matchStatus = !status || 
            (status === 'processed' && isProcessed) ||
            (status === 'pending' && !isProcessed);
        
        return matchSearch && matchStatus;
    });
}

/**
 * Apply ticket filters
 */
function filterTickets() {
    state.filters.search = document.getElementById('ticket-search').value;
    state.filters.status = document.getElementById('ticket-filter').value;
    renderTickets();
}

// ==================== UI HELPER FUNCTIONS ====================

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alert-container');
    const alertId = 'alert-' + Date.now();
    
    const alertHTML = `
        <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    alertContainer.insertAdjacentHTML('beforeend', alertHTML);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const element = document.getElementById(alertId);
        if (element) {
            const alert = new bootstrap.Alert(element);
            alert.close();
        }
    }, 5000);
}

/**
 * Show loading modal
 */
function showLoadingModal(title, details) {
    document.getElementById('loading-text').textContent = title;
    document.getElementById('loading-details').textContent = details;
    
    const modal = new bootstrap.Modal(document.getElementById('loadingModal'));
    modal.show();
}

/**
 * Hide loading modal
 */
function hideLoadingModal() {
    const modal = bootstrap.Modal.getInstance(document.getElementById('loadingModal'));
    if (modal) {
        modal.hide();
    }
}

/**
 * Update health status
 */
function updateHealthStatus(isHealthy) {
    const statusElement = document.getElementById('health-status');
    if (isHealthy) {
        statusElement.className = 'badge bg-success ms-2';
        statusElement.innerHTML = '<i class="fas fa-circle"></i> Connected';
    } else {
        statusElement.className = 'badge bg-danger ms-2';
        statusElement.innerHTML = '<i class="fas fa-circle"></i> Disconnected';
    }
}

/**
 * View ticket details
 */
function viewDetails(ticketId) {
    const ticket = state.tickets.find(t => t.ticket_id === ticketId);
    const result = state.results[ticketId];
    
    if (!ticket) {
        showAlert('Ticket not found', 'danger');
        return;
    }
    
    const details = `
        <strong>${ticket.ticket_id}</strong><br>
        <small class="text-muted">
            ${ticket.customer_email}<br>
            ${ticket.subject}
        </small>
        ${result ? `
            <hr>
            <div>
                <strong>Action:</strong> ${result.action}<br>
                <strong>Confidence:</strong> ${(result.confidence_score * 100).toFixed(0)}%<br>
                <strong>Tool Calls:</strong> ${result.tool_calls}
            </div>
        ` : '<hr><em class="text-muted">Not processed yet</em>'}
    `;
    
    alert(details);
}

// ==================== UTILITY FUNCTIONS ====================

/**
 * Format date
 */
function formatDate(isoString) {
    return new Date(isoString).toLocaleString();
}

/**
 * Get action badge class
 */
function getActionBadgeClass(action) {
    const classMap = {
        'approve_refund': 'success',
        'deny': 'danger',
        'escalate': 'warning'
    };
    return classMap[action] || 'secondary';
}

// ==================== KEYBOARD SHORTCUTS ====================
document.addEventListener('keydown', (event) => {
    // Ctrl+Shift+P to process all tickets
    if (event.ctrlKey && event.shiftKey && event.code === 'KeyP') {
        event.preventDefault();
        processAllTickets();
    }
    
    // Ctrl+R to refresh
    if (event.ctrlKey && event.code === 'KeyR') {
        event.preventDefault();
        updateStats();
    }
});

console.log('✓ Frontend ready');

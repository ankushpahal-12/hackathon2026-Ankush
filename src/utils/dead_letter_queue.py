"""
Dead-Letter Queue System
Failed tickets that can't be auto-resolved don't disappear - they're logged and tracked
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DeadLetterEntry:
    """Entry in the dead-letter queue"""
    ticket_id: str
    reason: str
    error_type: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    retry_count: int = 0
    max_retries: int = 2
    last_error: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self):
        return asdict(self)
    
    def is_retryable(self) -> bool:
        """Check if this entry should be retried"""
        return self.retry_count < self.max_retries
    
    def increment_retry(self):
        """Increment retry count"""
        self.retry_count += 1


class DeadLetterQueue:
    """
    PRODUCTION FEATURE: Dead-letter queue for failed tickets
    Failed tickets don't disappear - they're logged for analysis and retry
    """
    
    def __init__(self, filepath: Optional[str] = None):
        self.filepath = filepath or 'output/dead_letter_queue.json'
        self.queue: List[DeadLetterEntry] = []
        self._load()
    
    def add(
        self,
        ticket_id: str,
        reason: str,
        error_type: str,
        last_error: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        max_retries: int = 2
    ):
        """
        Add a failed ticket to the dead-letter queue
        
        Args:
            ticket_id: ID of the failed ticket
            reason: Why it failed (e.g., "Max tool retries exceeded")
            error_type: Type of error (e.g., "ToolTimeout")
            last_error: The last error message
            context: Additional context (customer info, order details, etc)
            max_retries: Maximum number of retries to attempt
        """
        entry = DeadLetterEntry(
            ticket_id=ticket_id,
            reason=reason,
            error_type=error_type,
            last_error=last_error,
            context=context or {},
            max_retries=max_retries
        )
        
        self.queue.append(entry)
        logger.warning(f"[DLQ] Added {ticket_id}: {reason}")
    
    def get_retryable(self) -> List[DeadLetterEntry]:
        """Get all entries that should be retried"""
        return [entry for entry in self.queue if entry.is_retryable()]
    
    def get_by_ticket_id(self, ticket_id: str) -> Optional[DeadLetterEntry]:
        """Retrieve a specific dead-letter entry"""
        return next((e for e in self.queue if e.ticket_id == ticket_id), None)
    
    def save(self):
        """Save dead-letter queue to disk"""
        Path(self.filepath).parent.mkdir(parents=True, exist_ok=True)
        
        dlq_data = {
            "generated_at": datetime.now().isoformat(),
            "total_entries": len(self.queue),
            "retryable_count": len(self.get_retryable()),
            "entries": [entry.to_dict() for entry in self.queue]
        }
        
        with open(self.filepath, 'w') as f:
            json.dump(dlq_data, f, indent=2)
        
        logger.info(f"Dead-letter queue saved: {self.filepath} ({len(self.queue)} entries)")
    
    def _load(self):
        """Load existing dead-letter queue from disk"""
        if Path(self.filepath).exists():
            try:
                with open(self.filepath, 'r') as f:
                    data = json.load(f)
                    for entry_data in data.get('entries', []):
                        entry = DeadLetterEntry(**entry_data)
                        self.queue.append(entry)
                logger.info(f"Loaded {len(self.queue)} entries from dead-letter queue")
            except Exception as e:
                logger.warning(f"Could not load dead-letter queue: {e}")
    
    def summary(self) -> Dict[str, Any]:
        """Get summary of dead-letter queue"""
        error_types = {}
        for entry in self.queue:
            error_types[entry.error_type] = error_types.get(entry.error_type, 0) + 1
        
        return {
            "total_entries": len(self.queue),
            "retryable_entries": len(self.get_retryable()),
            "error_types": error_types,
            "entries": [entry.to_dict() for entry in self.queue]
        }

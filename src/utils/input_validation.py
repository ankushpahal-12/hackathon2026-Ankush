"""
Enhanced Input Validation and Sanitization
Provides comprehensive input validation for all agent operations
"""

import re
import logging
from typing import Any, Dict, List, Optional, Type
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when input validation fails"""
    pass


class InputValidator:
    """
    Validates all inputs to agent operations
    Prevents injection attacks and malformed data
    """
    
    # Regex patterns for validation
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    ORDER_ID_PATTERN = re.compile(r'^ORD-\d{4,6}$')
    TICKET_ID_PATTERN = re.compile(r'^TKT-\d{3,5}$|^TICKET-[A-Z0-9]{4,}$')
    PRODUCT_ID_PATTERN = re.compile(r'^P\d{3,4}$')
    AMOUNT_PATTERN = re.compile(r'^\d+(\.\d{2})?$')
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate and sanitize email"""
        if not email or not isinstance(email, str):
            raise ValidationError("Email must be a non-empty string")
        
        email = email.strip().lower()
        
        if len(email) > 254:
            raise ValidationError("Email too long (max 254 chars)")
        
        if not InputValidator.EMAIL_PATTERN.match(email):
            raise ValidationError(f"Invalid email format: {email}")
        
        return email
    
    @staticmethod
    def validate_order_id(order_id: str) -> str:
        """Validate order ID format"""
        if not order_id or not isinstance(order_id, str):
            raise ValidationError("Order ID must be a non-empty string")
        
        order_id = order_id.strip().upper()
        
        if len(order_id) > 20:
            raise ValidationError("Order ID too long")
        
        if not InputValidator.ORDER_ID_PATTERN.match(order_id):
            raise ValidationError(f"Invalid order ID format: {order_id}. Expected ORD-XXXX")
        
        return order_id
    
    @staticmethod
    def validate_ticket_id(ticket_id: str) -> str:
        """Validate ticket ID format"""
        if not ticket_id or not isinstance(ticket_id, str):
            raise ValidationError("Ticket ID must be a non-empty string")
        
        ticket_id = ticket_id.strip().upper()
        
        if len(ticket_id) > 20:
            raise ValidationError("Ticket ID too long")
        
        if not InputValidator.TICKET_ID_PATTERN.match(ticket_id):
            raise ValidationError(f"Invalid ticket ID format: {ticket_id}")
        
        return ticket_id
    
    @staticmethod
    def validate_product_id(product_id: str) -> str:
        """Validate product ID format"""
        if not product_id or not isinstance(product_id, str):
            raise ValidationError("Product ID must be a non-empty string")
        
        product_id = product_id.strip().upper()
        
        if len(product_id) > 10:
            raise ValidationError("Product ID too long")
        
        if not InputValidator.PRODUCT_ID_PATTERN.match(product_id):
            raise ValidationError(f"Invalid product ID format: {product_id}. Expected PXXX")
        
        return product_id
    
    @staticmethod
    def validate_amount(amount: float) -> float:
        """Validate monetary amount"""
        if not isinstance(amount, (int, float)):
            raise ValidationError("Amount must be numeric")
        
        if amount < 0:
            raise ValidationError("Amount cannot be negative")
        
        if amount > 1_000_000:
            raise ValidationError("Amount exceeds maximum allowed")
        
        return round(float(amount), 2)
    
    @staticmethod
    def validate_message(message: str, max_length: int = 5000) -> str:
        """Validate customer message"""
        if not isinstance(message, str):
            raise ValidationError("Message must be a string")
        
        if len(message) == 0:
            raise ValidationError("Message cannot be empty")
        
        if len(message) > max_length:
            raise ValidationError(f"Message too long (max {max_length} chars)")
        
        # Sanitize: remove control characters but allow newlines
        sanitized = ''.join(char for char in message if ord(char) >= 32 or char in '\n\r\t')
        
        return sanitized.strip()
    
    @staticmethod
    def validate_query(query: str, max_length: int = 500) -> str:
        """Validate search query"""
        if not isinstance(query, str):
            raise ValidationError("Query must be a string")
        
        if len(query) == 0:
            raise ValidationError("Query cannot be empty")
        
        if len(query) > max_length:
            raise ValidationError(f"Query too long (max {max_length} chars)")
        
        # Allow only alphanumeric, spaces, and basic punctuation
        if not re.match(r'^[a-zA-Z0-9\s\-\(\)\.]+$', query):
            raise ValidationError("Query contains invalid characters")
        
        return query.strip()
    
    @staticmethod
    def validate_priority(priority: str) -> str:
        """Validate priority level"""
        valid_priorities = ['low', 'medium', 'high', 'critical']
        
        if not isinstance(priority, str):
            raise ValidationError("Priority must be a string")
        
        priority = priority.strip().lower()
        
        if priority not in valid_priorities:
            raise ValidationError(f"Invalid priority. Must be one of: {', '.join(valid_priorities)}")
        
        return priority
    
    @staticmethod
    def validate_dict_required_keys(data: Dict[str, Any], required_keys: List[str]) -> None:
        """Validate that dict contains all required keys"""
        if not isinstance(data, dict):
            raise ValidationError("Data must be a dictionary")
        
        missing_keys = [key for key in required_keys if key not in data]
        
        if missing_keys:
            raise ValidationError(f"Missing required fields: {', '.join(missing_keys)}")
    
    @staticmethod
    def validate_dict_types(data: Dict[str, Any], type_map: Dict[str, Type]) -> None:
        """Validate that dict values match expected types"""
        for key, expected_type in type_map.items():
            if key not in data:
                continue
            
            if not isinstance(data[key], expected_type):
                raise ValidationError(
                    f"Field '{key}' has wrong type. Expected {expected_type.__name__}, "
                    f"got {type(data[key]).__name__}"
                )

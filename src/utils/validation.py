"""
Schema Validation for Tool Outputs
Ensures data integrity before acting on tool results
"""

from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Schema validation failed"""
    pass


class SchemaValidator:
    """Validates tool outputs against expected schemas"""
    
    SCHEMAS = {
        "get_customer": {
            "required": ["status", "data"],
            "data_required": ["customer_id", "name", "email", "tier", "total_orders"],
            "types": {
                "status": str,
                "data": dict
            }
        },
        "get_order": {
            "required": ["status", "data"],
            "data_required": ["order_id", "product_id", "total_price", "delivery_date"],
            "types": {
                "status": str,
                "data": dict
            }
        },
        "check_refund_eligibility": {
            "required": ["status", "order_id", "eligible", "reason"],
            "types": {
                "status": str,
                "order_id": str,
                "eligible": bool,
                "reason": str
            }
        },
        "issue_refund": {
            "required": ["status", "refund_id", "order_id", "amount"],
            "types": {
                "status": str,
                "refund_id": str,
                "order_id": str,
                "amount": (int, float)
            }
        },
        "send_reply": {
            "required": ["status", "ticket_id"],
            "types": {
                "status": str,
                "ticket_id": str
            }
        },
        "escalate": {
            "required": ["status", "case_id", "ticket_id"],
            "types": {
                "status": str,
                "case_id": str,
                "ticket_id": str
            }
        }
    }
    
    @staticmethod
    def validate(tool_name: str, response: Any) -> bool:
        """
        Validate tool response against schema
        
        Args:
            tool_name: Name of the tool
            response: Response data from tool
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If validation fails
        """
        if not response:
            raise ValidationError(f"Response is None or empty")
        
        if not isinstance(response, dict):
            raise ValidationError(f"Response is not a dict: {type(response)}")
        
        schema = SchemaValidator.SCHEMAS.get(tool_name)
        if not schema:
            logger.warning(f"No schema defined for {tool_name}")
            return True
        
        # Check required fields
        for field in schema.get("required", []):
            if field not in response:
                raise ValidationError(f"Missing required field: {field}")
        
        # Check types
        for field, expected_type in schema.get("types", {}).items():
            if field in response:
                if not isinstance(response[field], expected_type):
                    raise ValidationError(
                        f"Field '{field}' has wrong type. "
                        f"Expected {expected_type}, got {type(response[field])}"
                    )
        
        # Check nested data if required
        if "data_required" in schema and "data" in response:
            data = response["data"]
            if not isinstance(data, dict):
                raise ValidationError("'data' field must be a dict")
            
            for field in schema.get("data_required", []):
                if field not in data:
                    raise ValidationError(f"Missing required data field: {field}")
        
        logger.debug(f"✓ Schema validation passed for {tool_name}")
        return True

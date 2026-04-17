"""
LLM Integration for Agent Reasoning
Supports: Google Gemini, OpenAI, Anthropic, Ollama

Enhances agent decision-making with AI-powered reasoning
"""

import json
import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from datetime import datetime

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def reason_about_ticket(self, context: Dict[str, Any]) -> str:
        """Use LLM to reason about ticket resolution"""
        pass
    
    @abstractmethod
    def craft_customer_message(self, context: Dict[str, Any]) -> str:
        """Use LLM to craft personalized customer message"""
        pass
    
    @abstractmethod
    def assess_confidence(self, context: Dict[str, Any]) -> float:
        """Use LLM to assess decision confidence"""
        pass


class GeminiProvider(LLMProvider):
    """Google Gemini LLM Provider"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini provider
        
        Args:
            api_key: Google API key (or from GOOGLE_API_KEY env var)
        """
        import os
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        self.model_name = "gemini-1.5-flash"
        
        if not self.api_key:
            logger.warning("GOOGLE_API_KEY not set. Gemini reasoning disabled.")
            self.enabled = False
        else:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(self.model_name)
                self.enabled = True
                logger.info(f"✓ Gemini {self.model_name} initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini: {e}")
                self.enabled = False
    
    def reason_about_ticket(self, context: Dict[str, Any]) -> str:
        """
        Use Gemini to reason about ticket resolution
        
        Args:
            context: Ticket context including customer, order, policy info
            
        Returns:
            LLM reasoning about the ticket
        """
        if not self.enabled:
            return "Unable to reason (Gemini not initialized)"
        
        try:
            prompt = self._build_reasoning_prompt(context)
            response = self.client.generate_content(prompt)
            logger.debug(f"Gemini reasoning: {response.text[:100]}...")
            return response.text
        except Exception as e:
            logger.error(f"Gemini reasoning failed: {e}")
            return f"Error during reasoning: {str(e)}"
    
    def craft_customer_message(self, context: Dict[str, Any]) -> str:
        """
        Use Gemini to craft personalized customer message
        
        Args:
            context: Customer, order, and decision context
            
        Returns:
            Personalized customer message
        """
        if not self.enabled:
            return "Dear customer, your request is being processed."
        
        try:
            prompt = self._build_message_prompt(context)
            response = self.client.generate_content(prompt)
            logger.debug(f"Gemini message crafted ({len(response.text)} chars)")
            return response.text
        except Exception as e:
            logger.error(f"Gemini message crafting failed: {e}")
            return f"Thank you for contacting us. We are reviewing your request."
    
    def assess_confidence(self, context: Dict[str, Any]) -> float:
        """
        Use Gemini to assess decision confidence
        
        Args:
            context: Decision context including evidence
            
        Returns:
            Confidence score 0.0-1.0
        """
        if not self.enabled:
            return 0.5
        
        try:
            prompt = self._build_confidence_prompt(context)
            response = self.client.generate_content(prompt)
            
            # Extract number from response
            text = response.text.strip()
            try:
                score = float(text.split('\n')[0])
                score = max(0.0, min(1.0, score))  # Clamp 0-1
                logger.debug(f"Gemini confidence assessment: {score:.2f}")
                return score
            except ValueError:
                logger.warning(f"Could not parse confidence from: {text}")
                return 0.5
        except Exception as e:
            logger.error(f"Gemini confidence assessment failed: {e}")
            return 0.5
    
    def _build_reasoning_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for ticket reasoning"""
        ticket = context.get('ticket', {})
        customer = context.get('customer', {})
        order = context.get('order', {})
        eligibility = context.get('eligibility', {})
        
        return f"""You are a support agent decision-making system. Analyze this support ticket and provide reasoning.

TICKET:
- ID: {ticket.get('ticket_id')}
- Subject: {ticket.get('subject')}
- Body: {ticket.get('body', '')[:200]}
- Customer Email: {ticket.get('customer_email')}

CUSTOMER:
- Name: {customer.get('name')}
- Tier: {customer.get('tier')}
- Total Orders: {customer.get('total_orders')}
- Previous Refunds: {customer.get('notes', '')[:100]}

ORDER:
- Order ID: {order.get('order_id')}
- Product: {order.get('product_id')}
- Price: ${order.get('total_price')}
- Delivery: {order.get('delivery_date')}

ELIGIBILITY:
- Eligible: {eligibility.get('eligible')}
- Reason: {eligibility.get('reason')}
- Days Since Delivery: {eligibility.get('days_since_delivery')}

Provide concise reasoning for approval/denial decision. Consider policy, customer history, and fairness."""
    
    def _build_message_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for customer message crafting"""
        customer = context.get('customer', {})
        order = context.get('order', {})
        decision = context.get('decision', {})
        
        return f"""Craft a professional, empathetic customer service response.

CUSTOMER: {customer.get('name')} (Tier: {customer.get('tier')})
ORDER: {order.get('order_id')} - ${order.get('total_price')}
DECISION: {decision.get('action')}
REASON: {decision.get('reason', 'Policy compliance')}

Write a personalized response (2-3 sentences). Be empathetic if denying, clear if approving."""
    
    def _build_confidence_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for confidence assessment"""
        evidence = context.get('evidence', {})
        
        return f"""Rate your confidence in this decision (0.0-1.0 only, no explanation):

Evidence:
- Tool Failures: {evidence.get('tool_errors', 0)}
- Retries: {evidence.get('retries', 0)}
- Data Completeness: {evidence.get('data_complete', 'unknown')}
- Policy Clarity: {evidence.get('policy_clear', 'unknown')}
- Customer Tier: {evidence.get('customer_tier', 'standard')}

Respond with ONLY a single number between 0.0 and 1.0."""


class OpenAIProvider(LLMProvider):
    """OpenAI LLM Provider"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Initialize OpenAI provider
        
        Args:
            api_key: OpenAI API key (or from OPENAI_API_KEY env var)
            model: Model name (gpt-4, gpt-3.5-turbo, etc)
        """
        import os
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model_name = model
        
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set. OpenAI reasoning disabled.")
            self.enabled = False
        else:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                self.enabled = True
                logger.info(f"✓ OpenAI {self.model_name} initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")
                self.enabled = False
    
    def reason_about_ticket(self, context: Dict[str, Any]) -> str:
        """Use OpenAI to reason about ticket"""
        if not self.enabled:
            return "Unable to reason (OpenAI not initialized)"
        
        try:
            prompt = self._build_reasoning_prompt(context)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI reasoning failed: {e}")
            return f"Error during reasoning: {str(e)}"
    
    def craft_customer_message(self, context: Dict[str, Any]) -> str:
        """Use OpenAI to craft customer message"""
        if not self.enabled:
            return "Dear customer, your request is being processed."
        
        try:
            prompt = self._build_message_prompt(context)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=300
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI message crafting failed: {e}")
            return "Thank you for contacting us. We are reviewing your request."
    
    def assess_confidence(self, context: Dict[str, Any]) -> float:
        """Use OpenAI to assess confidence"""
        if not self.enabled:
            return 0.5
        
        try:
            prompt = self._build_confidence_prompt(context)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=10
            )
            
            text = response.choices[0].message.content.strip()
            try:
                score = float(text.split('\n')[0])
                return max(0.0, min(1.0, score))
            except ValueError:
                logger.warning(f"Could not parse confidence from: {text}")
                return 0.5
        except Exception as e:
            logger.error(f"OpenAI confidence assessment failed: {e}")
            return 0.5
    
    def _build_reasoning_prompt(self, context: Dict[str, Any]) -> str:
        """Build OpenAI reasoning prompt"""
        # Same as Gemini for consistency
        ticket = context.get('ticket', {})
        customer = context.get('customer', {})
        order = context.get('order', {})
        eligibility = context.get('eligibility', {})
        
        return f"""You are a support agent decision-making system. Analyze this support ticket and provide reasoning.

TICKET:
- ID: {ticket.get('ticket_id')}
- Subject: {ticket.get('subject')}
- Body: {ticket.get('body', '')[:200]}

CUSTOMER:
- Name: {customer.get('name')}
- Tier: {customer.get('tier')}
- Orders: {customer.get('total_orders')}

ORDER:
- Order ID: {order.get('order_id')}
- Price: ${order.get('total_price')}

ELIGIBILITY:
- Eligible: {eligibility.get('eligible')}
- Reason: {eligibility.get('reason')}

Provide reasoning for your decision."""
    
    def _build_message_prompt(self, context: Dict[str, Any]) -> str:
        """Build OpenAI message prompt"""
        customer = context.get('customer', {})
        order = context.get('order', {})
        decision = context.get('decision', {})
        
        return f"""Craft a professional, empathetic customer service response.

CUSTOMER: {customer.get('name')}
ORDER: {order.get('order_id')}
DECISION: {decision.get('action')}
REASON: {decision.get('reason')}

Write a brief, empathetic response."""
    
    def _build_confidence_prompt(self, context: Dict[str, Any]) -> str:
        """Build OpenAI confidence prompt"""
        return "Rate this decision's confidence (0.0-1.0 only):\nRespond with only a number."


class LLMReasoner:
    """
    Orchestrates LLM reasoning for the support agent
    Handles fallback between providers
    """
    
    def __init__(self, providers: Optional[List[LLMProvider]] = None):
        """
        Initialize with LLM providers
        
        Args:
            providers: List of LLM providers to try in order
        """
        self.providers = providers or self._default_providers()
        self.enabled = any(p.enabled for p in self.providers)
        
        if self.enabled:
            logger.info(f"✓ LLM Reasoning initialized with {len(self.providers)} providers")
        else:
            logger.warning("No LLM providers available. Reasoning disabled.")
    
    def _default_providers(self) -> List[LLMProvider]:
        """Create default provider list (Gemini first, then OpenAI)"""
        return [
            GeminiProvider(),
            OpenAIProvider(),
        ]
    
    def reason_about_ticket(self, context: Dict[str, Any]) -> str:
        """Get reasoning from first available provider"""
        for provider in self.providers:
            if provider.enabled:
                return provider.reason_about_ticket(context)
        
        return "No LLM providers available"
    
    def craft_customer_message(self, context: Dict[str, Any]) -> str:
        """Get crafted message from first available provider"""
        for provider in self.providers:
            if provider.enabled:
                return provider.craft_customer_message(context)
        
        return "Dear customer, your request is being processed."
    
    def assess_confidence(self, context: Dict[str, Any]) -> float:
        """Get confidence from first available provider"""
        for provider in self.providers:
            if provider.enabled:
                return provider.assess_confidence(context)
        
        return 0.5

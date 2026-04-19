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
    
    @abstractmethod
    def generate_decision_reason(self, context: Dict[str, Any]) -> str:
        """Use LLM to generate a human-readable reason for the decision"""
        pass
    
    @abstractmethod
    def analyze_query_with_knowledge_base(self, 
                                         customer_query: str, 
                                         knowledge_base: str,
                                         customer_info: Dict[str, Any],
                                         order_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze customer query against knowledge base with LLM intelligence
        
        Args:
            customer_query: The customer's ticket/request text
            knowledge_base: Company policies and guidelines
            customer_info: Customer profile (tier, history, etc)
            order_info: Order details
            
        Returns:
            {
                'decision': 'APPROVE'|'DENY'|'ESCALATE',
                'reason': str,
                'confidence': float (0.0-1.0),
                'policy_match': str
            }
        """
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
    
    def generate_decision_reason(self, context: Dict[str, Any]) -> str:
        """
        Use Gemini to generate human-readable reason for decision
        
        Args:
            context: Decision context including action, factors
            
        Returns:
            Human-readable reason for the decision
        """
        if not self.enabled:
            return "Decision made based on policy compliance."
        
        try:
            prompt = self._build_decision_reason_prompt(context)
            response = self.client.generate_content(prompt)
            logger.debug(f"Gemini decision reason: {response.text[:100]}...")
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini decision reason generation failed: {e}")
            return "Decision made based on policy compliance."
    
    def _build_decision_reason_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for generating decision reason"""
        action = context.get('action', 'UNKNOWN')
        confidence = context.get('confidence', 0.5)
        accuracy_factors = context.get('accuracy_factors', {})
        eligibility = context.get('eligibility', {})
        customer = context.get('customer', {})
        
        return f"""Generate a brief, professional reason for this support decision (1-2 sentences max).

DECISION: {action.upper()}
CONFIDENCE: {confidence:.0%}
ELIGIBILITY: {eligibility.get('reason', 'Unknown')}
CUSTOMER TIER: {customer.get('tier', 'standard')}
DAYS SINCE DELIVERY: {eligibility.get('days_since_delivery', 'Unknown')}

Write a concise reason suitable for display on the ticket. Be empathetic but clear."""
    
    def _build_reasoning_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for ticket reasoning"""
        ticket = context.get('ticket', {}) if isinstance(context.get('ticket'), dict) else {}
        customer = context.get('customer', {}) if isinstance(context.get('customer'), dict) else {}
        order = context.get('order', {}) if isinstance(context.get('order'), dict) else {}
        eligibility = context.get('eligibility', {}) if isinstance(context.get('eligibility'), dict) else {}
        
        return f"""You are a support agent decision-making system. Analyze this support ticket and provide reasoning.

TICKET:
- ID: {ticket.get('ticket_id', 'N/A')}
- Subject: {ticket.get('subject', 'N/A')}
- Body: {ticket.get('body', '')[:200] if ticket.get('body') else 'N/A'}
- Customer Email: {ticket.get('customer_email', 'N/A')}

CUSTOMER:
- Name: {customer.get('name', 'N/A')}
- Tier: {customer.get('tier', 'standard')}
- Total Orders: {customer.get('total_orders', 0)}
- Previous Refunds: {customer.get('notes', '')[:100] if customer.get('notes') else 'N/A'}

ORDER:
- Order ID: {order.get('order_id', 'N/A')}
- Product: {order.get('product_id', 'N/A')}
- Price: ${order.get('total_price', 0)}
- Delivery: {order.get('delivery_date', 'N/A')}

ELIGIBILITY:
- Eligible: {eligibility.get('eligible', 'Unknown')}
- Reason: {eligibility.get('reason', 'No information')}
- Days Since Delivery: {eligibility.get('days_since_delivery', 'Unknown')}

Provide concise reasoning for approval/denial decision. Consider policy, customer history, and fairness."""
    
    def _build_message_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for customer message crafting"""
        customer = context.get('customer', {}) if isinstance(context.get('customer'), dict) else {}
        order = context.get('order', {}) if isinstance(context.get('order'), dict) else {}
        decision = context.get('decision', {}) if isinstance(context.get('decision'), dict) else {}
        
        return f"""Craft a professional, empathetic customer service response.

CUSTOMER: {customer.get('name', 'Valued Customer')} (Tier: {customer.get('tier', 'standard')})
ORDER: {order.get('order_id', 'N/A')} - ${order.get('total_price', 0)}
DECISION: {decision.get('action', 'PENDING')}
REASON: {decision.get('reason', 'Policy compliance')}

Write a personalized response (2-3 sentences). Be empathetic if denying, clear if approving."""
    
    def _build_confidence_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for confidence assessment"""
        evidence = context.get('evidence', {}) if isinstance(context.get('evidence'), dict) else {}
        
        return f"""Rate your confidence in this decision (0.0-1.0 only, no explanation):

Evidence:
- Tool Failures: {evidence.get('tool_errors', 0)}
- Retries: {evidence.get('retries', 0)}
- Data Completeness: {evidence.get('data_complete', 'unknown')}
- Policy Clarity: {evidence.get('policy_clear', 'unknown')}
- Customer Tier: {evidence.get('customer_tier', 'standard')}

Respond with ONLY a single number between 0.0 and 1.0."""
    
    def analyze_query_with_knowledge_base(self, 
                                         customer_query: str, 
                                         knowledge_base: str,
                                         customer_info: Dict[str, Any],
                                         order_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze customer query against knowledge base with LLM intelligence
        
        Args:
            customer_query: The customer's ticket/request text
            knowledge_base: Company policies and guidelines
            customer_info: Customer profile (tier, history, etc)
            order_info: Order details
            
        Returns:
            {
                'decision': 'APPROVE'|'DENY'|'ESCALATE',
                'reason': str,
                'confidence': float (0.0-1.0),
                'policy_match': str
            }
        """
        if not self.enabled:
            return {
                'decision': 'ESCALATE',
                'reason': 'LLM analysis disabled',
                'confidence': 0.5,
                'policy_match': 'Unknown'
            }
        
        try:
            prompt = self._build_query_analysis_prompt(customer_query, knowledge_base, customer_info, order_info)
            response = self.client.generate_content(prompt)
            
            # Parse response
            response_text = response.text.strip()
            logger.debug(f"LLM query analysis: {response_text[:200]}...")
            
            # Extract structured response
            result = self._parse_analysis_response(response_text)
            return result
        except Exception as e:
            logger.error(f"LLM query analysis failed: {e}")
            return {
                'decision': 'ESCALATE',
                'reason': f'LLM analysis error: {str(e)}',
                'confidence': 0.3,
                'policy_match': 'Error'
            }
    
    def _build_query_analysis_prompt(self, 
                                     customer_query: str, 
                                     knowledge_base: str,
                                     customer_info: Dict[str, Any],
                                     order_info: Dict[str, Any]) -> str:
        """Build prompt for analyzing customer query against knowledge base"""
        customer_name = customer_info.get('name', 'Customer')
        customer_tier = customer_info.get('tier', 'standard')
        total_orders = customer_info.get('total_orders', 0)
        
        order_id = order_info.get('order_id', 'Unknown')
        product_category = order_info.get('product_category', 'Unknown')
        days_since_delivery = order_info.get('days_since_delivery', 'Unknown')
        
        return f"""You are a support decision AI. Analyze the customer query against company policy and provide a decision with confidence score.

CUSTOMER INFORMATION:
- Name: {customer_name}
- Tier: {customer_tier}
- Previous Orders: {total_orders}

ORDER INFORMATION:
- Order ID: {order_id}
- Product Category: {product_category}
- Days Since Delivery: {days_since_delivery}

COMPANY POLICIES:
{knowledge_base[:2000]}

CUSTOMER QUERY:
{customer_query}

Based on the customer's request and company policies, provide your analysis in this format:
DECISION: APPROVE or DENY or ESCALATE
CONFIDENCE: 0.0-1.0 (your confidence in this decision)
REASON: Brief explanation (1-2 sentences)
POLICY_MATCH: Which policy applies (1-2 sentences)

Be fair and customer-friendly while respecting company policies."""
    
    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM analysis response into structured format"""
        result = {
            'decision': 'ESCALATE',
            'reason': 'Unable to parse response',
            'confidence': 0.5,
            'policy_match': 'Unknown'
        }
        
        try:
            lines = response_text.strip().split('\n')
            for line in lines:
                if line.startswith('DECISION:'):
                    decision = line.replace('DECISION:', '').strip().upper()
                    if 'APPROVE' in decision:
                        result['decision'] = 'APPROVE'
                    elif 'DENY' in decision:
                        result['decision'] = 'DENY'
                    else:
                        result['decision'] = 'ESCALATE'
                elif line.startswith('CONFIDENCE:'):
                    try:
                        conf_str = line.replace('CONFIDENCE:', '').strip()
                        confidence = float(conf_str.replace('%', '').strip()) / 100 if '%' in conf_str else float(conf_str)
                        result['confidence'] = max(0.0, min(1.0, confidence))
                    except ValueError:
                        result['confidence'] = 0.5
                elif line.startswith('REASON:'):
                    result['reason'] = line.replace('REASON:', '').strip()
                elif line.startswith('POLICY_MATCH:'):
                    result['policy_match'] = line.replace('POLICY_MATCH:', '').strip()
            
            return result
        except Exception as e:
            logger.warning(f"Failed to parse analysis response: {e}")
            return result


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
    
    def generate_decision_reason(self, context: Dict[str, Any]) -> str:
        """Use OpenAI to generate decision reason"""
        if not self.enabled:
            return "Decision made based on policy compliance."
        
        try:
            prompt = self._build_decision_reason_prompt(context)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI decision reason generation failed: {e}")
            return "Decision made based on policy compliance."
    
    def _build_decision_reason_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for generating decision reason"""
        action = context.get('action', 'UNKNOWN')
        confidence = context.get('confidence', 0.5)
        eligibility = context.get('eligibility', {})
        customer = context.get('customer', {})
        
        return f"""Generate a brief, professional reason for this support decision (1-2 sentences max).

DECISION: {action.upper()}
CONFIDENCE: {confidence:.0%}
ELIGIBILITY: {eligibility.get('reason', 'Unknown')}
CUSTOMER TIER: {customer.get('tier', 'standard')}
DAYS SINCE DELIVERY: {eligibility.get('days_since_delivery', 'Unknown')}

Write a concise reason suitable for display on the ticket. Be empathetic but clear."""
    
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
    
    def analyze_query_with_knowledge_base(self, 
                                         customer_query: str, 
                                         knowledge_base: str,
                                         customer_info: Dict[str, Any],
                                         order_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze customer query against knowledge base with LLM intelligence
        Uses OpenAI API
        """
        if not self.enabled:
            return {
                'decision': 'ESCALATE',
                'reason': 'LLM analysis disabled',
                'confidence': 0.5,
                'policy_match': 'Unknown'
            }
        
        try:
            prompt = self._build_query_analysis_prompt(customer_query, knowledge_base, customer_info, order_info)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content.strip()
            logger.debug(f"OpenAI query analysis: {response_text[:200]}...")
            
            result = self._parse_analysis_response(response_text)
            return result
        except Exception as e:
            logger.error(f"OpenAI query analysis failed: {e}")
            return {
                'decision': 'ESCALATE',
                'reason': f'LLM analysis error: {str(e)}',
                'confidence': 0.3,
                'policy_match': 'Error'
            }
    
    def _build_query_analysis_prompt(self, 
                                     customer_query: str, 
                                     knowledge_base: str,
                                     customer_info: Dict[str, Any],
                                     order_info: Dict[str, Any]) -> str:
        """Build prompt for analyzing customer query against knowledge base"""
        customer_name = customer_info.get('name', 'Customer')
        customer_tier = customer_info.get('tier', 'standard')
        total_orders = customer_info.get('total_orders', 0)
        
        order_id = order_info.get('order_id', 'Unknown')
        product_category = order_info.get('product_category', 'Unknown')
        days_since_delivery = order_info.get('days_since_delivery', 'Unknown')
        
        return f"""You are a support decision AI. Analyze the customer query against company policy and provide a decision with confidence score.

CUSTOMER INFORMATION:
- Name: {customer_name}
- Tier: {customer_tier}
- Previous Orders: {total_orders}

ORDER INFORMATION:
- Order ID: {order_id}
- Product Category: {product_category}
- Days Since Delivery: {days_since_delivery}

COMPANY POLICIES:
{knowledge_base[:2000]}

CUSTOMER QUERY:
{customer_query}

Based on the customer's request and company policies, provide your analysis in this format:
DECISION: APPROVE or DENY or ESCALATE
CONFIDENCE: 0.0-1.0 (your confidence in this decision)
REASON: Brief explanation (1-2 sentences)
POLICY_MATCH: Which policy applies (1-2 sentences)

Be fair and customer-friendly while respecting company policies."""
    
    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM analysis response into structured format"""
        result = {
            'decision': 'ESCALATE',
            'reason': 'Unable to parse response',
            'confidence': 0.5,
            'policy_match': 'Unknown'
        }
        
        try:
            lines = response_text.strip().split('\n')
            for line in lines:
                if line.startswith('DECISION:'):
                    decision = line.replace('DECISION:', '').strip().upper()
                    if 'APPROVE' in decision:
                        result['decision'] = 'APPROVE'
                    elif 'DENY' in decision:
                        result['decision'] = 'DENY'
                    else:
                        result['decision'] = 'ESCALATE'
                elif line.startswith('CONFIDENCE:'):
                    try:
                        conf_str = line.replace('CONFIDENCE:', '').strip()
                        confidence = float(conf_str.replace('%', '').strip()) / 100 if '%' in conf_str else float(conf_str)
                        result['confidence'] = max(0.0, min(1.0, confidence))
                    except ValueError:
                        result['confidence'] = 0.5
                elif line.startswith('REASON:'):
                    result['reason'] = line.replace('REASON:', '').strip()
                elif line.startswith('POLICY_MATCH:'):
                    result['policy_match'] = line.replace('POLICY_MATCH:', '').strip()
            
            return result
        except Exception as e:
            logger.warning(f"Failed to parse analysis response: {e}")
            return result


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
    
    def generate_decision_reason(self, context: Dict[str, Any]) -> str:
        """Get decision reason from first available provider"""
        for provider in self.providers:
            if provider.enabled:
                return provider.generate_decision_reason(context)
        
        return "Decision made based on policy compliance."
    
    def analyze_query_with_knowledge_base(self, 
                                         customer_query: str, 
                                         knowledge_base: str,
                                         customer_info: Dict[str, Any],
                                         order_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze customer query against knowledge base using available LLM provider
        Routes to first enabled provider (Gemini first, then OpenAI)
        
        Returns:
            {
                'decision': 'APPROVE'|'DENY'|'ESCALATE',
                'reason': str,
                'confidence': float (0.0-1.0),
                'policy_match': str
            }
        """
        for provider in self.providers:
            if provider.enabled:
                logger.info(f"Using {provider.__class__.__name__} for query analysis")
                return provider.analyze_query_with_knowledge_base(
                    customer_query, knowledge_base, customer_info, order_info
                )
        
        logger.warning("No LLM providers available for query analysis")
        return {
            'decision': 'ESCALATE',
            'reason': 'No LLM providers available',
            'confidence': 0.3,
            'policy_match': 'Unable to analyze'
        }

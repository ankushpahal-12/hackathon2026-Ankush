## LLM Integration Guide

This document explains how to enable LLM-powered reasoning in the support agent.

### Supported LLM Providers

The agent supports multiple LLM providers:

1. **Google Gemini** (Recommended - Free tier available)
2. **OpenAI** (GPT-4, GPT-3.5-Turbo)
3. **Anthropic** (Claude 3)
4. **Ollama** (Local/open-source - coming soon)

### Setup Instructions

#### Option 1: Google Gemini (Recommended)

1. Get API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Set environment variable:
   ```bash
   export GOOGLE_API_KEY="your-key-here"
   ```
3. Install library:
   ```bash
   pip install google-generativeai
   ```
4. Run agent:
   ```bash
   cd hackathon
   python main.py
   ```

#### Option 2: OpenAI

1. Get API key from [OpenAI Platform](https://platform.openai.com/account/api-keys)
2. Set environment variable:
   ```bash
   export OPENAI_API_KEY="your-key-here"
   ```
3. Install library:
   ```bash
   pip install openai
   ```
4. Run agent:
   ```bash
   cd hackathon
   python main.py
   ```

### LLM Usage in Agent

The agent uses LLM for three key tasks:

#### 1. **Ticket Reasoning**
When processing a ticket, the agent asks the LLM:
- "Is this refund request legitimate?"
- "What are the policy implications?"
- "Should we approve or deny?"

```python
llm_reasoning = reasoner.reason_about_ticket({
    'ticket': ticket_data,
    'customer': customer_data,
    'order': order_data,
    'eligibility': eligibility_data
})
```

#### 2. **Message Crafting**
Instead of template-based responses, the LLM generates personalized messages:
- "Thank you for contacting us..." → Personalized using customer name, situation, policy
- Different tone for approvals vs denials
- Empathetic language for difficult decisions

```python
message = reasoner.craft_customer_message({
    'customer': customer_data,
    'order': order_data,
    'decision': {'action': 'APPROVE', 'reason': '...'}
})
```

#### 3. **Confidence Assessment**
The LLM assesses how confident the decision is based on:
- Tool failures encountered
- Data completeness
- Policy clarity
- Customer tier

```python
confidence = reasoner.assess_confidence({
    'evidence': {
        'tool_errors': 2,
        'retries': 1,
        'data_complete': 'yes',
        'policy_clear': 'maybe',
        'customer_tier': 'gold'
    }
})
```

### Configuration

#### Disable LLM (Use Fallback)

```bash
# Edit main.py:
agent = SupportAgent(use_llm=False)  # Disables LLM, uses templates
```

#### Multiple Providers (Fallback Chain)

If Gemini isn't available, try OpenAI. If that fails, use templates:

```python
from src.llm import GeminiProvider, OpenAIProvider, LLMReasoner

reasoner = LLMReasoner(providers=[
    GeminiProvider(),
    OpenAIProvider(),
])
```

### Performance & Costs

| Provider | Cost | Speed | Quality |
|----------|------|-------|---------|
| Gemini | Free tier (20 calls/min) | Fast (1-2s) | Excellent |
| OpenAI GPT-4 | $0.03-0.06/1k tokens | Slower | Best |
| OpenAI GPT-3.5 | $0.0005-0.002/1k tokens | Fastest | Good |
| Anthropic Claude | $0.003-0.024/1k tokens | Medium | Excellent |

**Recommendation**: Start with Gemini free tier for testing. Scale to OpenAI for production.

### Troubleshooting

**"GOOGLE_API_KEY not set"**
- Verify environment variable is set: `echo $GOOGLE_API_KEY`
- On Windows: Use `set GOOGLE_API_KEY=your-key` in Command Prompt

**"Failed to initialize Gemini"**
- Check API key is valid: Try in [Google AI Studio](https://aistudio.google.com/app/apikey)
- Check rate limits: Free tier has 20 requests/minute limit
- Install library: `pip install google-generativeai`

**"LLM reasoning disabled (no valid API keys)"**
- Agent will still work! Falls back to template-based messages
- Set an API key to enable LLM features

### Metrics Reported

After running with LLM enabled, the agent reports:

```
LLM REASONING STATISTICS:
- Reasoning calls: 20/20 (100%)
- Message generation: 20/20 (100%)
- Confidence assessments: 20/20 (100%)
- Avg reasoning quality: 0.85/1.0
```

### Security Notes

- ⚠️ **Never commit API keys to Git!**
- Use environment variables only
- Consider API key rotation for production
- Monitor API costs in provider dashboards
- Set rate limits appropriately

### Cost Estimation

For 20 tickets with LLM enabled:

| Provider | Cost |
|----------|------|
| Gemini | Free (within limits) |
| OpenAI GPT-3.5 | ~$0.05 |
| OpenAI GPT-4 | ~$2.00 |
| Anthropic Claude | ~$0.10 |


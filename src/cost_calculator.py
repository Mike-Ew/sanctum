# Pricing per 1M tokens (in dollars)
PRICING = {
    "gpt-5": {"input": 20.0, "output": 60.0},
    "gpt-5-mini": {"input": 5.0, "output": 15.0},
    "gpt-5-nano": {"input": 2.0, "output": 8.0},
    "gpt-4o": {"input": 2.5, "output": 10.0},
    "gpt-3.5-turbo": {"input": 0.5, "output": 1.5}
}

def count_tokens(text, model="gpt-5"):
    """
    Count tokens using character-based estimation
    
    Args:
        text: Text to count tokens for
        model: Model name for tokenizer
        
    Returns:
        Number of tokens (estimated)
    """
    # Use character-based estimation
    # Average of 4 characters per token is a reasonable approximation
    return len(text) // 4

def estimate_cost(input_text, model="gpt-5", estimated_output_tokens=500):
    """
    Estimate cost before API call
    
    Args:
        input_text: Text to be sent to API
        model: Model to use
        estimated_output_tokens: Expected output size
        
    Returns:
        Dict with token counts and costs
    """
    input_tokens = count_tokens(input_text, model)
    
    if model not in PRICING:
        return {
            "input_tokens": input_tokens,
            "output_tokens": estimated_output_tokens,
            "input_cost": 0,
            "output_cost": 0,
            "total_cost": 0,
            "error": "Model pricing not available"
        }
    
    # Calculate costs (price is per 1M tokens)
    input_cost = (input_tokens / 1_000_000) * PRICING[model]["input"]
    output_cost = (estimated_output_tokens / 1_000_000) * PRICING[model]["output"]
    
    return {
        "input_tokens": input_tokens,
        "output_tokens": estimated_output_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": input_cost + output_cost,
        "formatted_cost": f"${input_cost + output_cost:.4f}"
    }

def calculate_actual_cost(usage_dict, model="gpt-5"):
    """
    Calculate actual cost from API response usage
    
    Args:
        usage_dict: Usage field from OpenAI API response
        model: Model used
        
    Returns:
        Dict with actual costs
    """
    if model not in PRICING:
        return {"error": "Model pricing not available"}
    
    prompt_tokens = usage_dict.get("prompt_tokens", 0)
    completion_tokens = usage_dict.get("completion_tokens", 0)
    total_tokens = usage_dict.get("total_tokens", 0)
    
    input_cost = (prompt_tokens / 1_000_000) * PRICING[model]["input"]
    output_cost = (completion_tokens / 1_000_000) * PRICING[model]["output"]
    
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": input_cost + output_cost,
        "formatted_cost": f"${input_cost + output_cost:.4f}"
    }

def format_cost_summary(cost_dict):
    """
    Format cost dictionary for display
    
    Args:
        cost_dict: Cost calculation dictionary
        
    Returns:
        Formatted string for display
    """
    if "error" in cost_dict:
        return cost_dict["error"]
    
    return f"""
📊 Token Usage:
• Input: {cost_dict['input_tokens']:,} tokens
• Output: {cost_dict.get('output_tokens', 0):,} tokens
• Total: {cost_dict.get('input_tokens', 0) + cost_dict.get('output_tokens', 0):,} tokens

💰 Cost Breakdown:
• Input cost: ${cost_dict['input_cost']:.4f}
• Output cost: ${cost_dict['output_cost']:.4f}
• Total: {cost_dict['formatted_cost']}
"""
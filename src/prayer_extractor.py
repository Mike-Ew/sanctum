from openai import OpenAI
import json

def extract_prayers_with_ai(transcript_text, api_key, model="gpt-5"):
    """
    Extract prayers from transcript using OpenAI API
    
    Args:
        transcript_text: Full transcript text
        api_key: OpenAI API key
        model: GPT model to use (gpt-5, gpt-5-mini, gpt-5-nano, gpt-4o, gpt-3.5-turbo)
        
    Returns:
        List of prayer dictionaries with 'number', 'text', 'scripture'
    """
    
    client = OpenAI(api_key=api_key)
    
    system_prompt = """You are a prayer point extraction specialist for church services.
    Your job is to find ALL prayers announced in the intercessory section.
    
    KEY UNDERSTANDING:
    - Prayers are ANNOUNCED first, then the congregation prays them
    - The announcement is what you need to capture, not the congregation's repetition
    - NEVER skip any prayers, especially not thanksgiving prayers
    
    PRAYER ANNOUNCEMENT PATTERNS:
    - "We shall be saying, 'Father...'" 
    - "Next we'll be saying father..."
    - "Let's pray saying, 'Father...'"
    - "We will rise and pray to our father in this way. Say father..."
    - Look for where the pastor tells people WHAT to pray
    
    PRAYER TYPES TO INCLUDE:
    - Thanksgiving prayers (usually first, starts with "Father, thank you...")
    - Intercessory prayers ("Father, in the name of Jesus...")
    - Declaration prayers ("Father, perfect..." or "Father, gather...")
    - ALL prayers matter - extract them all in order
    
    SCRIPTURE HANDLING:
    - Each prayer has a scripture reference (Acts, Isaiah, etc.)
    - Clean up messy references from speech-to-text
    - Fix typos and formatting issues
    
    OUTPUT:
    - Complete prayer text as announced
    - Cleaned scripture reference
    - Prayers numbered in order found"""
    
    # Use full transcript for GPT-5, limit for others
    if model.startswith('gpt-5'):
        text_to_process = transcript_text  # GPT-5 can handle 400K tokens
    else:
        text_to_process = transcript_text[:30000]  # Limit others to ~7.5K tokens
    
    user_prompt = f"""Extract ALL prayer points from the intercessory section of this church service.
    
    IMPORTANT RULES:
    1. Find where prayers are ANNOUNCED (not where congregation prays them)
    2. Look for these announcement patterns:
       - "We shall be saying..." 
       - "Next we'll be saying..."
       - "Let's pray saying..."
       - "We will next rise and pray to our father in this way. Say..."
    
    3. After each announcement, the prayer text usually starts with "Father"
    
    4. Include ALL prayers - DO NOT skip any, including:
       - Thanksgiving prayers (often start with "Father, thank you...")
       - Intercessory prayers (often "Father, in the name of Jesus...")
       - Declaration prayers (often "Father, perfect..." or "Father, gather...")
    
    5. Each prayer is followed by a scripture reference that needs cleaning:
       - "Act of apostle 14:17" or "14:E1 17" → "Acts 14:17"
       - "Act 3:16" or "chapter 3 and verse 16" → "Acts 3:16"
       - "Isaiah 9 and verse 8" → "Isaiah 9:8"
       - Remove any "E1" or similar artifacts
    
    6. Extract prayers in the ORDER they are announced (usually 3-5 prayers)
    
    Transcript:
    {text_to_process}
    
    Return JSON array with ALL prayers found, in order:
    [
        {{"number": "1", "text": "[complete prayer text]", "scripture": "[cleaned reference]"}},
        {{"number": "2", "text": "[complete prayer text]", "scripture": "[cleaned reference]"}},
        ...
    ]"""
    
    try:
        print(f"Calling {model} with {len(text_to_process)} characters...")
        
        # GPT-5 models only support default temperature
        if model.startswith('gpt-5'):
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
                # temperature=1 is the default for GPT-5
            )
        else:
            # For GPT-4o and others
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1
            )
        
        print(f"Got response from {model}")
        print(f"Response object: {response}")
        
        # Get the response content
        content = response.choices[0].message.content
        
        # Debug: print what we got
        print(f"Raw response from {model}:")
        print(content[:500])  # First 500 chars for debugging
        
        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]  # Remove ```json
        if content.startswith("```"):
            content = content[3:]  # Remove ```
        if content.endswith("```"):
            content = content[:-3]  # Remove trailing ```
        content = content.strip()
        
        result = json.loads(content)
        
        # Ensure we have a prayers array
        if "prayers" in result:
            return result["prayers"]
        elif isinstance(result, list):
            return result
        else:
            return []
            
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Response content: {content[:1000]}")
        raise e
    except Exception as e:
        print(f"AI extraction error: {e}")
        raise e  # Re-raise to see the actual error
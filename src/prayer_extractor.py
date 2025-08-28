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
    Extract ALL prayer points that the pastor announces for the congregation to pray.
    
    IMPORTANT PATTERNS TO RECOGNIZE:
    - "We shall be saying..." or "Next we'll be saying..." introduces a prayer
    - "Father, thank you..." IS a prayer point (don't skip thanksgiving prayers!)
    - "Father, in the name of Jesus..." starts many prayers
    - "Father, gather..." or "Father, perfect..." are prayer starts
    
    EXTRACT ALL PRAYERS INCLUDING:
    - Thanksgiving prayers (often first)
    - Intercessory prayers
    - Declaration prayers
    - Usually 3-5 total prayer points per service
    
    SCRIPTURE REFERENCES:
    - May appear as "Acts 14:17" or "Act of apostle 14:17" or similar
    - Clean up references (e.g., "Act 3:16" → "Acts 3:16")
    - "Isaiah 9 and verse 8" → "Isaiah 9:8"
    
    EXTRACT:
    - The complete prayer text as announced
    - The scripture reference (cleaned up)
    - The verse text when provided"""
    
    # Use full transcript for GPT-5, limit for others
    if model.startswith('gpt-5'):
        text_to_process = transcript_text  # GPT-5 can handle 400K tokens
    else:
        text_to_process = transcript_text[:30000]  # Limit others to ~7.5K tokens
    
    user_prompt = f"""Extract ALL prayer points from this church service transcript.
    
    LOOK FOR THESE PATTERNS:
    1. "We shall be saying, Father..." or "Next we'll be saying father..."
    2. "Let's pray saying Father..." or "Let's pray. Father..."
    3. Any prayer starting with "Father, thank you..." or "Father, in the name of Jesus..."
    
    The prayers are usually announced first, then prayed together by the congregation.
    Include ALL prayers, especially thanksgiving prayers (usually Prayer 1).
    
    Clean up scripture references:
    - "Act of apostle 14:17" → "Acts 14:17"
    - "Act 3:16" → "Acts 3:16"  
    - "Isaiah 9 and verse 8" → "Isaiah 9:8"
    
    Transcript:
    {text_to_process}
    
    Return JSON array with ALL prayers found (usually 3-5 total):
    [
        {{"number": "1", "text": "Father, thank you for invading our services last Sunday with abiding multitude and for the diverse signs and wonders wrought by your word and prophetic mantle", "scripture": "Acts 14:17", "verse_text": "Nevertheless he left not himself without witness..."}},
        {{"number": "2", "text": "Father, in the name of Jesus, open up the glorious destiny of all our new converts of the year, thereby leading many others to Christ and this church", "scripture": "Zechariah 8:23", "verse_text": "Thus saith the Lord of hosts..."}}
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
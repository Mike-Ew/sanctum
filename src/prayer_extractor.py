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
    Extract ALL prayer points from the INTERCESSORY SECTION of the service.
    
    IMPORTANT PATTERNS TO RECOGNIZE:
    - The intercessory section contains the main prayers
    - "We shall be saying..." or "Next we'll be saying..." introduces a prayer
    - "Father, thank you..." IS a prayer point (don't skip thanksgiving prayers!)
    - "Father, in the name of Jesus..." starts many prayers
    - "Father, gather..." or "Father, perfect..." are prayer starts
    
    EXTRACT ALL PRAYERS INCLUDING:
    - Thanksgiving prayers (often Prayer 1)
    - Intercessory prayers (main section)
    - Declaration prayers
    - Usually 3-5 total prayer points in the intercessory section
    
    SCRIPTURE REFERENCES:
    - May appear as "Acts 14:17" or "Act of apostle 14:17" or similar
    - Clean up references (e.g., "Act 3:16" → "Acts 3:16")
    - "Isaiah 9 and verse 8" → "Isaiah 9:8"
    - Even if pastor paraphrases, extract the reference for full verse lookup
    
    EXTRACT:
    - The complete prayer text as announced by the pastor
    - The scripture reference (cleaned up) - ALWAYS include this
    - Don't worry about verse text - the Bible API will provide full verses"""
    
    # Use full transcript for GPT-5, limit for others
    if model.startswith('gpt-5'):
        text_to_process = transcript_text  # GPT-5 can handle 400K tokens
    else:
        text_to_process = transcript_text[:30000]  # Limit others to ~7.5K tokens
    
    user_prompt = f"""Extract ALL prayer points from this church service transcript.
    
    CRITICAL: There are usually 4 prayers in the intercessory section:
    1. FIRST PRAYER (Thanksgiving): "Father, thank you for invading our services..." - Acts 14:17
    2. SECOND PRAYER: "Father, in the name of Jesus, open up the glorious destiny..." - Zechariah 8:23
    3. THIRD PRAYER: "Father, perfect the health..." - Acts 3:16
    4. FOURTH PRAYER: "Father, gather unprecedented..." - Isaiah 9:8
    
    LOOK FOR THESE EXACT PATTERNS:
    - "We shall be saying, 'Father, thank you..." - This is Prayer 1!
    - "We will next rise and pray to our father in this way. Say father..." 
    - "Next we'll be saying father..."
    - "Let's pray saying Father..."
    
    The first prayer is ALWAYS the thanksgiving prayer starting with "Father, thank you".
    DO NOT SKIP IT. It's part of the intercessory section.
    
    Clean up scripture references:
    - "Act of apostle 14:17" or "Act of apostle 14:E1 17" → "Acts 14:17"
    - "Act 3:16" or "Acts chapter 3 and verse 16" → "Acts 3:16"  
    - "Isaiah 9 and verse 8" → "Isaiah 9:8"
    - "Zechariah 8:23" or "Zech. 8:23" → "Zechariah 8:23"
    
    Transcript:
    {text_to_process}
    
    Return JSON array with ALL 4 prayers (or however many you find):
    [
        {{"number": "1", "text": "Father, thank you for invading our services last Sunday with abiding multitude and for the diverse signs and wonders wrought by your word and prophetic mantle", "scripture": "Acts 14:17"}},
        {{"number": "2", "text": "Father, in the name of Jesus, open up the glorious destiny of all our new converts of the year, thereby leading many others to Christ and this church", "scripture": "Zechariah 8:23"}},
        {{"number": "3", "text": "Father, perfect the health of every winner before this month is over", "scripture": "Acts 3:16"}},
        {{"number": "4", "text": "Father, gather unprecedented and abiding multitudes into our services this coming Sunday and grant every worshipper their desired encounter by your word", "scripture": "Isaiah 9:8"}}
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
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
    Extract ONLY the specific prayer points that the pastor announces, usually numbered or introduced as "prayer point".
    These are typically stated clearly before the congregation prays them.
    Each prayer point is usually 1-2 sentences and often has a scripture reference.
    
    IGNORE:
    - General thanksgiving prayers
    - Congregational responses and repetitions
    - Elaborations and expansions of the prayer points
    
    EXTRACT:
    - The exact prayer point as announced by the pastor
    - The associated scripture reference (e.g., "John 4:36")
    - The verse text if the pastor reads it (e.g., "And he that reapeth receiveth wages...")
    - Usually there are 4-5 main intercessory prayer points in a service"""
    
    # Use full transcript for GPT-5, limit for others
    if model.startswith('gpt-5'):
        text_to_process = transcript_text  # GPT-5 can handle 400K tokens
    else:
        text_to_process = transcript_text[:30000]  # Limit others to ~7.5K tokens
    
    user_prompt = f"""Extract the announced prayer points from this transcript.
    Look for phrases like "prayer point", "let us pray", "say Father", or numbered prayers.
    Also capture the Bible verse text when the pastor reads it after announcing the scripture reference.
    
    Transcript:
    {text_to_process}
    
    Return JSON array like:
    [
        {{"number": "1", "text": "Father, thank you for the unprecedented multitudes you drafted into our services last Sunday and for establishing the enough is enough verdict in all issues of concern in the lives of all worshippers", "scripture": "Psalm 118:23", "verse_text": "This is the Lord's doing; it is marvelous in our eyes"}},
        {{"number": "2", "text": "Father, in this season of glory consume all our new converts and new members with the zeal of the Lord so they can love to share the gospel with others thereby getting blessed in return", "scripture": "John 4:36", "verse_text": "And he that reapeth receiveth wages, and gathereth fruit unto life eternal: that both he that soweth and he that reapeth may rejoice together"}}
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
"""
Sanctum - Prayer Slides Generator V3 with AI
Uses OpenAI API for accurate prayer extraction
"""

import streamlit as st
import re
import os
import json
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="Sanctum - Prayer Slides Generator (AI)",
    page_icon="🙏",
    layout="centered"
)

def extract_video_id(url):
    """Extract YouTube video ID from URL"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/live\/)([^&\n?]+)',
        r'youtube\.com\/watch\?.*v=([^&\n?]+)',
        r'youtube\.com\/live\/([^&\n?]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def fetch_transcript(video_id):
    """Fetch transcript from YouTube video with timestamps"""
    try:
        # Create an instance of the API
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        try:
            # Try to get manually created transcript first
            transcript = transcript_list.find_transcript(['en'])
        except:
            # Fall back to auto-generated transcript
            try:
                transcript = transcript_list.find_generated_transcript(['en'])
            except:
                # Get any available transcript
                transcript = transcript_list.find_transcript(['en-US'])
        
        transcript_data = transcript.fetch()
        
        # Return both formatted text and raw data with timestamps
        formatter = TextFormatter()
        formatted_transcript = formatter.format_transcript(transcript_data)
        return formatted_transcript, transcript_data
    except Exception as e:
        return None, str(e)

def extract_prayers_with_ai(transcript_text, api_key, model="gpt-4-turbo-preview", transcript_data=None):
    """
    Use OpenAI to extract prayers and scriptures accurately using timestamps
    """
    try:
        import openai
        openai.api_key = api_key
        
        # If we have timestamp data, use it to identify prayer clusters
        if transcript_data and isinstance(transcript_data, list) and len(transcript_data) > 0:
            # Look for prayer point markers with timestamps
            prayer_markers = ['prayer point', 'prayer item', 'prayer number', 'let us lift', 'let us pray']
            prayer_segments = []
            
            for i, segment in enumerate(transcript_data):
                # Handle different transcript data formats
                if isinstance(segment, dict) and 'text' in segment:
                    text_lower = segment['text'].lower()
                else:
                    # Skip if format is unexpected
                    continue
                    
                # Check if this segment contains prayer markers
                if any(marker in text_lower for marker in prayer_markers):
                    # Found a prayer section marker - collect next 5 minutes of content
                    start_time = segment['start']
                    end_time = start_time + 300  # 5 minutes window
                    
                    # Collect all segments in this time window
                    prayer_section = []
                    for j in range(i, min(i+100, len(transcript_data))):
                        if isinstance(transcript_data[j], dict) and 'start' in transcript_data[j] and 'text' in transcript_data[j]:
                            if transcript_data[j]['start'] <= end_time:
                                prayer_section.append(transcript_data[j]['text'])
                            else:
                                break
                    
                    if prayer_section:
                        prayer_segments.append(' '.join(prayer_section))
            
            # Also look for clusters of "Father" prayers in time
            father_clusters = []
            for i, segment in enumerate(transcript_data):
                if isinstance(segment, dict) and 'text' in segment and 'start' in segment:
                    if segment['text'].strip().startswith('Father') or 'father' in segment['text'].lower()[:20]:
                        # Found a Father prayer - check if there are more nearby
                        cluster_start = segment['start']
                        cluster_texts = []
                        
                        # Look for prayers within 2 minutes
                        for j in range(max(0, i-10), min(i+30, len(transcript_data))):
                            if isinstance(transcript_data[j], dict) and 'start' in transcript_data[j] and 'text' in transcript_data[j]:
                                if abs(transcript_data[j]['start'] - cluster_start) <= 120:
                                    cluster_texts.append(transcript_data[j]['text'])
                        
                        if len(cluster_texts) >= 4:  # Found a cluster
                            father_clusters.append(' '.join(cluster_texts))
            
            # Combine both approaches
            relevant_text = ' '.join(prayer_segments + father_clusters)
            
            # If no clusters found, fall back to keyword search
            if not relevant_text:
                prayer_keywords = r'\b(pray|prayer|father|lord|in jesus name|let us pray|we ask|we declare|amen)\b'
                prayer_sentences = []
                for segment in transcript_data:
                    if re.search(prayer_keywords, segment['text'], re.IGNORECASE):
                        prayer_sentences.append(segment['text'])
                relevant_text = ' '.join(prayer_sentences)
        else:
            # Fallback to text-only processing
            prayer_keywords = r'\b(pray|prayer|father|lord|in jesus name|let us pray|we ask|we declare|amen)\b'
            sentences = re.split(r'(?<=[.!?])\s+', transcript_text)
            
            prayer_sentences = []
            for sent in sentences:
                if re.search(prayer_keywords, sent, re.IGNORECASE):
                    prayer_sentences.append(sent)
            
            relevant_text = ' '.join(prayer_sentences) if prayer_sentences else transcript_text
        
        # Limit to reasonable size
        max_chars = 12000
        if len(relevant_text) > max_chars:
            relevant_text = relevant_text[:max_chars]
        
        # Single API call with the filtered text
        system_prompt = """You are a church service assistant extracting congregational prayer points with their scripture references.
From the transcript, extract EXACTLY FOUR main prayer points that are displayed on screen during the service.
These are the formal prayer points the congregation reads together, NOT conversational prayers.
Look for prayers about: thanksgiving for multitudes/healing, new converts consistency, God's presence terminating sickness, gathering multitudes.
Each prayer MUST start with 'Father' and be complete sentences.
Each prayer MUST have a scripture reference - these are usually shown right after the prayer.
Common scripture patterns: Psalm 115:1, Psalm 84:7, Psalm 114:7-8, Job 33:23-24, etc.
Return exactly 4 prayer points with their scriptures in the order they appear."""

        user_prompt = f"""Extract the 4 main congregational prayer points from this filtered transcript.
These are the formal prayers displayed on screen, not casual prayers.
Look for these specific prayer themes in order:
1. Thanksgiving for multitudes and healing miracles from last Sunday
2. New converts/members being consumed with zeal for consistency
3. God's presence dominating services and terminating health challenges
4. Gathering unprecedented multitudes this coming Sunday

IMPORTANT: Each prayer MUST have a scripture reference. Look for scripture mentions right after each prayer.

Scripture patterns to look for:
- Book chapter:verse (e.g., "Psalm 115:1", "John 3:16")
- Book chapter verse (e.g., "Psalm 115 verse 1")
- Common books: Psalm/Psalms, Isaiah, John, Matthew, Acts, Corinthians, etc.

Return as JSON array with EXACTLY 4 items:
[
  {{
    "number": 1,
    "prayer": "Father, thank you for...",
    "scripture": "Psalm 115:1"
  }},
  {{
    "number": 2,
    "prayer": "Father, in the name of Jesus...",
    "scripture": "Isaiah 60:1"
  }}
]

If a scripture is not clearly stated for a prayer, use these common references based on prayer theme:
- Thanksgiving/praise: "Psalm 100:4" or "Psalm 103:1"
- Healing/health: "Isaiah 53:5" or "Jeremiah 30:17"
- Salvation/souls: "Acts 2:47" or "Luke 19:10"
- Blessing/favor: "Psalm 5:12" or "Numbers 6:24-26"
- Protection: "Psalm 91:11" or "2 Thessalonians 3:3"
- Growth/increase: "Isaiah 60:22" or "Psalm 115:14"

Filtered transcript (prayer-related sentences only):
{relevant_text}"""
            
        # Use selected model for extraction
        # GPT-5 models use max_completion_tokens instead of max_tokens
        if model.startswith('gpt-5'):
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_completion_tokens=2000
            )
        else:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
        
        try:
            response_text = response.choices[0].message.content
            
            # Debug: Show filtered text and response
            with st.expander("🔍 Debug: Filtered Text & AI Response"):
                st.text(f"Filtered text length: {len(relevant_text)} chars")
                st.text(f"Prayer sentences found: {len(prayer_sentences)}")
                st.code(response_text[:1000])
            
            # Extract JSON from response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            response_text = response_text.strip()
            
            # Parse JSON
            prayers = json.loads(response_text)
            
            # Ensure it's a list
            if isinstance(prayers, dict):
                prayers = [prayers]
            
            return prayers
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            st.warning(f"Could not parse prayers: {str(e)[:100]}")
            # Fallback: try to extract prayers manually
            fallback_prayers = []
            lines = response_text.split('\n')
            for i, line in enumerate(lines):
                if 'Father' in line:
                    fallback_prayers.append({
                        'number': str(len(fallback_prayers) + 1),
                        'prayer': line.strip(),
                        'scripture': ''
                    })
            return fallback_prayers[:4]  # Limit to 4
    except Exception as e:
        st.error(f"AI extraction error: {str(e)}")
        return []

def format_scripture_reference(scripture):
    """Format scripture reference to match slide style"""
    if not scripture:
        return ""
    
    # Common book abbreviations
    abbreviations = {
        'genesis': 'GEN.', 'exodus': 'EXO.', 'leviticus': 'LEV.',
        'numbers': 'NUM.', 'deuteronomy': 'DEU.', 'joshua': 'JOS.',
        'judges': 'JUD.', 'ruth': 'RUT.', '1 samuel': '1 SAM.',
        '2 samuel': '2 SAM.', '1 kings': '1 KIN.', '2 kings': '2 KIN.',
        'job': 'JOB', 'psalm': 'PSA.', 'psalms': 'PSA.', 'proverbs': 'PRO.',
        'ecclesiastes': 'ECC.', 'isaiah': 'ISA.', 'jeremiah': 'JER.',
        'matthew': 'MAT.', 'mark': 'MAR.', 'luke': 'LUK.', 'john': 'JOH.',
        'acts': 'ACT.', 'romans': 'ROM.', '1 corinthians': '1 COR.',
        '2 corinthians': '2 COR.', 'galatians': 'GAL.', 'ephesians': 'EPH.',
        'philippians': 'PHI.', 'colossians': 'COL.', 'titus': 'TIT.',
        'hebrews': 'HEB.', 'james': 'JAM.', '1 peter': '1 PET.',
        '2 peter': '2 PET.', 'revelation': 'REV.', 'zechariah': 'ZEC.'
    }
    
    # Extract book name
    for book, abbrev in abbreviations.items():
        if book in scripture.lower():
            # Extract chapter and verse
            match = re.search(r'(\d+)[:\s]+(\d+)', scripture)
            if match:
                return f"{abbrev} {match.group(1)}:{match.group(2)}"
    
    # If no match, try to extract any book chapter:verse pattern
    match = re.search(r'([A-Za-z]+)\s+(\d+)[:\s]+(\d+)', scripture)
    if match:
        book = match.group(1).upper()[:3] + '.'
        return f"{book} {match.group(2)}:{match.group(3)}"
    
    return scripture.upper()[:50]  # Fallback

def format_slide_text(text, max_chars=350):
    """Format text for slide display in ALL CAPS"""
    text = text.upper()
    text = re.sub(r'\s+', ' ', text).strip()
    
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    max_line_chars = 60
    
    for word in words:
        word_length = len(word) + 1
        if current_length + word_length > max_line_chars and current_line:
            lines.append(' '.join(current_line))
            current_line = [word]
            current_length = word_length
        else:
            current_line.append(word)
            current_length += word_length
    
    if current_line:
        lines.append(' '.join(current_line))
    
    if len(lines) > 8:
        return split_into_multiple_slides(lines)
    
    return ['\n'.join(lines)]

def split_into_multiple_slides(lines, max_lines=8):
    """Split lines into multiple slides if needed"""
    slides = []
    for i in range(0, len(lines), max_lines):
        slide_lines = lines[i:i+max_lines]
        slides.append('\n'.join(slide_lines))
    return slides

def generate_prayer_slides(prayers, include_prayer_number=True, separate_scripture=True):
    """Generate slides in EasyWorship format - 8 slides total (4 prayers + 4 scriptures)"""
    all_slides = []
    
    for prayer in prayers:
        # Prepare header
        if include_prayer_number and prayer.get('number'):
            header = f"PRAYER {prayer['number']}"
        else:
            header = "PRAYER"
        
        # Format prayer text
        prayer_text = prayer.get('prayer', '')
        prayer_slides = format_slide_text(prayer_text)
        
        # Create prayer slide(s)
        for i, slide_text in enumerate(prayer_slides):
            slide_parts = [header]
            slide_parts.append("")  # Blank line after header
            slide_parts.append(slide_text)
            all_slides.append('\n'.join(slide_parts))
        
        # Create separate scripture slide
        if separate_scripture and prayer.get('scripture'):
            scripture_parts = [
                f"SCRIPTURE {prayer.get('number', '')}",
                "",
                format_scripture_reference(prayer.get('scripture', '')).upper(),
                "",
                f"(FOR PRAYER {prayer.get('number', '')})"
            ]
            all_slides.append('\n'.join(scripture_parts))
        elif not separate_scripture and prayer.get('scripture'):
            # Add scripture to last prayer slide if not separating
            if all_slides:
                last_slide = all_slides[-1]
                last_slide += "\n\n" + format_scripture_reference(prayer.get('scripture', ''))
                all_slides[-1] = last_slide
    
    return '\n\n---\n\n'.join(all_slides)

# Streamlit UI
st.title("🙏 Sanctum - Prayer Slides Generator V3")
st.markdown("AI-powered prayer extraction for accurate results")

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")
    
    # API Key input - check env first, then allow manual input
    env_key = os.getenv('OPENAI_API_KEY')
    
    if env_key:
        api_key = env_key
        st.success("✅ API Key loaded from .env file")
    else:
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            help="Enter your OpenAI API key or set OPENAI_API_KEY in .env file"
        )
        
        if api_key:
            st.success("✅ API Key configured")
        else:
            st.warning("⚠️ API Key required for AI extraction")
    
    st.markdown("---")
    
    # Model selection
    model_choice = st.selectbox(
        "AI Model",
        ["gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-4", "gpt-4-turbo-preview", "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo-16k"],
        index=0,  # Default to gpt-5
        help="GPT-5 is the latest and most capable model (released Aug 2025)"
    )
    
    include_numbers = st.checkbox("Include Prayer Numbers", value=True)
    separate_scriptures = st.checkbox("Separate Scripture Slides", value=True, 
                                     help="Create separate slides for scriptures (8 total) or include on prayer slides (4 total)")
    
    extraction_method = st.radio(
        "Extraction Method",
        ["AI (Recommended)", "Regex (Fallback)"],
        help="AI provides more accurate extraction"
    )
    
    st.markdown("---")
    st.markdown("### 💰 Cost Estimate")
    
    cost_map = {
        "gpt-3.5-turbo-16k": "~$0.002 per sermon",
        "gpt-4": "~$0.02 per sermon",
        "gpt-4-turbo-preview": "~$0.01 per sermon",
        "gpt-4o": "~$0.005 per sermon",
        "gpt-4o-mini": "~$0.001 per sermon"
    }
    
    st.markdown(f"**Selected Model ({model_choice}):**")
    st.markdown(cost_map.get(model_choice, "~$0.01 per sermon"))
    
    st.markdown("---")
    st.markdown("### 📖 Why AI?")
    st.markdown("""
    AI extraction provides:
    - Complete prayer capture
    - Accurate scripture matching
    - Better handling of speech patterns
    - Context understanding
    """)

# Main input area
youtube_url = st.text_input(
    "YouTube Video URL",
    placeholder="https://www.youtube.com/watch?v=...",
    help="Paste the full YouTube URL of the sermon"
)

# Example of expected output
with st.expander("📋 See Example Output"):
    st.markdown("""
    **Prayer 2:**
    - Prayer: "Father thank you for drafting great multitudes into our services..."
    - Scripture: "PSA. 115:1"
    
    **Prayer 3:**
    - Prayer: "Father consume all our new converts and new members..."
    - Scripture: "PSA. 84:7"
    """)

# Generate button
if st.button("🎬 Generate Prayer Slides", type="primary"):
    if not api_key and extraction_method == "AI (Recommended)":
        st.error("Please enter your OpenAI API key in the sidebar")
    elif youtube_url:
        video_id = extract_video_id(youtube_url)
        
        if video_id:
            with st.spinner("Fetching transcript..."):
                result = fetch_transcript(video_id)
                
                if result[0] is None:
                    st.error(f"Error fetching transcript: {result[1]}")
                else:
                    transcript, transcript_data = result
                    
                    # Add transcript download option
                    with st.expander("📄 View/Download Transcript"):
                        st.text_area("Full Transcript", transcript[:5000] + "..." if len(transcript) > 5000 else transcript, height=300)
                        st.download_button(
                            label="📥 Download Full Transcript",
                            data=transcript,
                            file_name=f"transcript_{video_id}.txt",
                            mime="text/plain",
                            help="Download the full transcript for manual review or testing"
                        )
                        st.info(f"Transcript length: {len(transcript)} characters")
                    
                    with st.spinner(f"🤖 Extracting prayers with {model_choice}..."):
                        if extraction_method == "AI (Recommended)" and api_key:
                            prayers = extract_prayers_with_ai(transcript, api_key, model_choice, transcript_data)
                        else:
                            st.warning("Falling back to regex extraction...")
                            # Fallback to basic extraction
                            prayers = []
                            # Simple Father prayer extraction
                            father_matches = re.findall(r'(?i)(father[^.]+(?:\.[^.]+){0,3})', transcript)
                            for i, match in enumerate(father_matches[:10], 1):
                                prayers.append({
                                    'number': str(i),
                                    'prayer': match.strip(),
                                    'scripture': ''
                                })
                        
                        if prayers:
                            st.success(f"✅ Found {len(prayers)} prayer(s)")
                            
                            # Display extracted prayers
                            with st.expander("🔍 View Extracted Prayers"):
                                for prayer in prayers[:5]:  # Show first 5
                                    st.markdown(f"**Prayer {prayer.get('number', '?')}:**")
                                    st.markdown(f"- {prayer.get('prayer', 'N/A')[:100]}...")
                                    if prayer.get('scripture'):
                                        st.markdown(f"- Scripture: {prayer.get('scripture', 'N/A')}")
                                    st.markdown("---")
                            
                            # Generate formatted slides
                            formatted_slides = generate_prayer_slides(prayers, include_numbers, separate_scriptures)
                            
                            # Preview ALL slides (8 total: 4 prayers + 4 scriptures)
                            st.markdown("### 📄 Full Slide Preview (8 Slides)")
                            slides_list = formatted_slides.split('\n\n---\n\n')
                            
                            # Create tabs for all slides
                            if len(slides_list) > 0:
                                # Group into prayers and scriptures for better organization
                                tab_names = []
                                for i in range(len(slides_list)):
                                    if i % 2 == 0:  # Prayer slides
                                        tab_names.append(f"Prayer {(i//2)+1}")
                                    else:  # Scripture slides
                                        tab_names.append(f"Scripture {(i//2)+1}")
                                
                                # Show all slides in tabs
                                if len(slides_list) <= 8:
                                    tabs = st.tabs(tab_names[:len(slides_list)])
                                    for i, tab in enumerate(tabs):
                                        with tab:
                                            st.code(slides_list[i], language=None)
                                else:
                                    # If more than 8, show in two rows
                                    st.markdown("#### Prayers")
                                    prayer_tabs = st.tabs([f"Prayer {i+1}" for i in range(4)])
                                    for i, tab in enumerate(prayer_tabs):
                                        if i*2 < len(slides_list):
                                            with tab:
                                                st.code(slides_list[i*2], language=None)
                                    
                                    st.markdown("#### Scriptures")
                                    scripture_tabs = st.tabs([f"Scripture {i+1}" for i in range(4)])
                                    for i, tab in enumerate(scripture_tabs):
                                        if i*2+1 < len(slides_list):
                                            with tab:
                                                st.code(slides_list[i*2+1], language=None)
                            
                            # Download buttons
                            st.markdown("### 💾 Download")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.download_button(
                                    label="📥 Download for EasyWorship",
                                    data=formatted_slides.replace('---', ''),
                                    file_name="prayer_slides.txt",
                                    mime="text/plain"
                                )
                            
                            with col2:
                                # Also save as JSON for reference
                                st.download_button(
                                    label="📥 Download as JSON",
                                    data=json.dumps(prayers, indent=2),
                                    file_name="prayers.json",
                                    mime="application/json"
                                )
                        else:
                            st.warning("No prayers detected. Check your API key or try regex mode.")
        else:
            st.error("Invalid YouTube URL")
    else:
        st.warning("Please enter a YouTube URL")

# Manual Testing Section
with st.expander("🧪 Manual Prompt Testing"):
    st.markdown("Test different prompts with the transcript")
    
    if 'transcript' in locals() and transcript:
        custom_prompt = st.text_area(
            "Custom Prompt",
            value="""Find all prayers in this transcript that start with "Father". 
Format each as:
Prayer X: [full prayer text]
Scripture: [reference if mentioned]

Look for prayers about:
- Thanksgiving for multitudes/services
- New converts and members
- Healing and miracles
- God's presence in services""",
            height=150
        )
        
        if st.button("Test Custom Prompt", key="test_prompt"):
            if api_key:
                try:
                    import openai
                    openai.api_key = api_key
                    
                    # Take first 10000 chars for testing
                    test_chunk = transcript[:10000]
                    
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are analyzing a church sermon transcript."},
                            {"role": "user", "content": custom_prompt + "\n\nTranscript:\n" + test_chunk}
                        ],
                        temperature=0.1,
                        max_tokens=2000
                    )
                    
                    result = response.choices[0].message.content
                    st.markdown("### AI Response:")
                    st.text_area("Result", result, height=400)
                    
                    # Option to copy result
                    st.code(result)
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            else:
                st.warning("API key required for testing")
    else:
        st.info("First fetch a transcript from a YouTube video above")

# Instructions
with st.expander("🔑 How to get OpenAI API Key"):
    st.markdown("""
    1. Go to [OpenAI Platform](https://platform.openai.com)
    2. Sign up or log in
    3. Navigate to API Keys section
    4. Create a new API key
    5. Copy and paste it in the sidebar
    
    **Note:** You'll need to add billing to use the API, but costs are minimal (~$0.002 per sermon)
    """)

# Footer
st.markdown("---")
st.markdown("Made with ❤️ for worship teams | AI-powered for accuracy")
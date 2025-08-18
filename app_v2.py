"""
Sanctum - Prayer Slides Generator V2
Enhanced version with proper slide formatting matching EasyWorship style
"""

import streamlit as st
import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import io

st.set_page_config(
    page_title="Sanctum - Prayer Slides Generator",
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
    """Fetch transcript from YouTube video"""
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        # Try to find English transcript first, then any available
        try:
            transcript = transcript_list.find_transcript(['en'])
        except:
            # Get first available transcript in any language
            transcript = transcript_list.find_generated_transcript(['en'])
            if not transcript:
                available = transcript_list._get_fetched_transcripts()
                if available:
                    transcript = list(available.values())[0]
        
        # Fetch the actual transcript data
        transcript_data = transcript.fetch()
        
        # Format the transcript
        formatter = TextFormatter()
        formatted_transcript = formatter.format_transcript(transcript_data)
        return formatted_transcript
    except Exception as e:
        return None, str(e)

def extract_prayers_structured(transcript):
    """
    Extract prayers with structure matching the screenshot format
    Returns list of prayer objects with prayer text and scripture
    """
    prayers = []
    
    # Normalize transcript
    text = re.sub(r'\s+', ' ', transcript)
    
    # First, look for explicit prayer markers with better capture
    # Pattern 1: "prayer" followed by content until next prayer or scripture
    prayer_sections = re.split(r'(?i)(?:prayer\s*(?:point)?\s*\d*[:.]?\s*|let\s+us\s+pray)', text)
    
    for i, section in enumerate(prayer_sections[1:], 1):  # Skip first section before any prayer
        if len(section.strip()) > 20:  # Must have substantial content
            # Extract the prayer content - look for "Father" prayers
            father_match = re.search(r'(?i)(father[^.]*(?:\.[^.]*){0,5})', section)
            
            if father_match:
                prayer_text = father_match.group(1).strip()
            else:
                # Take the first substantial part of the section
                sentences = re.split(r'[.!?]+', section)
                prayer_text = '. '.join(sentences[:3]).strip()
            
            # Look for scripture reference
            scripture = ""
            scripture_patterns = [
                r'([A-Z][a-z]+\s+\d+[:\s]+\d+)',  # Simple: Genesis 1:1
                r'([A-Z][a-z]+\s+chapter\s+\d+\s+verse\s+\d+)',  # Full: Genesis chapter 1 verse 1
                r'Scripture:?\s*"?([^"]+)"?',  # Explicit scripture marker
            ]
            
            for pattern in scripture_patterns:
                scripture_match = re.search(pattern, section, re.IGNORECASE)
                if scripture_match:
                    scripture = scripture_match.group(1) if scripture_match.group(1) else scripture_match.group(0)
                    scripture = format_scripture_reference(scripture.strip())
                    break
            
            # Clean prayer text
            prayer_text = re.sub(r'\s+', ' ', prayer_text)
            prayer_text = prayer_text.strip('"').strip()
            
            # Only add if we have meaningful content
            if len(prayer_text) > 30:
                prayers.append({
                    'number': str(i),
                    'prayer': prayer_text,
                    'scripture': scripture
                })
    
    # If no prayers found with markers, look for Father prayers directly
    if not prayers:
        # Pattern for prayers starting with "Father"
        father_pattern = r'(?i)(father[^.]*(?:\.[^.]*){1,5})'
        father_matches = re.finditer(father_pattern, text)
        
        for i, match in enumerate(father_matches, 1):
            prayer_text = match.group(1).strip()
            
            # Look for scripture near this prayer
            scripture = ""
            context = text[match.end():match.end() + 300]
            scripture_patterns = [
                r'([A-Z][a-z]+\s+\d+[:\s]+\d+)',
                r'([A-Z][a-z]+\s+chapter\s+\d+\s+verse\s+\d+)',
            ]
            
            for pattern in scripture_patterns:
                scripture_match = re.search(pattern, context, re.IGNORECASE)
                if scripture_match:
                    scripture = format_scripture_reference(scripture_match.group(1))
                    break
            
            # Clean and validate
            prayer_text = re.sub(r'\s+', ' ', prayer_text).strip()
            
            if len(prayer_text) > 30 and len(prayer_text) < 1000:  # Reasonable length
                prayers.append({
                    'number': str(i),
                    'prayer': prayer_text,
                    'scripture': scripture
                })
    
    return prayers[:20]  # Limit to first 20 prayers to avoid noise

def format_scripture_reference(scripture):
    """Format scripture reference to match slide style (e.g., PSA. 115:1)"""
    # Common book abbreviations
    abbreviations = {
        'genesis': 'GEN.',
        'exodus': 'EXO.',
        'leviticus': 'LEV.',
        'numbers': 'NUM.',
        'deuteronomy': 'DEU.',
        'psalms': 'PSA.',
        'psalm': 'PSA.',
        'proverbs': 'PRO.',
        'matthew': 'MAT.',
        'mark': 'MAR.',
        'luke': 'LUK.',
        'john': 'JOH.',
        'acts': 'ACT.',
        'romans': 'ROM.',
        'corinthians': 'COR.',
        'galatians': 'GAL.',
        'ephesians': 'EPH.',
        'philippians': 'PHI.',
        'colossians': 'COL.',
        'thessalonians': 'THE.',
        'timothy': 'TIM.',
        'titus': 'TIT.',
        'hebrews': 'HEB.',
        'james': 'JAM.',
        'peter': 'PET.',
        'revelation': 'REV.',
        'zechariah': 'ZEC.',
    }
    
    # Clean up the reference
    scripture = re.sub(r'\s+', ' ', scripture).strip()
    
    # Extract book and reference
    match = re.match(r'([A-Za-z]+(?:\s+[A-Za-z]+)?)\s*(?:chapter\s+)?(\d+)[\s:]+(?:verse\s+)?(\d+)', scripture, re.IGNORECASE)
    
    if match:
        book = match.group(1).lower()
        chapter = match.group(2)
        verse = match.group(3)
        
        # Get abbreviation
        abbrev = abbreviations.get(book, book.upper()[:3] + '.')
        
        return f"{abbrev} {chapter}:{verse}"
    
    return scripture.upper()

def format_slide_text(text, max_chars=350):
    """
    Format text for slide display in ALL CAPS with proper line breaks
    Matches the style shown in the screenshot
    """
    # Convert to uppercase
    text = text.upper()
    
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Split into chunks that fit on screen
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    max_line_chars = 60  # Approximate characters per line
    
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
    
    # Group lines into slides if too many
    if len(lines) > 8:  # Max 8 lines per slide
        return split_into_multiple_slides(lines)
    
    return ['\n'.join(lines)]

def split_into_multiple_slides(lines, max_lines=8):
    """Split lines into multiple slides if needed"""
    slides = []
    for i in range(0, len(lines), max_lines):
        slide_lines = lines[i:i+max_lines]
        slides.append('\n'.join(slide_lines))
    return slides

def generate_prayer_slides(prayers, include_prayer_number=True):
    """
    Generate slides in EasyWorship format matching the screenshot style
    
    Format per slide:
    - Header: PRAYER [NUMBER]
    - Content: Prayer text in ALL CAPS
    - Footer: Scripture reference
    - Separator: Blank line between slides
    """
    all_slides = []
    
    for prayer in prayers:
        # Prepare header
        if include_prayer_number and prayer['number']:
            header = f"PRAYER {prayer['number']}"
        else:
            header = "PRAYER"
        
        # Format prayer text
        prayer_slides = format_slide_text(prayer['prayer'])
        
        # Create slides
        for i, slide_text in enumerate(prayer_slides):
            slide_parts = [header]
            slide_parts.append("")  # Blank line after header
            slide_parts.append(slide_text)
            
            # Add scripture reference at the bottom (only on last slide of multi-part prayer)
            if prayer['scripture'] and i == len(prayer_slides) - 1:
                slide_parts.append("")  # Blank line before scripture
                slide_parts.append(prayer['scripture'])
            
            all_slides.append('\n'.join(slide_parts))
    
    return '\n\n---\n\n'.join(all_slides)  # Use --- as slide separator for clarity

# Streamlit UI
st.title("🙏 Sanctum - Prayer Slides Generator V2")
st.markdown("Generate EasyWorship-ready prayer slides with proper formatting")

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")
    
    include_numbers = st.checkbox("Include Prayer Numbers", value=True, 
                                 help="Add prayer numbers to headers (PRAYER 1, PRAYER 2, etc.)")
    
    format_style = st.selectbox("Format Style", 
                               ["EasyWorship (ALL CAPS)", "ProPresenter (Title Case)", "Custom"],
                               help="Choose text formatting style")
    
    max_lines = st.slider("Max Lines per Slide", 4, 10, 8,
                         help="Maximum lines of text per slide")
    
    st.markdown("---")
    st.markdown("### 📖 About")
    st.markdown("""
    This enhanced version formats prayers to match 
    professional worship slide standards:
    - Structured headers
    - ALL CAPS text
    - Scripture references
    - Proper slide breaks
    """)

# Main input area
youtube_url = st.text_input(
    "YouTube Video URL",
    placeholder="https://www.youtube.com/watch?v=... or /live/...",
    help="Paste the full YouTube URL of the sermon"
)

# Generate button
if st.button("🎬 Generate Prayer Slides", type="primary"):
    if youtube_url:
        # Extract video ID
        video_id = extract_video_id(youtube_url)
        
        if video_id:
            with st.spinner("Fetching transcript..."):
                result = fetch_transcript(video_id)
                
                if isinstance(result, tuple):
                    transcript, error = result
                    st.error(f"Error fetching transcript: {error}")
                else:
                    transcript = result
                    
                    with st.spinner("Extracting and formatting prayers..."):
                        prayers = extract_prayers_structured(transcript)
                        
                        if prayers:
                            st.success(f"✅ Found {len(prayers)} prayer(s)")
                            
                            # Generate formatted slides
                            formatted_slides = generate_prayer_slides(prayers, include_numbers)
                            
                            # Preview in columns
                            st.markdown("### 📄 Preview")
                            
                            # Show first few slides
                            slides_list = formatted_slides.split('\n\n---\n\n')
                            
                            # Display in tabs for better organization
                            if len(slides_list) > 1:
                                tabs = st.tabs([f"Prayer {i+1}" for i in range(min(5, len(slides_list)))])
                                for i, tab in enumerate(tabs):
                                    if i < len(slides_list):
                                        with tab:
                                            # Simulate slide appearance
                                            st.code(slides_list[i], language=None)
                                
                                if len(slides_list) > 5:
                                    st.info(f"... and {len(slides_list) - 5} more slides")
                            else:
                                st.code(slides_list[0], language=None)
                            
                            # Statistics
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total Prayers", len(prayers))
                            with col2:
                                st.metric("Total Slides", len(slides_list))
                            with col3:
                                scriptures = sum(1 for p in prayers if p['scripture'])
                                st.metric("With Scripture", scriptures)
                            
                            # Download section
                            st.markdown("### 💾 Download Options")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                # Standard format for EasyWorship
                                easyworship_format = formatted_slides.replace('---', '')  # Remove visual separators
                                st.download_button(
                                    label="📥 Download for EasyWorship",
                                    data=easyworship_format,
                                    file_name="prayer_slides_easyworship.txt",
                                    mime="text/plain",
                                    help="Double-spaced format for EasyWorship import"
                                )
                            
                            with col2:
                                # Alternative format with clear separators
                                st.download_button(
                                    label="📥 Download with Separators",
                                    data=formatted_slides,
                                    file_name="prayer_slides_formatted.txt",
                                    mime="text/plain",
                                    help="Includes visual separators between slides"
                                )
                            
                        else:
                            st.warning("No prayers detected. Try adjusting detection settings or check the transcript.")
                            
                            # Show sample of transcript for debugging
                            with st.expander("🔍 View Transcript Sample"):
                                st.text(transcript[:2000] + "..." if len(transcript) > 2000 else transcript)
        else:
            st.error("Invalid YouTube URL. Please check and try again.")
    else:
        st.warning("Please enter a YouTube URL")

# Instructions
with st.expander("📖 How to Import into EasyWorship"):
    st.markdown("""
    1. **Download the file** using the button above
    2. **Open EasyWorship**
    3. Go to **Songs → Import → Import Songs**
    4. Select **Plain Text** as the format
    5. Choose your downloaded file
    6. Each double-spaced section becomes a slide
    7. Review and adjust formatting as needed
    
    **Tip:** The prayers are formatted to match standard worship slide style:
    - Headers show prayer numbers
    - Text is in ALL CAPS for visibility
    - Scripture references appear at the bottom
    """)

# Footer
st.markdown("---")
st.markdown("Made with ❤️ for worship teams | [Report Issue](https://github.com/Mike-Ew/sanctum/issues)")
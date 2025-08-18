"""
Sanctum - Prayer Slides Generator
Extracts prayers from YouTube sermons and formats them for EasyWorship
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

def extract_prayers(transcript):
    """Extract prayer sections from transcript"""
    # Prayer detection keywords and patterns
    prayer_indicators = [
        r'let us pray',
        r'let\'s pray',
        r'father we',
        r'lord we',
        r'dear god',
        r'dear lord',
        r'heavenly father',
        r'we thank you',
        r'we praise you',
        r'in jesus name',
        r'in jesus\' name',
        r'amen'
    ]
    
    # Split transcript into sentences
    sentences = re.split(r'(?<=[.!?])\s+', transcript)
    
    prayers = []
    in_prayer = False
    current_prayer = []
    
    for sentence in sentences:
        sentence_lower = sentence.lower()
        
        # Check if sentence contains prayer indicators
        has_prayer_indicator = any(indicator in sentence_lower or re.search(indicator, sentence_lower) 
                                  for indicator in prayer_indicators)
        
        if has_prayer_indicator and not in_prayer:
            in_prayer = True
            current_prayer = [sentence]
        elif in_prayer:
            current_prayer.append(sentence)
            # End prayer at "amen" or after significant break
            if 'amen' in sentence_lower or len(current_prayer) > 15:
                prayers.append(' '.join(current_prayer))
                current_prayer = []
                in_prayer = False
    
    # Add any remaining prayer
    if current_prayer:
        prayers.append(' '.join(current_prayer))
    
    return prayers

def clean_text(text):
    """Clean prayer text for slides"""
    # Remove timestamps
    text = re.sub(r'\[\d+:\d+\]', '', text)
    text = re.sub(r'\d+:\d+', '', text)
    
    # Remove filler words and sounds
    fillers = ['um', 'uh', 'ah', 'er', 'hmm', 'you know', 'like']
    for filler in fillers:
        text = re.sub(r'\b' + filler + r'\b', '', text, flags=re.IGNORECASE)
    
    # Clean up extra spaces and punctuation
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s+([.,!?])', r'\1', text)
    text = text.strip()
    
    return text

def chunk_text(text, max_chars=150, max_lines=4):
    """Split text into slide-sized chunks"""
    chunks = []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence_length = len(sentence)
        
        # Check if adding this sentence exceeds limits
        if current_length + sentence_length > max_chars or len(current_chunk) >= max_lines:
            if current_chunk:
                chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_length = sentence_length
        else:
            current_chunk.append(sentence)
            current_length += sentence_length + 1  # +1 for space
    
    # Add remaining chunk
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

def format_for_easyworship(prayers):
    """Format prayers for EasyWorship import"""
    slides = []
    
    for prayer in prayers:
        # Clean the prayer text
        cleaned = clean_text(prayer)
        
        # Split into chunks
        chunks = chunk_text(cleaned)
        
        # Add chunks as slides
        slides.extend(chunks)
    
    # Join with double newlines (EasyWorship format)
    return '\n\n'.join(slides)

# Streamlit UI
st.title("🙏 Sanctum - Prayer Slides Generator")
st.markdown("Generate EasyWorship-ready prayer slides from YouTube sermons")

# Input section
youtube_url = st.text_input(
    "YouTube Video URL",
    placeholder="https://www.youtube.com/watch?v=...",
    help="Paste the full YouTube URL of the sermon"
)

# Settings
with st.expander("⚙️ Settings"):
    max_chars = st.slider("Max characters per slide", 50, 300, 150)
    max_lines = st.slider("Max lines per slide", 2, 6, 4)

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
                    
                    with st.spinner("Extracting prayers..."):
                        prayers = extract_prayers(transcript)
                        
                        if prayers:
                            st.success(f"Found {len(prayers)} prayer section(s)")
                            
                            # Format for EasyWorship
                            formatted_slides = format_for_easyworship(prayers)
                            
                            # Preview
                            with st.expander("📄 Preview Slides"):
                                slides_preview = formatted_slides.split('\n\n')
                                for i, slide in enumerate(slides_preview[:5], 1):
                                    st.text(f"Slide {i}:")
                                    st.info(slide)
                                if len(slides_preview) > 5:
                                    st.text(f"... and {len(slides_preview) - 5} more slides")
                            
                            # Download button
                            st.download_button(
                                label="📥 Download slides.txt",
                                data=formatted_slides,
                                file_name="prayer_slides.txt",
                                mime="text/plain"
                            )
                        else:
                            st.warning("No prayers detected in the transcript. Try adjusting the detection settings.")
        else:
            st.error("Invalid YouTube URL. Please check and try again.")
    else:
        st.warning("Please enter a YouTube URL")

# Instructions
with st.expander("📖 How to Use"):
    st.markdown("""
    1. **Paste YouTube URL**: Copy the full URL of the sermon video
    2. **Click Generate**: The app will fetch the transcript and extract prayers
    3. **Download slides.txt**: Save the generated file
    4. **Import to EasyWorship**: 
       - Open EasyWorship
       - Go to Songs > Import
       - Select the slides.txt file
       - Each paragraph becomes a slide
    """)

# Footer
st.markdown("---")
st.markdown("Made with ❤️ for worship teams everywhere")
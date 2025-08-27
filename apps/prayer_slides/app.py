import streamlit as st
import re
from youtube_transcript_api import YouTubeTranscriptApi
import validators

def extract_video_id(url):
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:watch\?v=)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def fetch_transcript(video_id):
    try:
        # Create API instance and fetch transcript
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
        
        # Extract text from snippets
        full_text = ' '.join([snippet.text for snippet in transcript.snippets])
        return full_text
    except Exception as e:
        st.error(f"Error fetching transcript: {str(e)}")
        return None

def extract_prayers(text):
    prayer_keywords = [
        r'let us pray',
        r'let\'s pray',
        r'father we',
        r'lord we',
        r'dear god',
        r'dear lord',
        r'heavenly father',
        r'we pray',
        r'we thank you',
        r'in jesus name',
        r'amen'
    ]
    
    pattern = '|'.join(prayer_keywords)
    sentences = text.split('.')
    
    prayer_sections = []
    in_prayer = False
    current_prayer = []
    
    for sentence in sentences:
        sentence_lower = sentence.lower().strip()
        
        if any(keyword in sentence_lower for keyword in ['let us pray', 'let\'s pray', 'father we', 'lord we', 'dear god', 'dear lord', 'heavenly father']):
            in_prayer = True
            current_prayer = [sentence.strip()]
        elif in_prayer:
            current_prayer.append(sentence.strip())
            if 'amen' in sentence_lower:
                prayer_sections.append('. '.join(current_prayer))
                in_prayer = False
                current_prayer = []
        elif re.search(pattern, sentence_lower) and len(sentence.strip()) > 20:
            context_start = max(0, sentences.index(sentence) - 1)
            context_end = min(len(sentences), sentences.index(sentence) + 3)
            context = '. '.join(sentences[context_start:context_end])
            if len(context) > 50:
                prayer_sections.append(context.strip())
    
    if in_prayer and current_prayer:
        prayer_sections.append('. '.join(current_prayer))
    
    return prayer_sections

def clean_text(text):
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'(?:um|uh|you know|like|I mean|actually),?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\.{2,}', '.', text)
    text = re.sub(r'\s+([,.!?])', r'\1', text)
    
    return text.strip()

def chunk_into_slides(text, max_chars=200, max_lines=4):
    sentences = text.split('. ')
    slides = []
    current_slide = []
    current_length = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        sentence_with_period = sentence if sentence.endswith('.') else sentence + '.'
        sentence_length = len(sentence_with_period)
        
        if current_length + sentence_length > max_chars or len(current_slide) >= max_lines:
            if current_slide:
                slides.append(' '.join(current_slide))
            current_slide = [sentence_with_period]
            current_length = sentence_length
        else:
            current_slide.append(sentence_with_period)
            current_length += sentence_length + 1
    
    if current_slide:
        slides.append(' '.join(current_slide))
    
    return slides

def format_for_easyworship(slides):
    return '\n\n'.join(slides)

st.set_page_config(
    page_title="Prayer Slides Generator",
    page_icon="🙏",
    layout="centered"
)

st.title("🙏 Prayer Slides Generator")
st.markdown("Generate EasyWorship-ready prayer slides from YouTube sermons")

st.markdown("---")

youtube_url = st.text_input(
    "Enter YouTube URL:",
    placeholder="https://www.youtube.com/watch?v=..."
)

col1, col2 = st.columns([1, 1])
with col1:
    max_chars = st.slider("Max characters per slide", 100, 400, 200)
with col2:
    max_lines = st.slider("Max lines per slide", 2, 6, 4)

if st.button("Generate Prayer Slides", type="primary"):
    if youtube_url:
        if not validators.url(youtube_url):
            st.error("Please enter a valid URL")
        else:
            video_id = extract_video_id(youtube_url)
            
            if not video_id:
                st.error("Could not extract video ID from URL")
            else:
                with st.spinner("Fetching transcript..."):
                    transcript = fetch_transcript(video_id)
                
                if transcript:
                    with st.spinner("Extracting prayers..."):
                        prayers = extract_prayers(transcript)
                    
                    if prayers:
                        st.success(f"Found {len(prayers)} prayer section(s)")
                        
                        all_slides = []
                        for i, prayer in enumerate(prayers, 1):
                            cleaned = clean_text(prayer)
                            slides = chunk_into_slides(cleaned, max_chars, max_lines)
                            all_slides.extend(slides)
                        
                        output_text = format_for_easyworship(all_slides)
                        
                        st.subheader("Preview")
                        with st.expander(f"View all {len(all_slides)} slides"):
                            for i, slide in enumerate(all_slides, 1):
                                st.text(f"Slide {i}:")
                                st.info(slide)
                                st.markdown("---")
                        
                        st.download_button(
                            label="📥 Download slides.txt",
                            data=output_text,
                            file_name="prayer_slides.txt",
                            mime="text/plain"
                        )
                    else:
                        st.warning("No prayer sections found in the transcript. Try adjusting the detection settings or check if the video contains prayers.")
    else:
        st.warning("Please enter a YouTube URL")

st.markdown("---")
with st.expander("ℹ️ How to use"):
    st.markdown("""
    1. **Paste a YouTube link** of a sermon or service
    2. **Adjust settings** for slide length if needed
    3. **Click Generate** to extract and format prayers
    4. **Download** the formatted text file
    5. **Import** into EasyWorship (each paragraph becomes a slide)
    
    **Tips:**
    - Works best with videos that have captions/transcripts
    - Prayer detection looks for keywords like "Let us pray", "Father we", etc.
    - Adjust character/line limits based on your screen size
    """)

st.markdown("---")
st.caption("Prayer Slides Generator v1.0 | Built with Streamlit")
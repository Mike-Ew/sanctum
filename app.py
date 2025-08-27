import streamlit as st
from src.transcript import get_transcript
from src.prayer_extractor import extract_prayers_with_ai
from src.bible_fetcher import fetch_verse
from src.auth import check_password, logout
import os
from dotenv import load_dotenv

load_dotenv()

st.title("Sanctum - Prayer Extractor")

# Check authentication
if not check_password():
    st.stop()

# Settings sidebar
with st.sidebar:
    st.header("Settings")
    
    # Add logout button at top of sidebar
    if st.button("🚪 Logout", use_container_width=True):
        logout()
    
    st.divider()
    
    # Try to get API key from multiple sources
    api_key = ""
    
    # First try Streamlit secrets
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
        st.success("✅ API Key loaded from secrets")
    # Then try environment variables
    elif os.getenv("OPENAI_API_KEY"):
        api_key = os.getenv("OPENAI_API_KEY", "")
        st.success("✅ API Key loaded from .env")
    # Finally allow manual input
    else:
        api_key = st.text_input("OpenAI API Key", type="password")
    
    model = st.selectbox(
        "AI Model",
        ["gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-4o", "gpt-3.5-turbo"],
        index=1  # Default to gpt-5-mini
    )
    
    # Pricing information
    st.divider()
    st.subheader("💰 Pricing (per 1M tokens)")
    pricing_info = {
        "gpt-5": "$20 input / $60 output",
        "gpt-5-mini": "$5 input / $15 output",
        "gpt-5-nano": "$2 input / $8 output",
        "gpt-4o": "$2.50 input / $10 output",
        "gpt-3.5-turbo": "$0.50 input / $1.50 output"
    }
    st.info(pricing_info.get(model, "Pricing not available"))
    
    # Token limits
    st.subheader("📊 Token Limits")
    token_limits = {
        "gpt-5": "400K total (272K input)",
        "gpt-5-mini": "400K total (272K input)",
        "gpt-5-nano": "400K total (272K input)",
        "gpt-4o": "128K context window",
        "gpt-3.5-turbo": "16K context window"
    }
    st.info(token_limits.get(model, "Limits not available"))
    
    extraction_method = st.radio(
        "Extraction Method",
        ["AI (OpenAI)", "Transcript Only"]
    )

# Main interface
url = st.text_input("Enter YouTube URL:")

if st.button("Extract Prayers"):
    if url:
        # Extract video ID
        if "youtube.com/watch?v=" in url:
            video_id = url.split("watch?v=")[1].split("&")[0]
        elif "youtube.com/live/" in url:
            video_id = url.split("youtube.com/live/")[1].split("?")[0]
        elif "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0]
        else:
            video_id = url
        
        st.write(f"Video ID: {video_id}")
        
        # Get transcript
        with st.spinner("Fetching transcript..."):
            transcript = get_transcript(video_id)
        
        if transcript:
            st.success(f"Found {len(transcript)} segments")
            
            # Combine transcript text
            full_text = " ".join([s.text for s in transcript])
            
            if extraction_method == "AI (OpenAI)":
                if not api_key:
                    st.error("Please provide an OpenAI API key")
                else:
                    # Show transcript info
                    char_count = len(full_text)
                    token_estimate = char_count // 4  # Rough estimate
                    
                    st.info(f"📝 Processing {char_count:,} characters (~{token_estimate:,} tokens)")
                    
                    # Show transcript preview for non-GPT-5 models
                    if model.startswith('gpt-5'):
                        with st.expander(f"View Full Transcript (all {char_count:,} chars being analyzed)"):
                            st.text_area("Transcript being analyzed:", value=full_text, height=300)
                    else:
                        limit = 30000 if not model.startswith('gpt-3.5') else 10000
                        with st.expander(f"View Transcript (first {limit:,} chars being analyzed)"):
                            st.text_area("Transcript being analyzed:", value=full_text[:limit], height=300)
                    
                    with st.spinner(f"Extracting prayers with {model}..."):
                        try:
                            prayers = extract_prayers_with_ai(full_text, api_key, model)
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                            prayers = []
                    
                    if prayers:
                        st.success(f"Extracted {len(prayers)} prayer points")
                        
                        # Fetch Bible verses automatically from API (override any AI-extracted verses)
                        with st.spinner("Fetching Bible verses from KJV..."):
                            for prayer in prayers:
                                if prayer.get('scripture'):
                                    verse_result = fetch_verse(prayer['scripture'])
                                    if not verse_result['error']:
                                        # Always use API verse, even if AI provided one
                                        prayer['verse_text'] = verse_result['text']
                                        prayer['verse_source'] = 'Bible API'
                                        st.caption(f"✅ Fetched {prayer['scripture']}: {verse_result['text'][:50]}...")
                                    else:
                                        st.caption(f"⚠️ Could not fetch {prayer['scripture']}: {verse_result['error']}")
                        
                        # Display prayers with separate scripture slides
                        st.subheader("📋 Prayer Points for EasyWorship")
                        
                        # Export button
                        col1, col2 = st.columns([3, 1])
                        with col2:
                            # Generate export text
                            export_text = ""
                            for i, prayer in enumerate(prayers, 1):
                                # Prayer slide
                                export_text += f"PRAYER {i}\n"
                                export_text += "=" * 50 + "\n"
                                export_text += prayer.get('text', '').upper() + "\n\n"
                                export_text += prayer.get('scripture', '').upper() + "\n"
                                export_text += "\n" + "=" * 50 + "\n\n"
                                
                                # Scripture slide
                                if prayer.get('scripture') and prayer.get('verse_text'):
                                    export_text += f"SCRIPTURE {i}\n"
                                    export_text += "=" * 50 + "\n"
                                    export_text += prayer.get('scripture', '').upper() + " (KJV)\n\n"
                                    export_text += prayer.get('verse_text', '').upper() + "\n"
                                    export_text += "\n" + "=" * 50 + "\n\n"
                            
                            # Download button
                            st.download_button(
                                label="📥 Export to TXT",
                                data=export_text,
                                file_name="prayer_points.txt",
                                mime="text/plain",
                                help="Download formatted text file for EasyWorship"
                            )
                        
                        # Create tabs for different views
                        tab1, tab2, tab3, tab4 = st.tabs(["Slide View", "Prayer Points Only", "Scriptures Only", "Export Preview"])
                        
                        with tab1:
                            # Show as slides (prayer + scripture separately)
                            for i, prayer in enumerate(prayers, 1):
                                # Prayer slide
                                st.markdown(f"### 📋 PRAYER {i}")
                                prayer_text = prayer.get('text', '').upper()
                                scripture_ref = prayer.get('scripture', '')
                                
                                # Format for EasyWorship prayer slide
                                prayer_slide = f"{prayer_text}\n\n{scripture_ref}"
                                # Calculate height based on text length (roughly 20 pixels per line)
                                lines = len(prayer_slide.split('\n')) + prayer_slide.count('\n') + (len(prayer_slide) // 80)
                                height = max(150, lines * 25)
                                st.text_area(
                                    f"Prayer {i} Slide (Copy to EasyWorship):",
                                    value=prayer_slide,
                                    height=height,
                                    key=f"prayer_{i}"
                                )
                                
                                # Scripture slide (if scripture exists)
                                if scripture_ref:
                                    st.markdown(f"### 📖 SCRIPTURE {i}")
                                    verse_text = prayer.get('verse_text', '')
                                    if verse_text:
                                        # Show FULL verse from API in CAPS
                                        scripture_slide = f"{scripture_ref.upper()} (KJV)\n\n{verse_text.upper()}"
                                        # Auto-adjust height for verse text
                                        lines = len(scripture_slide.split('\n')) + scripture_slide.count('\n') + (len(scripture_slide) // 80)
                                        height = max(120, lines * 25)
                                        st.text_area(
                                            f"Scripture {i} Slide (Copy to EasyWorship):",
                                            value=scripture_slide,
                                            height=height,
                                            key=f"scripture_{i}"
                                        )
                                    else:
                                        st.info(f"Scripture Reference: {scripture_ref} (KJV)")
                                        st.caption("Note: Verse text not found in transcript")
                                
                                st.divider()
                        
                        with tab2:
                            # Prayer points formatted for EasyWorship
                            st.markdown("### For EasyWorship Prayer Slides")
                            for i, prayer in enumerate(prayers, 1):
                                prayer_content = f"{prayer.get('text', '').upper()}\n\n{prayer.get('scripture', '')}"
                                # Auto-adjust height
                                lines = len(prayer_content.split('\n')) + prayer_content.count('\n') + (len(prayer_content) // 80)
                                height = max(120, lines * 25)
                                st.text_area(
                                    f"PRAYER {i}:",
                                    value=prayer_content,
                                    height=height,
                                    key=f"prayer_only_{i}"
                                )
                        
                        with tab3:
                            # Scripture references for verse slides
                            st.markdown("### Scripture References for Verse Slides")
                            scriptures_text = "\n".join([
                                f"SCRIPTURE {i+1}: {p.get('scripture', '').upper()} (KJV)"
                                for i, p in enumerate(prayers) if p.get('scripture')
                            ])
                            st.text_area(
                                "All Scripture References:",
                                value=scriptures_text,
                                height=150
                            )
                            st.info("📌 Verses fetched from Bible API - Complete KJV text")
                        
                        with tab4:
                            # Export preview
                            st.markdown("### Export Preview (TXT File)")
                            st.text_area(
                                "This is what will be exported:",
                                value=export_text,
                                height=500,
                                help="All text in CAPS for EasyWorship"
                            )
                    else:
                        st.warning("No prayers found")
            else:
                # Show transcript only - same format as sent to AI
                st.text_area("Full Transcript (as sent to AI):", value=full_text, height=500)
        else:
            st.error("Failed to fetch transcript")
            st.info("""
            **Possible reasons:**
            - Video doesn't have captions/subtitles enabled
            - Transcripts are disabled by the uploader
            - Live stream still in progress
            - Private or age-restricted video
            
            **Try:**
            - Check if the video has CC (Closed Captions) button on YouTube
            - Try a different video from your church
            - Wait if it's a recent live stream (transcripts generate after stream ends)
            """)
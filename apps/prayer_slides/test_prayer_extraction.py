#!/usr/bin/env python3
"""Test script for prayer extraction from YouTube video"""

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
import re

def extract_video_id(url):
    """Extract video ID from YouTube URL"""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:watch\?v=)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
        r'(?:live\/)([0-9A-Za-z_-]{11})'  # Added pattern for live videos
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def fetch_transcript(video_id):
    """Fetch transcript from YouTube"""
    try:
        # Create API instance and fetch transcript
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
        
        # Extract text from snippets
        full_text = ' '.join([snippet.text for snippet in transcript.snippets])
        return full_text
    except (NoTranscriptFound, TranscriptsDisabled) as e:
        print(f"No transcript available: {str(e)}")
        return None
    except Exception as e:
        print(f"Error fetching transcript: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return None

def extract_prayers(text):
    """Extract prayer sections from transcript"""
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
    
    sentences = text.split('.')
    prayer_sections = []
    in_prayer = False
    current_prayer = []
    
    for sentence in sentences:
        sentence_lower = sentence.lower().strip()
        
        # Check if prayer starts
        if any(keyword in sentence_lower for keyword in ['let us pray', 'let\'s pray', 'father we', 'lord we', 'dear god', 'dear lord', 'heavenly father']):
            in_prayer = True
            current_prayer = [sentence.strip()]
        elif in_prayer:
            current_prayer.append(sentence.strip())
            # Check if prayer ends
            if 'amen' in sentence_lower:
                prayer_sections.append('. '.join(current_prayer))
                in_prayer = False
                current_prayer = []
    
    # Add any remaining prayer
    if in_prayer and current_prayer:
        prayer_sections.append('. '.join(current_prayer))
    
    return prayer_sections

def clean_text(text):
    """Clean text from fillers and formatting issues"""
    # Remove brackets and parentheses
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    # Remove filler words
    text = re.sub(r'(?:um|uh|you know|like|I mean|actually),?\s*', '', text, flags=re.IGNORECASE)
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\.{2,}', '.', text)
    text = re.sub(r'\s+([,.!?])', r'\1', text)
    
    return text.strip()

def chunk_into_slides(text, max_chars=200, max_lines=4):
    """Split text into slide-sized chunks"""
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

# Test with the provided YouTube URL
url = "https://www.youtube.com/live/x0IhRd7P9LY?si=UX0LmJN_lzv6IxZ-"
print(f"Testing with URL: {url}")
print("=" * 60)

# Extract video ID
video_id = extract_video_id(url)
print(f"Extracted Video ID: {video_id}")
print()

if video_id:
    # Fetch transcript
    print("Fetching transcript...")
    transcript = fetch_transcript(video_id)
    
    if transcript:
        print(f"Transcript fetched! Length: {len(transcript)} characters")
        print("\nFirst 500 characters of transcript:")
        print(transcript[:500])
        print("\n" + "=" * 60)
        
        # Extract prayers
        print("\nExtracting prayers...")
        prayers = extract_prayers(transcript)
        
        if prayers:
            print(f"Found {len(prayers)} prayer section(s)!")
            
            all_slides = []
            for i, prayer in enumerate(prayers, 1):
                print(f"\n--- Prayer Section {i} ---")
                print(f"Original length: {len(prayer)} characters")
                
                # Clean the prayer text
                cleaned = clean_text(prayer)
                print(f"Cleaned length: {len(cleaned)} characters")
                
                # Chunk into slides
                slides = chunk_into_slides(cleaned)
                all_slides.extend(slides)
                
                print(f"Created {len(slides)} slides from this prayer")
                
                # Show first 2 slides as preview
                for j, slide in enumerate(slides[:2], 1):
                    print(f"\nSlide {j}:")
                    print(slide)
            
            # Save to file
            output_text = '\n\n'.join(all_slides)
            with open('prayer_slides_output.txt', 'w') as f:
                f.write(output_text)
            
            print("\n" + "=" * 60)
            print(f"✅ Total slides created: {len(all_slides)}")
            print("📄 Output saved to: prayer_slides_output.txt")
            
        else:
            print("No prayer sections found in the transcript.")
            print("The video might not contain explicit prayer sections.")
    else:
        print("Could not fetch transcript. The video might not have captions enabled.")
else:
    print("Could not extract video ID from the URL.")
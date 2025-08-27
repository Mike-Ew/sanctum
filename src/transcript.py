from youtube_transcript_api import YouTubeTranscriptApi

def get_transcript(video_id, languages=['en']):
    """
    Fetch transcript for a YouTube video
    
    Args:
        video_id: YouTube video ID
        languages: List of language codes in priority order
        
    Returns:
        List of transcript segments with 'text', 'start', 'duration'
        or None if transcript not available
    """
    try:
        # Use the static method directly
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        return transcript
    except Exception as e:
        print(f"Error fetching transcript: {str(e)}")
        return None
from youtube_transcript_api import YouTubeTranscriptApi
import traceback

def get_transcript(video_id, languages=['en']):
    """
    Fetch transcript for a YouTube video
    
    Args:
        video_id: YouTube video ID
        languages: List of language codes in priority order
        
    Returns:
        Dict with 'transcript' and 'error' keys
    """
    result = {
        'transcript': None,
        'error': None,
        'error_type': None,
        'error_details': None
    }
    
    try:
        # Log attempt
        print(f"[DEBUG] Attempting to fetch transcript for video: {video_id}")
        
        # Use the correct static method
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript(languages).fetch()
        
        print(f"[DEBUG] Successfully fetched {len(transcript)} segments")
        result['transcript'] = transcript
        return result
        
    except Exception as e:
        error_type = type(e).__name__
        error_message = str(e)
        
        # Log detailed error
        print(f"[ERROR] Failed to fetch transcript")
        print(f"[ERROR] Error Type: {error_type}")
        print(f"[ERROR] Error Message: {error_message}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        
        result['error'] = error_message
        result['error_type'] = error_type
        result['error_details'] = traceback.format_exc()
        
        return result
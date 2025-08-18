#!/usr/bin/env python3
"""
Test script for Sanctum app functionality
"""

from app import extract_video_id, clean_text, chunk_text, extract_prayers

def test_video_id_extraction():
    """Test YouTube URL parsing"""
    test_urls = [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("invalid_url", None)
    ]
    
    print("Testing Video ID Extraction:")
    for url, expected in test_urls:
        result = extract_video_id(url)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {url[:30]}... -> {result}")
    print()

def test_text_cleaning():
    """Test text cleaning functionality"""
    test_texts = [
        ("[10:32] Father we um thank you", "Father we thank you"),
        ("Lord   we    praise", "Lord we praise"),
        ("Amen.", "Amen.")
    ]
    
    print("Testing Text Cleaning:")
    for dirty, expected in test_texts:
        result = clean_text(dirty)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{dirty}' -> '{result}'")
    print()

def test_chunking():
    """Test text chunking"""
    long_text = "This is the first sentence. This is the second sentence. This is the third sentence. This is the fourth sentence. This is the fifth sentence."
    
    print("Testing Text Chunking:")
    chunks = chunk_text(long_text, max_chars=50, max_lines=2)
    print(f"  Original: {len(long_text)} chars")
    print(f"  Chunks: {len(chunks)} pieces")
    for i, chunk in enumerate(chunks, 1):
        print(f"    Chunk {i}: {len(chunk)} chars - '{chunk[:30]}...'")
    print()

def test_prayer_extraction():
    """Test prayer extraction"""
    sample_transcript = """
    Welcome everyone to today's service. Let's begin with announcements.
    Now let us pray. Father we thank you for this day. We praise your holy name.
    Lord we ask for your guidance and wisdom. In Jesus name we pray, Amen.
    Now let's turn to scripture for today's reading.
    """
    
    print("Testing Prayer Extraction:")
    prayers = extract_prayers(sample_transcript)
    print(f"  Found {len(prayers)} prayer(s)")
    if prayers:
        for i, prayer in enumerate(prayers, 1):
            print(f"    Prayer {i}: '{prayer[:50]}...'")
    print()

if __name__ == "__main__":
    print("=" * 50)
    print("SANCTUM APP FUNCTIONALITY TEST")
    print("=" * 50)
    print()
    
    test_video_id_extraction()
    test_text_cleaning()
    test_chunking()
    test_prayer_extraction()
    
    print("=" * 50)
    print("All tests completed!")
    print("=" * 50)
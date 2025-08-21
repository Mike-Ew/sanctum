from src.transcript import get_transcript

# Test with a YouTube URL
url = input("Enter YouTube URL: ")

# Extract video ID from URL
if "youtube.com/watch?v=" in url:
    video_id = url.split("watch?v=")[1].split("&")[0]
elif "youtu.be/" in url:
    video_id = url.split("youtu.be/")[1].split("?")[0]
else:
    video_id = url

print(f"Video ID: {video_id}")
print("Fetching transcript...")

transcript = get_transcript(video_id)

if transcript:
    print(f"\nFound {len(transcript)} segments")
    print("\nFirst 5 segments:")
    for i, segment in enumerate(transcript[:5]):
        print(f"{i+1}. {segment['text']}")
else:
    print("Failed to fetch transcript")
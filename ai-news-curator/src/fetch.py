import json
import subprocess
from typing import List, Dict, Optional

from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

def get_full_description_and_chapters(video_id: str) -> (Optional[str], Optional[list]):
    """
    Fetches the full video description and chapters using yt-dlp.
    """
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    command = [
        "yt-dlp",
        "--dump-json",
        "--no-warnings",
        video_url
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        video_info = json.loads(result.stdout)
        return video_info.get("description"), video_info.get("chapters")
    except subprocess.CalledProcessError as e:
        print(f"Error fetching video info with yt-dlp for {video_id}: {e.stderr}")
        return None, None
    except json.JSONDecodeError:
        print(f"Error decoding JSON from yt-dlp for {video_id}")
        return None, None

def get_transcript(video_id: str) -> Optional[List[Dict]]:
    """
    Fetches the transcript for a video.
    Returns a list of dicts with 'text', 'start', and 'duration'.
    Returns None if the transcript is unavailable.
    """
    try:
        # Note: The youtube-transcript-api v1.2.4 has an unexpected API.
        # It requires instantiating the class and calling a 'list' method.
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        transcript = transcript_list.find_transcript(['en'])
        return transcript.fetch()
    except (NoTranscriptFound, TranscriptsDisabled) as e:
        print(f"Could not retrieve transcript for {video_id}: {e}")
        return None

if __name__ == '__main__':
    # Video from the previous step's output
    TEST_VIDEO_ID = "UlbokBsjMRY" 

    print(f"--- Testing fetch.py with video ID: {TEST_VIDEO_ID} ---")

    # Test get_full_description_and_chapters
    print("\n1. Fetching full description and chapters...")
    description, chapters = get_full_description_and_chapters(TEST_VIDEO_ID)
    if description:
        print("   ✅ Success! Fetched description.")
        if chapters:
            print(f"   ✅ Success! Fetched {len(chapters)} chapters.")
        else:
            print("   ℹ️ No chapters found for this video.")
    else:
        print("   ❌ Failed to fetch description and chapters.")

    # Test get_transcript
    print("\n2. Fetching transcript...")
    transcript = get_transcript(TEST_VIDEO_ID)
    if transcript:
        print("   ✅ Success! Fetched transcript.")
    else:
        print("   ❌ Failed to fetch transcript.")

    print("\n--- Test complete ---")
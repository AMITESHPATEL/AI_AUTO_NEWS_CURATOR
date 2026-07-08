import xml.etree.ElementTree as ET
import requests
import json
from typing import List
from src.models import RawVideo

def get_recent_videos(channel_id: str) -> List[RawVideo]:
    """
    Fetches the most recent videos from a YouTube channel's RSS feed.
    """
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    try:
        response = requests.get(feed_url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching RSS feed: {e}")
        return []

    root = ET.fromstring(response.content)
    videos = []
    ns = {
        'atom': 'http://www.w3.org/2005/Atom',
        'yt': 'http://www.youtube.com/xml/schemas/2015',
        'media': 'http://search.yahoo.com/mrss/'
    }

    for entry in root.findall('atom:entry', ns):
        video_id = entry.find('yt:videoId', ns).text
        title = entry.find('atom:title', ns).text
        description = entry.find('media:group/media:description', ns).text
        published_at = entry.find('atom:published', ns).text
        link_tag = entry.find('atom:link[@rel="alternate"]', ns)
        url = link_tag.get('href') if link_tag is not None else f"https://www.youtube.com/watch?v={video_id}"

        videos.append(RawVideo(
            video_id=video_id,
            title=title,
            description=description,
            published_at=published_at,
            url=url
        ))
    return videos

def get_new_videos(videos: List[RawVideo], state_file: str) -> List[RawVideo]:
    """
    Filters a list of videos, returning only those not present in the state file.
    """
    try:
        with open(state_file, 'r') as f:
            processed_video_ids = set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        processed_video_ids = set()

    new_videos = [video for video in videos if video.video_id not in processed_video_ids]
    return new_videos

if __name__ == '__main__':
    # Example usage:
    # Replace with a real Channel ID from your config.yaml for testing
    # Using Google for Developers channel as an example
    TEST_CHANNEL_ID = "UC_x5XG1OV2P6uZZ5FSM9Ttw" 
    STATE_FILE = "../state.json" # Adjust path if running from a different directory

    print(f"Fetching recent videos for channel ID: {TEST_CHANNEL_ID}")
    all_recent_videos = get_recent_videos(TEST_CHANNEL_ID)

    if all_recent_videos:
        print(f"Found {len(all_recent_videos)} recent videos.")
        
        # Create a dummy state file for testing
        dummy_state_file = 'temp_state.json'
        try:
            with open(dummy_state_file, 'w') as f:
                # Pretend we've already processed the first video
                if len(all_recent_videos) > 1:
                    json.dump([all_recent_videos[0].video_id], f)
                else:
                    json.dump([], f)

            print("\nTesting get_new_videos...")
            new_videos = get_new_videos(all_recent_videos, dummy_state_file)
            
            if new_videos:
                print(f"Found {len(new_videos)} new videos:")
                for video in new_videos:
                    print(f"- {video.title} (ID: {video.video_id})")
            else:
                print("No new videos found.")

        finally:
            # Clean up the dummy state file
            import os
            if os.path.exists(dummy_state_file):
                os.remove(dummy_state_file)
    else:
        print("Could not fetch recent videos.")


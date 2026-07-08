import argparse
import json
import logging
import yaml
import os
from typing import List, Dict, Any

# Get the directory where main.py is located
script_dir = os.path.dirname(os.path.abspath(__file__))

from src.rss_monitor import get_recent_videos, get_new_videos
from src.fetch import get_full_description_and_chapters, get_transcript
from src.segment import parse_timestamps, build_segments
from src.enrich import enrich_link
from src.rank import rank_segments
from src.package import write_content_package
from src.models import RawVideo, Segment

def setup_logging(log_file: str):
    """Sets up logging to file and console."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def load_config(path: str) -> Dict[str, Any]:
    """Loads the YAML configuration file."""
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def process_video(video: RawVideo, config: Dict[str, Any]):
    """
    Runs the full processing pipeline for a single video.
    """
    logging.info(f"Processing video: {video.title} ({video.video_id})")

    # 1. Fetch full description and transcript
    logging.info("Fetching full description and transcript...")
    description, chapters = get_full_description_and_chapters(video.video_id)
    if not description:
        logging.error("Failed to fetch description. Skipping video.")
        return False
    
    transcript = get_transcript(video.video_id)
    if not transcript:
        logging.error("Failed to fetch transcript. Skipping video.")
        return False

    # If chapters are present in metadata, use them. Otherwise, parse description.
    if chapters:
        logging.info(f"Found {len(chapters)} chapters in video metadata.")
        timestamps = [(c['start_time'], c['title'], []) for c in chapters]
    else:
        logging.info("No chapters in metadata, parsing description for timestamps.")
        timestamps = parse_timestamps(description)

    if not timestamps:
        logging.error("No timestamps found. Skipping video.")
        return False

    # 2. Build segments
    logging.info(f"Building {len(timestamps)} segments...")
    segments = build_segments(timestamps, transcript)

    # 3. Enrich links
    logging.info("Enriching links found in segments...")
    all_enriched_links = {}
    for segment in segments:
        enriched_for_segment = []
        for link_url in segment.links:
            enriched_for_segment.append(enrich_link(link_url, config.get('github_token')))
        all_enriched_links[segment.title] = enriched_for_segment

    # 4. Rank segments
    logging.info("Ranking segments...")
    ranked_stories = rank_segments(segments, all_enriched_links, config)

    # 5. Write content package
    logging.info("Writing content package...")
    package_path = write_content_package(video, ranked_stories, config['output_dir'])
    logging.info(f"Content package written to {package_path}")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="AI News Auto-Curator")
    parser.add_argument('--dry-run', action='store_true', help="Run without updating state file.")
    parser.add_argument('--video-url', type=str, help="Force process a single video URL, ignoring RSS feed and state.")
    args = parser.parse_args()

    config_path = os.path.join(script_dir, 'config.yaml')
    config = load_config(config_path)

    # Make paths absolute
    config['log_file'] = os.path.join(script_dir, config['log_file'])
    config['state_file'] = os.path.join(script_dir, config['state_file'])
    config['output_dir'] = os.path.join(script_dir, config['output_dir'])
    
    setup_logging(config['log_file'])

    videos_to_process: List[RawVideo] = []

    if args.video_url:
        logging.info(f"Processing single video from URL: {args.video_url}")
        video_id = None
        if "v=" in args.video_url:
            video_id = args.video_url.split('v=')[1].split('&')[0]
        elif "youtu.be/" in args.video_url:
            video_id = args.video_url.split('youtu.be/')[1].split('?')[0]
        
        if not video_id:
            logging.error("Could not parse video ID from URL.")
            return

        # We need to fetch minimal info to create a RawVideo object
        desc, _ = get_full_description_and_chapters(video_id)
        if desc:
             videos_to_process.append(RawVideo(
                video_id=video_id,
                title=f"Video {video_id}", # yt-dlp doesn't give us title easily here
                description=desc,
                published_at= "N/A",
                url=args.video_url
             ))
        else:
            logging.error("Could not fetch video info for URL.")
            return
    else:
        logging.info("Checking RSS feed for new videos...")
        all_videos = get_recent_videos(config['channel_id'])
        videos_to_process = get_new_videos(all_videos, config['state_file'])
        logging.info(f"Found {len(videos_to_process)} new videos to process.")

    if not videos_to_process:
        logging.info("No new videos to process. Exiting.")
        return

    processed_ids = []
    for video in videos_to_process:
        try:
            success = process_video(video, config)
            if success:
                processed_ids.append(video.video_id)
        except Exception as e:
            logging.error(f"An unexpected error occurred while processing {video.video_id}: {e}", exc_info=True)

    if not args.dry_run and processed_ids:
        logging.info(f"Updating state file with {len(processed_ids)} new video IDs...")
        try:
            with open(config['state_file'], 'r+') as f:
                state = json.load(f)
                state.extend(processed_ids)
                f.seek(0)
                json.dump(state, f, indent=4)
        except FileNotFoundError:
            with open(config['state_file'], 'w') as f:
                json.dump(processed_ids, f, indent=4)
    
    logging.info("Pipeline run complete.")

if __name__ == "__main__":
    main()

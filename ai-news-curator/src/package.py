import os
from pathlib import Path
from typing import List
import datetime

from src.models import RawVideo, RankedStory, Segment, EnrichedLink

def write_content_package(video: RawVideo, ranked_stories: List[RankedStory], output_dir: str) -> str:
    """
    Writes a markdown file containing all the curated content for a video.
    """
    # Sanitize video title for use as a directory name
    sanitized_title = "".join(c for c in video.title if c.isalnum() or c in (' ', '_')).rstrip()
    
    if video.published_at != "N/A":
        video_date = datetime.datetime.fromisoformat(video.published_at.replace('Z', '+00:00')).strftime('%Y-%m-%d')
    else:
        video_date = datetime.datetime.now().strftime('%Y-%m-%d') # Fallback for single URL runs
    
    # Create a directory for the video's output
    package_dir = Path(output_dir) / f"{video_date}_{sanitized_title}"
    package_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = package_dir / "content_package.md"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# AI News Digest: {video.title}\n\n")
        f.write(f"**Video URL:** {video.url}\n")
        f.write(f"**Published Date:** {video_date}\n\n")
        f.write("---\n\n")
        
        f.write("## Top Ranked Stories\n\n")
        
        for story in ranked_stories:
            f.write(f"### Rank {story.rank}: {story.segment.title}\n\n")
            f.write(f"**Model's Reasoning:** *{story.reasoning}*\n\n")
            
            # Timestamp link
            timestamp_url = f"https://youtu.be/{video.video_id}?t={story.segment.start_seconds}"
            f.write(f"**Timestamp:** [{story.segment.start_seconds}s]({timestamp_url})\n\n")
            
            f.write("#### Transcript Excerpt:\n")
            f.write(f"> {story.segment.transcript_text}\n\n")
            
            if story.enriched_links:
                f.write("#### Enriched Links:\n")
                for link in story.enriched_links:
                    f.write(f"- **URL:** {link.url}\n")
                    f.write(f"  - **Type:** {link.source_type}\n")
                    if link.title:
                        f.write(f"  - **Title:** {link.title}\n")
                    if link.fetch_error:
                        f.write(f"  - **Fetch Error:** {link.fetch_error}\n")
                    if link.content:
                        f.write(f"  - **Content Preview:**\n")
                        f.write("    ```\n")
                        f.write(f"    {link.content[:500].strip()}...\n")
                        f.write("    ```\n")
                f.write("\n")
            
            f.write("---\n\n")

        f.write("## Draft Post (Paste from LLM here):\n\n")
        f.write("*(Your draft post goes here)*\n")

    return str(filepath)


if __name__ == '__main__':
    # Dummy data for testing
    dummy_video = RawVideo(
        video_id="test_vid_123",
        title="AI Weekly Review",
        description="A test video.",
        published_at="2026-07-08T12:00:00Z",
        url="https://www.youtube.com/watch?v=test_vid_123"
    )
    
    dummy_stories = [
        RankedStory(
            segment=Segment(
                title="New LLM Released",
                start_seconds=65,
                end_seconds=120,
                transcript_text="A major tech company has released a new large language model that is breaking all the benchmarks.",
                links=["https://github.com/test/new-llm"]
            ),
            enriched_links=[
                EnrichedLink(
                    url="https://github.com/test/new-llm",
                    source_type="github",
                    title="test/new-llm",
                    content="This is the README for the new LLM.",
                    fetch_error=None
                )
            ],
            rank=1,
            reasoning="This is the most significant story of the week."
        ),
        RankedStory(
            segment=Segment(
                title="AI in Robotics",
                start_seconds=120,
                end_seconds=180,
                transcript_text="A new paper shows how AI is being used to improve robotic dexterity.",
                links=["https://arxiv.org/abs/2607.12345"]
            ),
            enriched_links=[
                EnrichedLink(
                    url="https://arxiv.org/abs/2607.12345",
                    source_type="arxiv",
                    title="AI for Robotic Dexterity",
                    content="Abstract: We present a new method for training robotic arms...",
                    fetch_error=None
                )
            ],
            rank=2,
            reasoning="This is a breakthrough in the field of robotics."
        )
    ]
    
    output_directory = "../output" # Relative to the src directory

    print("--- Testing package.py ---")
    
    print("Generating content package...")
    package_path = write_content_package(dummy_video, dummy_stories, output_directory)
    
    if Path(package_path).exists():
        print(f"   ✅ Success! Package written to: {package_path}")
        
        print("\n--- File Content ---")
        with open(package_path, 'r', encoding='utf-8') as f:
            print(f.read())
        print("--- End of File Content ---")
    else:
        print("   ❌ Failed to write package file.")
        
    print("\n--- Test complete ---")

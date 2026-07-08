import re
from typing import List, Tuple, Dict, Optional
from src.models import Segment

def parse_timestamps(description: str) -> List[Tuple[int, str, List[str]]]:
    """
    Parses a video description to find timestamps, chapter titles, and associated links.
    Returns a list of tuples: (start_seconds, title, [links]).
    """
    # Regex to find timestamps (HH:MM:SS or MM:SS) and the chapter title
    timestamp_pattern = re.compile(r"\(?(\d{1,2}:\d{2}(?::\d{2})?)\)?\s+(.+)")
    # Regex to find URLs
    url_pattern = re.compile(r"https?://\S+")
    
    lines = description.split('\n')
    timestamps = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        match = timestamp_pattern.match(line)
        if match:
            time_str, title = match.groups()
            
            # Convert time string to seconds
            parts = list(map(int, time_str.split(':')))
            if len(parts) == 3: # HH:MM:SS
                seconds = parts[0] * 3600 + parts[1] * 60 + parts[2]
            else: # MM:SS
                seconds = parts[0] * 60 + parts[1]
            
            # Look for links in the current line and the next 2 lines
            links = url_pattern.findall(line)
            if i + 1 < len(lines):
                links.extend(url_pattern.findall(lines[i+1]))
            if i + 2 < len(lines):
                links.extend(url_pattern.findall(lines[i+2]))

            timestamps.append((seconds, title.strip(), list(set(links))))

    return timestamps

from typing import List, Tuple, Dict, Any

# ... (rest of the file is the same until build_segments)

def build_segments(timestamps: List[Tuple[int, str, List[str]]], transcript: Any) -> List[Segment]:
    """
    Builds video segments from timestamps and a full transcript object.
    """
    segments = []
    if not timestamps or not transcript:
        return segments

    # The transcript object has a 'snippets' attribute which is iterable
    snippets = transcript.snippets if hasattr(transcript, 'snippets') else transcript

    for i, (start_s, title, links) in enumerate(timestamps):
        end_s = timestamps[i + 1][0] if i + 1 < len(timestamps) else None
        
        segment_text = ""
        for part in snippets:
            # The 'part' is an object with attributes, not a dictionary
            part_start = part.start
            # Check if the transcript part belongs to this segment
            if start_s <= part_start and (end_s is None or part_start < end_s):
                segment_text += part.text + " "
        
        segments.append(Segment(
            title=title,
            start_seconds=start_s,
            end_seconds=end_s,
            transcript_text=segment_text.strip(),
            links=links
        ))
        
    return segments

if __name__ == '__main__':
    # Example from a real video description
    test_description = """
    Here are the top stories from this week's developer news!
    
    (0:00) Intro
    (0:15) Gemini 3.5 Live Translate
    https://google.com/gemini
    (1:30) Gemini in Xcode
    Check it out here: https://github.com/google/gemini-ios
    (3:45) And something else entirely
    
    Thanks for watching!
    """
    
    # Abridged example transcript
    test_transcript = [
        {'text': 'Hello and welcome', 'start': 0.5, 'duration': 2.0},
        {'text': 'to the show.', 'start': 2.5, 'duration': 1.5},
        {'text': 'First up, we have Gemini 3.5', 'start': 15.2, 'duration': 4.0},
        {'text': 'with its new Live Translate feature.', 'start': 19.5, 'duration': 3.0},
        {'text': 'It is amazing.', 'start': 23.0, 'duration': 2.0},
        {'text': 'Next, for all you iOS developers,', 'start': 90.1, 'duration': 3.5},
        {'text': 'Gemini is now in Xcode.', 'start': 94.0, 'duration': 2.8},
        {'text': 'And for our final story,', 'start': 225.0, 'duration': 2.5},
        {'text': 'something completely different.', 'start': 228.0, 'duration': 3.0},
    ]

    print("--- Testing segment.py ---")
    
    print("\n1. Parsing timestamps...")
    parsed_timestamps = parse_timestamps(test_description)
    if parsed_timestamps:
        print(f"   ✅ Success! Found {len(parsed_timestamps)} timestamps.")
        for ts in parsed_timestamps:
            print(f"      - Time: {ts[0]}s, Title: '{ts[1]}', Links: {ts[2]}")
    else:
        print("   ❌ Failed to parse timestamps.")

    print("\n2. Building segments...")
    segments = build_segments(parsed_timestamps, test_transcript)
    if segments:
        print(f"   ✅ Success! Built {len(segments)} segments.")
        for i, seg in enumerate(segments):
            print(f"\n   --- Segment {i+1} ---")
            print(f"   Title: {seg.title}")
            print(f"   Time: {seg.start_seconds}s - {seg.end_seconds}s")
            print(f"   Links: {seg.links}")
            print(f"   Transcript (first 50 chars): '{seg.transcript_text[:50]}...'")
    else:
        print("   ❌ Failed to build segments.")
        
    print("\n--- Test complete ---")

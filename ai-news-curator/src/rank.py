import json
import os
from dotenv import load_dotenv
import requests
from typing import List, Dict, Any

from src.models import Segment, EnrichedLink, RankedStory

load_dotenv() 

def call_ollama(prompt: str, config: Dict[str, Any]) -> str:
    """Calls the Ollama API to get a ranking."""
    ollama_config = config['ollama']
    try:
        response = requests.post(
            f"{ollama_config['host']}/api/generate",
            json={
                "model": ollama_config['model'],
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": ollama_config['temperature']
                }
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json()['response']
    except requests.RequestException as e:
        print(f"Error calling Ollama: {e}")
        return None

def call_gemini(prompt: str, config: Dict[str, Any]) -> str:
    """Calls the Gemini API to get a ranking."""
    gemini_config = config['gemini']
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("GEMINI_API_KEY environment variable not set.")
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_config['model']}:generateContent"
    headers = {'x-goog-api-key': api_key}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": gemini_config['temperature']}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code == 429:
            print("Gemini API rate limit hit. Falling back to Ollama for this run.")
            return call_ollama(prompt, config) # Fallback to Ollama
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except requests.RequestException as e:
        print(f"Error calling Gemini API: {e}")
        return None

def parse_ranking_response(raw_text: str, segments: List[Segment], enriched_links: Dict[str, List[EnrichedLink]]) -> List[RankedStory]:
    """Parses the JSON response from the LLM and creates RankedStory objects."""
    try:
        # The response might be in a markdown code block
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0]
        
        data = json.loads(raw_text)
        ranked_items = data['ranked']
        
        ranked_stories = []
        for item in ranked_items:
            segment_index = item['index'] - 1 # Adjust for 0-based index
            if 0 <= segment_index < len(segments):
                segment = segments[segment_index]
                story = RankedStory(
                    segment=segment,
                    enriched_links=enriched_links.get(segment.title, []),
                    rank=item['rank'],
                    reasoning=item['reasoning']
                )
                ranked_stories.append(story)
        
        return sorted(ranked_stories, key=lambda s: s.rank)

    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"Failed to parse LLM ranking response: {e}\nRaw response:\n{raw_text}")
        return None

def rank_segments(segments: List[Segment], enriched_links: Dict[str, List[EnrichedLink]], config: Dict[str, Any]) -> List[RankedStory]:
    """
    Ranks segments using an LLM backend and returns a list of RankedStory objects.
    """
    top_n = config['ranking']['top_n']
    
    # Create a simplified representation of segments for the prompt
    prompt_segments = []
    for i, segment in enumerate(segments):
        link_urls = [link.url for link in enriched_links.get(segment.title, [])]
        prompt_segments.append(
            f"{i+1}. {segment.title}\n"
            f"   - Transcript: {segment.transcript_text[:300]}...\n"
            f"   - Links: {link_urls}"
        )
    
    prompt = (
        f"You are ranking AI news stories from a YouTube video for a social media digest. "
        f"Given the list of stories below, pick the top {top_n} by significance and recency. "
        f"Respond with ONLY valid JSON in this exact shape: "
        f'{{"ranked": [{{"index": <int>, "rank": <int>, "reasoning": "<one sentence>"}}, ...]}}\n\n'
        f"Stories:\n" + "\n".join(prompt_segments)
    )

    backend = config['llm']['backend']
    print(f"Ranking segments using '{backend}' backend...")
    
    raw_response = None
    if backend == 'gemini':
        raw_response = call_gemini(prompt, config)
    elif backend == 'ollama':
        raw_response = call_ollama(prompt, config)
    else:
        print(f"Unknown LLM backend: {backend}")
        return None

    if not raw_response:
        print("LLM call failed. Falling back to taking the first N segments.")
        # Fallback logic
        ranked_stories = []
        for i, segment in enumerate(segments[:top_n]):
            ranked_stories.append(RankedStory(
                segment=segment,
                enriched_links=enriched_links.get(segment.title, []),
                rank=i + 1,
                reasoning="Fell back to chronological order due to LLM failure."
            ))
        return ranked_stories

    ranked_stories = parse_ranking_response(raw_response, segments, enriched_links)
    
    if not ranked_stories:
        print("Parsing LLM response failed. Falling back to first N segments.")
        # Fallback logic
        ranked_stories = []
        for i, segment in enumerate(segments[:top_n]):
            ranked_stories.append(RankedStory(
                segment=segment,
                enriched_links=enriched_links.get(segment.title, []),
                rank=i + 1,
                reasoning="Fell back to chronological order due to parsing failure."
            ))
        return ranked_stories
        
    return ranked_stories


if __name__ == '__main__':
    # Dummy data for testing
    dummy_segments = [
        Segment(title="Story A", start_seconds=10, end_seconds=20, transcript_text="This is about A.", links=[]),
        Segment(title="Story B", start_seconds=20, end_seconds=30, transcript_text="This is about B, which is very important.", links=[]),
        Segment(title="Story C", start_seconds=30, end_seconds=40, transcript_text="This is about C.", links=[]),
    ]
    dummy_enriched_links = {
        "Story A": [EnrichedLink(url="http://a.com", source_type="article", title="A", content="A content", fetch_error=None)],
        "Story B": [EnrichedLink(url="http://b.com", source_type="article", title="B", content="B content", fetch_error=None)],
    }
    dummy_config = {
        "llm": {"backend": "ollama"},
        "ollama": {"host": "http://localhost:11434", "model": "qwen2:1.5b", "temperature": 0.1},
        "gemini": {"model": "gemini-2.5-flash", "temperature": 0.2},
        "ranking": {"top_n": 2}
    }

    print("--- Testing rank.py ---")
    
    # Check if Ollama is running before testing
    try:
        requests.get(dummy_config['ollama']['host'], timeout=2)
        ollama_running = True
    except requests.RequestException:
        ollama_running = False

    if ollama_running:
        print("Ollama server is reachable. Running test...")
        ranked = rank_segments(dummy_segments, dummy_enriched_links, dummy_config)
        if ranked:
            print("\n--- Ranking Complete ---")
            for story in ranked:
                print(f"Rank {story.rank}: {story.segment.title} - {story.reasoning}")
            print("---")
        else:
            print("Ranking failed.")
    else:
        print("Ollama server not found at http://localhost:11434. Skipping rank.py test.")
        print("Please start the Ollama server to test this module.")

    print("\n--- Test complete ---")

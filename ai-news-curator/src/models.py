from dataclasses import dataclass, field
from typing import Optional

@dataclass
class RawVideo:
    video_id: str
    title: str
    description: str
    published_at: str
    url: str

@dataclass
class Segment:
    title: str                # from the description's timestamp line
    start_seconds: int
    end_seconds: int | None
    transcript_text: str
    links: list[str] = field(default_factory=list) # raw URLs found in this segment's description line(s)

@dataclass
class EnrichedLink:
    url: str
    source_type: str           # "github" | "arxiv" | "article" | "unknown"
    title: str | None
    content: str                # README text / abstract / extracted article text
    fetch_error: str | None

@dataclass
class RankedStory:
    segment: Segment
    enriched_links: list[EnrichedLink]
    rank: int                   # 1-5
    reasoning: str               # why the model ranked it here

# AI News Auto-Curator — MVP Plan

## 1. What this is

A local Python pipeline that watches one YouTube channel (an AI-news channel), and for every
new video:

1. Pulls the transcript + description
2. Splits the video into individual news items using the timestamps the creator already put
   in the description
3. Follows every link in the description (GitHub, arXiv, blog posts, etc.) and pulls in the
   real content behind it
4. Ranks the top 5 most significant/recent stories from that video using an LLM — either a
   local Ollama model (Qwen) or the Gemini API, switchable via config (see section 5)
5. Writes one clean markdown "content package" per story — everything needed to write a
   social post: summary, source links, transcript excerpt, README/abstract text, etc.

That markdown file is the final output of this MVP. The person then pastes it into a
closed-source LLM chat (Claude, ChatGPT, whatever) to actually write the LinkedIn/Twitter
post copy, and copies the result into LinkedIn/Twitter by hand.

## 2. Explicit non-goals for this MVP

Do NOT build these yet — they're future work, listed in section 9:

- No automatic post-writing (that step stays manual, via a closed-source LLM chat)
- No LinkedIn API or X/Twitter API integration — publishing is 100% copy-paste by hand
- No multi-channel support — hardcode one channel via config, design so it's easy to extend
  later, but don't build the abstraction now
- No web UI / dashboard — this is a CLI script
- No database — flat JSON files for state are enough at this volume

## 3. Environment

- Python 3.11+
- Ollama installed locally, already pulled model(s). Recommend testing both and picking one
  via config:
  - `qwen2.5:7b-instruct-q4_K_M` — better reasoning, may spill some layers to CPU on a 4GB
    GPU (RTX 3050 Ti), will be slower
  - `qwen2.5:3b-instruct` — fully fits in VRAM, faster, somewhat weaker judgment
  - Fallback if both are too slow in practice: `qwen2.5:1.5b-instruct`
- Ollama runs as a local server at `http://localhost:11434` — the script talks to it over
  HTTP, no API key needed

**Ranking backend is pluggable** — build it so `config.yaml` picks between:

- `ollama` — fully local, free, no rate limits, quality/speed depends on the model above
- `gemini` — Google's Gemini API. Free via a Google AI Studio key (no credit card): as of
  mid-2026 the Flash and Flash-Lite models are free-tier eligible with limits in the
  ballpark of 10-15 requests/minute and hundreds to ~1,500 requests/day — more than enough
  for a handful of ranking calls per video. Recommended free-tier models: `gemini-2.5-flash`
  or `gemini-2.5-flash-lite`. Two things worth knowing before relying on it:
  - Google's free-tier rate limits have changed several times through 2026 — check the
    live limits shown in Google AI Studio for your project rather than trusting a fixed
    number
  - On the free tier, Google may use your prompts/outputs to improve their models — fine
    for public AI news content, but worth being aware of since it differs from Ollama
    (which sends nothing anywhere)

Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com) — no card
required — and put it in `config.yaml` (or better, load it from an environment variable,
see below).

### Python packages

```
yt-dlp
youtube-transcript-api
requests
trafilatura        # clean text extraction from generic web pages
pyyaml              # config file
python-dateutil
```

No extra SDK is needed for Gemini — plain `requests` against the REST endpoint is enough
(see 7.5), so it doesn't add a new dependency.

No paid API keys are required for the MVP. A GitHub personal access token is optional but
recommended (raises the unauthenticated 60 req/hour GitHub API limit). If using the Gemini
backend, keep the API key out of `config.yaml` in version control — load it from an
environment variable (e.g. `GEMINI_API_KEY`) instead.

## 4. Directory structure

```
ai-news-curator/
├── config.yaml
├── state.json                  # tracks which video IDs have already been processed
├── requirements.txt
├── main.py                     # entry point, orchestrates the pipeline
├── src/
│   ├── rss_monitor.py          # step 1: detect new videos
│   ├── fetch.py                # step 2: pull transcript + description via yt-dlp
│   ├── segment.py              # step 3: split transcript into per-story chunks
│   ├── enrich.py                # step 4: follow links, pull GitHub/arXiv/article content
│   ├── rank.py                  # step 5: call Ollama, pick top 5
│   ├── package.py               # step 6: write the markdown content package
│   └── models.py                # shared dataclasses
├── output/
│   └── 2026-07-08_video-title/
│       └── content_package.md
└── logs/
    └── run.log
```

## 5. Config file (`config.yaml`)

```yaml
channel_id: "UCxxxxxxxxxxxxxxxxxxxxxxxx"   # the AI news channel's UC... ID
poll_interval_minutes: 60

llm:
  backend: "ollama"    # "ollama" | "gemini" — which one ranks the stories

ollama:
  host: "http://localhost:11434"
  model: "qwen2.5:7b-instruct-q4_K_M"
  temperature: 0.2

gemini:
  model: "gemini-2.5-flash"
  temperature: 0.2
  # api_key: read from GEMINI_API_KEY env var, not stored here

ranking:
  top_n: 5

output_dir: "output"
state_file: "state.json"
log_file: "logs/run.log"

github_token: ""    # optional, raises GitHub API rate limit if set
```

## 6. Data model (`src/models.py`)

Use `dataclasses` (or pydantic if Claude Code prefers — either is fine, pydantic gives free
validation).

```python
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
    links: list[str]          # raw URLs found in this segment's description line(s)

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
```

## 7. Module-by-module plan

### 7.1 `rss_monitor.py`

- `get_recent_videos(channel_id: str) -> list[RawVideo]`
  - GET `https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}`
  - Parse the Atom XML (stdlib `xml.etree.ElementTree` is enough, no need for feedparser)
  - Return video id, title, description snippet, published date, url for each `<entry>`
- `get_new_videos(videos: list[RawVideo], state_file: str) -> list[RawVideo]`
  - Load `state.json` (a list of already-processed video IDs)
  - Return only videos not in that list
  - Caller is responsible for updating state.json after a video is fully processed —
    don't mark it processed until the whole pipeline succeeds for that video, so a crash
    mid-run retries cleanly

### 7.2 `fetch.py`

- `get_full_description(video_id: str) -> str`
  - RSS descriptions are sometimes truncated — use `yt-dlp` to get the full description and
    chapter list: `yt-dlp --dump-json <video_url>`, read `description` and `chapters` fields
- `get_transcript(video_id: str) -> list[dict]`
  - Use `youtube_transcript_api.YouTubeTranscriptApi.get_transcript(video_id)`
  - Returns list of `{text, start, duration}` — keep this raw, `segment.py` will bucket it
  - Handle `TranscriptsDisabled` / `NoTranscriptFound` gracefully — log and skip the video
    rather than crashing the whole run

### 7.3 `segment.py`

- `parse_timestamps(description: str) -> list[tuple[int, str]]`
  - Regex for lines like `00:00 Intro`, `03:12 GPT-6 launches`, `1:04:33 New robotics paper`
  - Convert `mm:ss` / `h:mm:ss` to total seconds
  - Also grab any URL(s) that appear on the same line or in the following 1-2 lines (creators
    usually put the link right under the timestamp entry)
- `build_segments(timestamps, transcript) -> list[Segment]`
  - For each timestamp, its segment's transcript is every transcript chunk whose `start`
    falls between this timestamp and the next one
  - Concatenate that transcript text into `Segment.transcript_text`

### 7.4 `enrich.py`

- `extract_links(text: str) -> list[str]` — regex, dedupe
- `classify_link(url: str) -> str` — `"github"` if `github.com` in netloc and has `/owner/repo`
  path, `"arxiv"` if `arxiv.org`, else `"article"`
- `enrich_github(url: str, token: str | None) -> EnrichedLink`
  - Parse owner/repo from URL, call `GET https://api.github.com/repos/{owner}/{repo}/readme`
    with `Accept: application/vnd.github.raw+json`, use token in `Authorization` header if
    provided
- `enrich_arxiv(url: str) -> EnrichedLink`
  - Extract the arXiv ID, call `http://export.arxiv.org/api/query?id_list={id}`, parse the
    Atom response for title + abstract
- `enrich_article(url: str) -> EnrichedLink`
  - `trafilatura.fetch_url` + `trafilatura.extract`, truncate to ~1500 chars
- `enrich_link(url: str, github_token: str | None) -> EnrichedLink` — dispatches to the above
  based on `classify_link`, catches exceptions and returns an `EnrichedLink` with
  `fetch_error` set rather than raising

### 7.5 `rank.py`

- `rank_segments(segments: list[Segment], config) -> list[RankedStory]`
  - Builds the single shared prompt below, then dispatches to whichever backend
    `config.llm.backend` names. Both backends must return the same parsed structure so the
    rest of the pipeline doesn't care which one ran.

Shared prompt (same text regardless of backend — one segment list, title + first ~300 words
of transcript + which links it has):

```
You are ranking AI news stories extracted from a single YouTube video for a social media
digest. Given the list of stories below, pick the top {top_n} by a combination of
significance (major model/product releases, big benchmark results, notable funding/research)
and recency. Respond with ONLY valid JSON, no other text, in this exact shape:

{"ranked": [{"index": <int>, "reasoning": "<one sentence>"}, ...]}

Stories:
1. [title] - [transcript excerpt] - links: [...]
2. ...
```

- `call_ollama(prompt: str, config) -> str`
  - POST to `{ollama.host}/api/generate` with `model`, `prompt`, `stream: false`,
    `temperature`; return the raw text response
- `call_gemini(prompt: str, config) -> str`
  - POST to
    `https://generativelanguage.googleapis.com/v1beta/models/{gemini.model}:generateContent`
    with header `x-goog-api-key: {GEMINI_API_KEY env var}` and body
    `{"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": ...}}`
  - Extract the text from `response["candidates"][0]["content"]["parts"][0]["text"]`
  - If Gemini returns a 429 (rate limit), log it clearly and fall back to `call_ollama` for
    this run rather than failing — free-tier limits shift over time, don't let a quota bump
    break the pipeline
- `parse_ranking_response(raw_text: str, segments: list[Segment]) -> list[RankedStory]`
  - Shared by both backends: strip markdown code fences if present, `json.loads`, map each
    `index` back to its `Segment`
  - If parsing fails, retry once with a stricter reminder appended to the prompt (same
    backend); if it fails again, fall back to taking the first `top_n` segments in video
    order and log a warning — never crash the run over a bad ranking response

### 7.6 `package.py`

- `write_content_package(video: RawVideo, ranked: list[RankedStory], output_dir: str) -> str`
- One markdown file per video, one section per ranked story, containing:
  - Story title, rank, one-line reasoning from the model
  - Video timestamp link: `https://youtu.be/{video_id}?t={start_seconds}`
  - Full transcript excerpt for that segment
  - For each enriched link: the URL, its type, and the pulled content (README/abstract/article
    text)
  - A blank "Draft post (paste from LLM here):" placeholder heading, so the workflow is:
    open this file → paste the whole thing into Claude/ChatGPT → paste the result back
    under that heading → copy to LinkedIn/Twitter by hand

### 7.7 `main.py`

Orchestrates: load config → get new videos → for each new video, run fetch → segment →
enrich → rank → package, in that order, wrapped in a try/except per video so one bad video
doesn't stop the others → update `state.json` only after a video's package is fully written →
log everything to `logs/run.log`.

Add a `--dry-run` flag that runs the whole pipeline but skips writing to `state.json`, so it
can be re-run repeatedly against the same video while testing.

Add a `--video-url` flag to force-process a specific video regardless of the RSS feed /
state file, for testing against a known video.

## 8. Build order (do these in order, test after each one)

- [ ] 1. Scaffold the repo structure, `requirements.txt`, `config.yaml`, empty modules
- [ ] 2. `rss_monitor.py` — fetch and parse the RSS feed, print new video titles to confirm
      it works against the real channel
- [ ] 3. `fetch.py` — pull description + transcript for one hardcoded video ID, print both
- [ ] 4. `segment.py` — parse timestamps from that video's real description, confirm segment
      boundaries look right by printing them
- [ ] 5. `enrich.py` — confirm it correctly classifies and enriches at least one GitHub link,
      one arXiv link, and one generic article link
- [ ] 6. `rank.py` — confirm Ollama is reachable (`curl http://localhost:11434/api/tags`),
      test the ranking prompt against real segments with `backend: ollama`, then switch
      `config.yaml` to `backend: gemini` (with `GEMINI_API_KEY` set) and confirm it produces
      the same shape of output — sanity-check both against the same video and compare quality
- [ ] 7. `package.py` — generate one full content package markdown file and manually review
      it for readability
- [ ] 8. `main.py` — wire it all together, run end-to-end against one real new video
- [ ] 9. Add error handling for the known failure points: transcripts disabled, private/
      deleted videos, malformed timestamps, Ollama timeout, unreachable links
- [ ] 10. Set up the cron job / scheduled task to run `main.py` on `poll_interval_minutes`

## 9. Future enhancements (explicitly out of scope for now)

- Auto-draft the post copy via a closed-source LLM API call instead of manual paste, once
  the ranking quality is trusted
- Auto-publish: LinkedIn's `w_member_social` scope (self-serve "Share on LinkedIn" product)
  can post to a personal profile without the heavy Marketing Developer Platform approval —
  worth adding once drafts are consistently good. X/Twitter no longer has a free posting
  tier as of Feb 2026 (pay-per-use, ~$0.20/post if it contains a link) — factor that in if
  auto-posting to X is ever added
- Multiple source channels
- A lightweight review UI (even just a Google Sheet synced via API) instead of opening
  markdown files by hand
- Add Groq (free tier, very fast Llama models) as a third ranking backend option alongside
  Ollama and Gemini, for days the local machine is off
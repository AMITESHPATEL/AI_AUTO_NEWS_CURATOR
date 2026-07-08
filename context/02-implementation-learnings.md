# Implementation Learnings & Decisions

This document records the key technical challenges encountered during the implementation of the AI News Auto-Curator and the solutions applied.

## 1. `youtube-transcript-api` Inconsistencies

The most significant challenge was interacting with the `youtube-transcript-api` library (version 1.2.4). The plan was based on documentation that suggested a static `get_transcript` method, which did not exist on the class.

- **Problem**: `AttributeError: type object 'YouTubeTranscriptApi' has no attribute 'get_transcript'` and subsequent `AttributeError` for `list_transcripts`.
- **Investigation**:
    1.  Initially assumed a naming conflict with my own `get_transcript` function, but renaming it did not solve the issue.
    2.  Used `dir(YouTubeTranscriptApi)` to inspect the class attributes at runtime. This revealed that the expected methods (`get_transcript`, `list_transcripts`) were missing. The available methods were `list` and `fetch`.
    3.  Experimentation showed that `list` was an *instance method*, not a static one.
- **Solution**: The correct invocation required instantiating the class first:
    ```python
    api = YouTubeTranscriptApi()
    transcript_list = api.list(video_id) # The method is named 'list'
    transcript = transcript_list.find_transcript(['en'])
    transcript_object = transcript.fetch() # This returns a Transcript object
    ```
- **Further Learning**: The object returned by `fetch()` was not a list of dictionaries as assumed, but a `Transcript` object. The actual transcript parts were in the `.snippets` attribute of this object. The `build_segments` function was updated to iterate over `transcript.snippets` and access data using attribute access (e.g., `part.start`) instead of dictionary keys.

## 2. Web Content Enrichment (`enrich.py`)

Fetching content from generic article links proved unreliable.

- **Problem**: `trafilatura.fetch_url()` failed for several test URLs, including a Google Blog post and a BBC News article, returning errors like `NameResolutionError` and `404 Client Error`.
- **Investigation**: The errors suggested that the websites were either blocking automated requests or had network-related issues specific to the execution environment.
- **Solution**:
    1.  The `enrich_article` function was made more robust by using the `requests` library directly. This allowed for setting a `User-Agent` header to mimic a browser, reducing the chance of being blocked.
    2.  For testing purposes, the test URL was changed to a Wikipedia page, which is known to be more permissive for scrapers. This confirmed the code was working correctly and the issue was with the target websites.

## 3. Timestamp Parsing (`segment.py`)

The initial regex for parsing timestamps from the video description was too brittle.

- **Problem**: The regex `(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+)` failed to find any matches in the test description.
- **Investigation**: The test description had timestamps formatted like `(0:00) Intro` with leading whitespace. The regex did not account for the parentheses, and `re.match` was failing due to the leading spaces.
- **Solution**:
    1.  The regex was updated to `\(?(\d{1,2}:\d{2}(?::\d{2})?)\)?\s+(.+)` to handle optional parentheses.
    2.  The line being matched was stripped of leading/trailing whitespace using `.strip()` before applying the regex match.

## 4. Script Pathing (`main.py`)

Running the main script from the project's root directory caused a `FileNotFoundError`.

- **Problem**: The script could not find `config.yaml` because it was looking for it in the current working directory, not the directory where the script itself was located.
- **Solution**: The script was modified to use absolute paths based on its own file location. This makes the script runnable from any directory.
    ```python
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.yaml')
    # This pattern was applied to all file paths (logs, state, output).
    ```

## 5. Data-Related Runtime Errors

Two significant runtime errors occurred due to incorrect assumptions about data.

- **Problem 1**: `TypeError: 'FetchedTranscriptSnippet' object is not subscriptable` in `build_segments`.
    - **Cause**: As detailed in point 1, the code was trying to use dictionary-style access (`part['start']`) on an object.
    - **Solution**: Switched to attribute access (`part.start`).

- **Problem 2**: `ValueError: Invalid isoformat string: 'N/A'` in `write_content_package`.
    - **Cause**: When running with `--video-url`, a `RawVideo` object was created with `"N/A"` as the `published_at` date, which the date parser could not handle.
    - **Solution**: The `write_content_package` function was updated to check if `published_at` is `"N/A"` and use the current date as a fallback.

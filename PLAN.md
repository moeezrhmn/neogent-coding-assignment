# Call Transcript Extractor — Plan

## Requirement

Build a small program that extracts the following from a call transcript:

1. The caller's name
2. Their intent
3. Whether a follow-up is needed, with the date/time if applicable

## Stack

- Python 3.12 with uv
- Gemini free tier: `gemini-3.5-flash`, falling back to `gemini-3.5-flash-lite` if it's overloaded
- Pydantic for the response schema and validation

## Approach

```
transcript.txt ──► script ──► Gemini (JSON schema) ──► Pydantic validation ──► JSON output
```

## Steps

| # | Step | Status |
|---|---|---|
| 1 | Set up the project with uv and add the Gemini key | ✅ Done |
| 2 | Extract caller name: [extract.py](extract.py) | ✅ Done |
| 3 | Extract intent | ✅ Done |
| 4 | Extract follow-up (needed + day/time) | ✅ Done |

## Output for the sample

```json
{
  "caller_name": "Linda",
  "intent": "The agent called to schedule a $4,200 roof repair following a storm damage inspection, but Linda stated they are waiting for a second opinion first.",
  "follow_up": {
    "needed": true,
    "date_time": "Friday at 2pm"
  }
}
```

## Notes

- **Caller ≠ intended contact:** the agent asked for Mark, but Linda answered.
- **No dates in the transcript:** it only says "Friday at 2pm", with no calendar date, so the output keeps the phrase as said. See [README.md](README.md#dates-are-not-in-the-transcript).
- The full list of edge cases is in [README.md](README.md#edge-cases).

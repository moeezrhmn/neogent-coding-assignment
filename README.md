# Call Transcript Extractor

A small Python script that reads a voice-agent call transcript and extracts the caller's name, their intent, and whether a follow-up is needed (with date/time). It uses Gemini with a forced JSON schema validated by Pydantic.

## Setup

Requires [uv](https://docs.astral.sh/uv/) and a free Gemini API key from [Google AI Studio](https://aistudio.google.com).

```bash
uv sync
echo 'GEMINI_API_KEY=your-key-here' > .env
```

## Usage

```bash
uv run --env-file .env extract.py transcripts/sample.txt
```

## Output

For [transcripts/sample.txt](transcripts/sample.txt):

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

| Field | Meaning |
|---|---|
| `caller_name` | Person who actually spoke on the customer side |
| `intent` | What the call is about and the caller's position |
| `follow_up.needed` | Whether a follow-up was agreed |
| `follow_up.date_time` | Agreed follow-up day/time as said in the call, or `null` |

## How it works

1. The transcript is sent to Gemini with a system prompt containing the extraction rules.
2. The `CallSummary` Pydantic model is passed as the response schema, so the model must return JSON in that exact shape.
3. Pydantic validates the response, so a malformed answer fails loudly instead of printing bad data.
4. If `gemini-3.5-flash` is overloaded (5xx), the script falls back to `gemini-3.5-flash-lite`.

## Edge cases

### Handled

- **Someone else answers:** the agent asks for Mark but Linda answers. Linda is returned as the caller, not Mark.
- **No guessed surnames:** Linda's last name is never said, so the output is "Linda", not "Linda Henderson".
- **Two days mentioned:** Thursday is the competitor's visit and Friday is the follow-up. Only Friday is returned.
- **Vague time made specific:** "Friday afternoon" became "Friday at 2pm", and the confirmed time is used.
- **No invented dates:** the follow-up is returned as said, not as a guessed calendar date.
- **Missing values:** no caller name or no follow-up is returned as `null`.

### Not handled yet

- **The caller never says their name:** only the agent says it ("Thanks Linda").
- **A handoff partway through:** "Hold on, let me get Mark." Now there are two people on the customer side.
- **Voicemail or a wrong number:** there's no real caller.
- **The caller corrects their name:** "It's Jon, not John."
- **Nicknames vs. full names:** "Bob" vs. "Robert" might be treated as two people.
- **Speech-to-text mistakes:** misspelled names, or "Mark's" turned into a different name.
- **Names that are also ordinary words:** Will, Hope, Grace.
- **Inbound calls:** the "Agent"/"Caller" labels might mean something different.
- **Prompt injection:** the transcript says "ignore your instructions…"

## Dates are not in the transcript

The transcript mentions **days and a time, but no calendar dates**:

| Phrase | Refers to | Date given? |
|---|---|---|
| "last Tuesday" | Roof inspection | Day only |
| "on Thursday" | Second opinion from another contractor | Day only |
| "Friday afternoon" → "Friday at 2pm" | Follow-up call | Day and time only |

The call date, year and timezone are all missing. Without knowing when the call happened, "Friday at 2pm" can't be turned into a real date. The planned fix:

- Accept a `--call-date` argument (e.g. `--call-date 2026-10-28`) and resolve relative days against it. Friday after a Wednesday Oct 28 call is **2026-10-30 14:00**.
- Without `--call-date`, return the phrase as said ("Friday at 2pm") with the date set to `null`, rather than guessing.
- The timezone is unknown, so treat the time as the customer's local time.

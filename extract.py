"""Extract the caller's name, intent and follow-up from a voice-agent call transcript.

Usage:
    uv run --env-file .env extract.py transcripts/sample.txt
"""

import sys
from pathlib import Path

from google import genai
from google.genai import errors
from pydantic import BaseModel, Field

MODELS = ["gemini-3.5-flash", "gemini-3.5-flash-lite"]  # primary, then fallback

SYSTEM_PROMPT = """You extract structured information from call transcripts.
Rules:
- caller_name: the person who actually spoke on the customer side of the call.
  This may differ from who the agent asked for (e.g. a spouse answers).
  Use only names said in the transcript. Never infer surnames. Null if unknown.
- intent: one sentence covering what the call is about and the caller's
  response or position.
- follow_up.needed: true only if a follow-up was agreed in the call.
- follow_up.date_time: the final agreed day/time exactly as said (prefer the
  agent's confirmed time over a vaguer one). The transcript has no calendar
  dates, so never invent one. Null if no follow-up.
- Don't confuse follow-up timing with other dates mentioned in the call."""


class FollowUp(BaseModel):
    needed: bool = Field(description="Whether a follow-up was agreed")
    date_time: str | None = Field(description="Agreed follow-up day/time as said")


class CallSummary(BaseModel):
    caller_name: str | None = Field(description="Person who actually spoke on the call")
    intent: str = Field(description="What the call is about and the caller's position")
    follow_up: FollowUp


def extract(transcript: str) -> CallSummary:
    client = genai.Client()  # reads GEMINI_API_KEY from the environment
    for model in MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=transcript,
                config={
                    "system_instruction": SYSTEM_PROMPT,
                    "response_mime_type": "application/json",
                    "response_schema": CallSummary,
                    "temperature": 0,
                },
            )
            return CallSummary.model_validate_json(response.text)
        except errors.ServerError as e:  # 503 overloaded etc. -> try next model
            print(f"[{model}] unavailable ({e.code}), trying fallback...", file=sys.stderr)
    raise RuntimeError("All models are unavailable, try again shortly.")


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Usage: extract.py <transcript_file>")
    transcript = Path(sys.argv[1]).read_text()
    print(extract(transcript).model_dump_json(indent=2))


if __name__ == "__main__":
    main()

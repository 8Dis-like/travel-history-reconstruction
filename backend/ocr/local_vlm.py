from pydantic import BaseModel
import httpx
import json
import base64


_SCHEMA = {
    "type": "object",
    "properties": {
        "date": {"type": ["string", "null"], "description": "ISO 8601 YYYY-MM-DD, or null if illegible/absent"},
        "country": {"type": ["string", "null"], "description": "ISO-3166 alpha-3 country code (e.g. GBR, USA, FRA, COL, HKG), or null if illegible/absent"},
        "direction": {"type": ["string", "null"], "enum": ["ENTRY", "EXIT", None], "description": "ENTRY, EXIT, or null if illegible/absent"},
        "confidence": {"type": ["number", "null"], "minimum": 0, "maximum": 1}
    },
    "required": ["date", "country", "direction", "confidence"],
    "additionalProperties": False
}

_SYSTEM_PROMPT_current = """
Is there a legible passport stamp? If no, return all null fields as specified. If yes, are all fields legible? 
If a field is not legible, return null for that field.

Rules:
- date: the date in ISO 8601 format YYYY-MM-DD. If no date is clearly indicated, set to null.
- country: the ISO-3166 alpha-3 country code (e.g. GBR, USA, FRA, ESP, HKG). If no country is clearly indicated, set to null.
- direction: exactly "ENTRY" or "EXIT". If no direction is clearly indicated, set to null.
- confidence reflects how legible/certain the visible fields are, from 0 (unreadable) to 1 (fully clear). If everything is null, confidence should be 0.

Return ONLY a JSON object with these exact keys. Set any unreadable field to null.
Example 1: 
Input: Image of a stamp clearly shows the country name, date, and direction.
{"date": "2024-03-15", "country": "GBR", "direction": "ENTRY", "confidence": 0.85}
Example 2: 
Input: Image shows a smudged stamp, but fields are unreadable.
Output: {"date": null, "country": null, "direction": null, "confidence": 0}
Example 3:
Input: Image shows a blank page or no visible stamp.
Output: {"date": null, "country": null, "direction": null, "confidence": 0}

Critical rules:
- If you cannot clearly identify a field, you MUST set it to null. Do NOT guess based on typical passport stamps
"""


_SYSTEM_PROMPT_old = """
Task: Extract entry/exit stamp data from a passport page image.

Evaluate each field INDEPENDENTLY. A stamp can have some legible fields 
and some illegible fields at the same time — this is the normal case, 
not an edge case. Do not let confidence in one field affect your answer 
for another field.

Fields:
- date: ISO 8601 (YYYY-MM-DD). Only return a date if every digit is 
  visually distinguishable. If any digit is ambiguous, smudged, or 
  requires assumption (e.g. "this is probably a 3 because that's a 
  common day"), set to null.
- country: ISO-3166 alpha-3 code (e.g. GBR, USA, FRA, ESP, HKG). Only 
  return a code if the country identifier (name, coat of arms, or 
  unambiguous text) is directly visible. Do not infer country from 
  language, script style, or stamp shape alone. If you cannot point to 
  the literal visual evidence, set to null.
- direction: exactly "ENTRY" or "EXIT". Only return this if an explicit 
  word, arrow, or symbol indicates direction. Do not infer direction 
  from context (e.g. "this looks like a departure stamp because it's 
  on the left page"). If ambiguous, set to null.
- confidence: 0 (nothing usable) to 1 (all visible fields fully clear). 
  If everything is null, confidence must be 0.

Hard rule: for each field, ask "could I point to the exact pixels that 
prove this value?" If not, the field is null. Guessing a plausible value 
is a critical failure — a null is always the correct answer over a guess.

Return ONLY a JSON object with exactly these keys: date, country, 
direction, confidence.

Example 1 — fully legible stamp:
{"date": "2024-03-15", "country": "GBR", "direction": "ENTRY", "confidence": 0.85}

Example 2 — partially legible stamp (country and direction clear, date smudged):
{"date": null, "country": "FRA", "direction": "EXIT", "confidence": 0.5}

Example 3 — partially legible stamp (date clear, country stamp too faded to read, no direction marker visible):
{"date": "2023-11-02", "country": null, "direction": null, "confidence": 0.4}

Example 4 — smudged/illegible stamp:
{"date": null, "country": null, "direction": null, "confidence": 0}

Example 5 — no stamp:
{"date": null, "country": null, "direction": null, "confidence": 0}
"""


_SYSTEM_PROMPT = """
Task: Extract entry/exit stamp data from a passport page image.

BASE RATE: Most stamps you will encounter are partially illegible or 
degraded. A fully legible stamp with all three fields clearly readable 
is the exception, not the norm. The presence of visible ink does not 
mean a field is readable — smudging, overlap, low contrast, and partial 
strikes are the default condition of real stamps, not edge cases.

COST ASYMMETRY: A wrong value is far more costly than a null. Null is 
a correct, successful output — not a fallback or failure state. Guessing 
a plausible value when the evidence is ambiguous is the single worst 
outcome this task can produce, worse than returning null for every field.

STEP 1 — TRANSCRIBE (do this before any judgment):
For each mark, character, digit, or symbol visible on the stamp, write 
out literally what you can see, in reading order. Use "?" for any single 
character you cannot distinguish with certainty (e.g. "202?-03-1?"). Do 
not fill in missing or unclear characters based on what would be 
plausible. Do this for the date, any text/imagery identifying a country, 
and any arrow/word/symbol indicating direction — separately.

STEP 2 — SCORE LEGIBILITY (based only on your Step 1 transcription):
For each of the three fields, assign a legibility score from 0.0 to 1.0:
- 1.0: every character/symbol needed for the field is unambiguous in 
  your transcription, no "?" present
- 0.5: partially visible, at least one character is uncertain or a "?"
- 0.0: not visible at all, or transcription is entirely "?"

STEP 3 — APPLY FIELD RULES (using only Step 1 + Step 2, evaluate each 
field independently — one field's clarity has no bearing on another):

- date: ISO 8601 (YYYY-MM-DD). Only output a date if its legibility 
  score is 1.0. Any "?" in the date transcription means null.
- country: ISO-3166 alpha-3 code (e.g. GBR, USA, FRA, ESP, HKG). Only 
  output a code if the country identifier's legibility score is 1.0 
  AND you can cite what you saw (name, coat of arms, unambiguous text). 
  Never infer country from language style, script, or stamp shape alone.
- direction: exactly "ENTRY" or "EXIT". Only output this if the 
  direction identifier's legibility score is 1.0 — an explicit word, 
  arrow, or symbol. Never infer direction from context, page position, 
  or stamp type.
- confidence: 0 (nothing usable) to 1 (all visible fields fully clear). 
  If all three fields are null, confidence must be 0.

FINAL CHECK before responding: for each non-null field, confirm you 
transcribed it in Step 1 with zero "?" characters. If you cannot meet 
this bar, change the field to null now.

Return ONLY a JSON object with exactly these keys: date, country, 
direction, confidence. Do not include your transcription or legibility 
scores in the output — use them only as internal reasoning steps.

Example 1 — fully legible stamp:
{"date": "2024-03-15", "country": "GBR", "direction": "ENTRY", "confidence": 0.85}

Example 2 — partially legible stamp (country and direction clear, date smudged):
{"date": null, "country": "FRA", "direction": "EXIT", "confidence": 0.5}

Example 3 — partially legible stamp (date clear, country stamp too faded to read, no direction marker visible):
{"date": "2023-11-02", "country": null, "direction": null, "confidence": 0.4}

Example 4 — smudged/illegible stamp:
{"date": null, "country": null, "direction": null, "confidence": 0}

Example 5 — no stamp:
{"date": null, "country": null, "direction": null, "confidence": 0}
"""


class LocalExtractionResult(BaseModel):
    date: str | None
    country: str | None
    direction: str | None
    confidence: float


class LocalLlamaModel:
    def __init__(self):
        self.model_type = "local"
    
    def _create_payload(self, image_string: str):
        payload = {
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": [
                    {"type": "text", "text": "Extract the stamp data as JSON."},
                    {"type": "image_url", "image_url": {"url": image_string}}
                ]}
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "stamp", "strict": True, "schema": _SCHEMA}
            },
            "temperature": 0
        }

        return payload


    def extract(self, image_string: str):
        payload = self._create_payload(image_string)

        response = httpx.post("http://localhost:8080/v1/chat/completions", json=payload, timeout=600.0)
        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        parsed = json.loads(content)
        stamp = LocalExtractionResult.model_validate(parsed)

        return stamp


if __name__ == "__main__":
    model = LocalLlamaModel()
    image_path = "/Users/wilsontee/travel-history-reconstruction/local_data/my_passport_stamps/pg_5_stamp_1.png"

    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    print(model.extract(b64))
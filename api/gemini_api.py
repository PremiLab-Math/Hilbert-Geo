"""Gemini client (via OpenAI-compatible gateway) for theorem-sequence + CDL generation."""

import os

from openai import OpenAI

from api.base import (
    build_golden_prompt,
    build_messages,
    image_to_base64,
    parse_model_response,
)

DEFAULT_MODEL = "gemini-2.5-pro"
DEFAULT_BASE_URL = os.environ.get("GEMINI_API_BASE", "http://aicanapi.com/v1")


class _KeyPool:
    """Round-robin pool over GOOGLE_API_KEYS (comma-separated) or GOOGLE_API_KEY."""

    def __init__(self, keys=None):
        if keys:
            self.keys = list(keys)
        else:
            raw = os.environ.get("GOOGLE_API_KEYS") or os.environ.get("GOOGLE_API_KEY") or ""
            self.keys = [k.strip() for k in raw.split(",") if k.strip()]
        self.idx = 0
        self.exhausted = set()

    def next(self):
        if not self.keys:
            raise RuntimeError("No Gemini API keys configured (set GOOGLE_API_KEYS or GOOGLE_API_KEY).")
        for _ in range(len(self.keys)):
            key = self.keys[self.idx % len(self.keys)]
            self.idx = (self.idx + 1) % len(self.keys)
            if key not in self.exhausted:
                return key
        raise RuntimeError("All Gemini API keys are exhausted.")

    def mark_exhausted(self, key):
        self.exhausted.add(key)


_default_pool = _KeyPool()


def generate_gemini_cdl(
    problem_text,
    image_path,
    predicate_list,
    model=DEFAULT_MODEL,
    problem_id=0,
    examples_data=None,
    api_key=None,
    base_url=None,
    max_tokens=16000,
    temperature=0.1,
    key_pool=None,
):
    """Call Gemini through an OpenAI-compatible base URL and return validated JSON."""
    image_b64 = image_to_base64(image_path) if image_path else None
    if not image_b64 and not problem_text:
        return {"status": "error", "message": "neither image nor text provided"}

    pool = key_pool or _default_pool
    key = api_key or pool.next()

    golden_prompt = build_golden_prompt(predicate_list, examples_data)
    messages = build_messages(problem_text, image_b64, golden_prompt, problem_id, examples_data)

    client = OpenAI(api_key=key, base_url=base_url or DEFAULT_BASE_URL)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=120.0,
        )
    except Exception as e:
        msg = str(e)
        if "429" in msg or "quota" in msg.lower() or "exhausted" in msg.lower():
            pool.mark_exhausted(key)
        return {"status": "error", "message": msg}

    raw = response.choices[0].message.content if response.choices else ""
    data, err = parse_model_response(raw, problem_id, problem_text)
    if err:
        return {"status": "error", "message": err, "raw_output": raw}
    return {"status": "success", "data": data}

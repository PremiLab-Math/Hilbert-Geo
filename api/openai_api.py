"""OpenAI / ChatGPT client for theorem-sequence + CDL generation."""

import os

from openai import OpenAI

from api.base import (
    build_golden_prompt,
    build_messages,
    image_to_base64,
    parse_model_response,
)

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_BASE_URL = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")


def _client(api_key=None, base_url=None):
    return OpenAI(
        api_key=api_key or os.environ["OPENAI_API_KEY"],
        base_url=base_url or DEFAULT_BASE_URL,
    )


def generate_cdl(
    problem_text,
    image_path,
    predicate_list,
    model=DEFAULT_MODEL,
    problem_id=0,
    examples_data=None,
    api_key=None,
    base_url=None,
    max_tokens=8000,
    temperature=0.1,
):
    """Call an OpenAI-compatible chat model and return validated problem JSON.

    Returns dict {"status": "success", "data": {...}} or
    {"status": "error", "message": ...}.
    """
    image_b64 = image_to_base64(image_path) if image_path else None
    if not image_b64 and not problem_text:
        return {"status": "error", "message": "neither image nor text provided"}

    golden_prompt = build_golden_prompt(predicate_list, examples_data)
    messages = build_messages(problem_text, image_b64, golden_prompt, problem_id, examples_data)

    response = _client(api_key, base_url).chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content if response.choices else ""
    data, err = parse_model_response(raw, problem_id, problem_text)
    if err:
        return {"status": "error", "message": err, "raw_output": raw}
    return {"status": "success", "data": data}


def generate_chatgpt_cdl(*args, **kwargs):
    """Alias for generate_cdl, kept for clarity when mixing providers."""
    return generate_cdl(*args, **kwargs)

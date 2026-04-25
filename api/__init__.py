"""Model API helpers for theorem-sequence + CDL generation."""

from api.base import (
    PROMPT_TEMPLATE,
    JSON_EXAMPLE,
    ProblemSchema,
    build_geometry_prompt,
    build_golden_prompt,
    build_messages,
    encode_image,
    fix_incomplete_json,
    image_to_base64,
    load_few_shot_examples,
    load_valid_predicates,
    normalize_api_response,
    parse_model_response,
)
from api.claude_api import generate_claude_cdl
from api.gemini_api import generate_gemini_cdl
from api.openai_api import generate_cdl, generate_chatgpt_cdl

__all__ = [
    "PROMPT_TEMPLATE",
    "JSON_EXAMPLE",
    "ProblemSchema",
    "build_geometry_prompt",
    "build_golden_prompt",
    "build_messages",
    "encode_image",
    "fix_incomplete_json",
    "image_to_base64",
    "load_few_shot_examples",
    "load_valid_predicates",
    "normalize_api_response",
    "parse_model_response",
    "generate_cdl",
    "generate_chatgpt_cdl",
    "generate_gemini_cdl",
    "generate_claude_cdl",
]

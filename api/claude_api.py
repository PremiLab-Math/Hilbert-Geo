"""Claude (Anthropic SDK) client for theorem-sequence + CDL generation."""

import base64
import os
from pathlib import Path

from api.base import (
    _DEFAULT_DAG,
    build_golden_prompt,
    parse_model_response,
)

DEFAULT_MODEL = "claude-opus-4-7"


def _image_block(image_path):
    if not image_path:
        return None
    path = Path(image_path)
    suffix = path.suffix.lower()
    media_type = "image/jpeg" if suffix in {".jpg", ".jpeg"} else "image/png"
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": base64.b64encode(path.read_bytes()).decode("utf-8"),
        },
    }


def _build_anthropic_messages(problem_text, image_path, examples_data, problem_id):
    """Anthropic message format: examples are concatenated into a single user turn."""
    user_blocks = []

    for i, ex in enumerate(examples_data or [], 1):
        user_blocks.append({
            "type": "text",
            "text": (
                f"Example {i} (ID: {ex['problem_id']}):\n"
                f"Natural Language Description: \"{ex['problem_text']}\"\n"
                f"Expected output JSON:\n"
                f"  construction_cdl: {ex['construction_cdl']}\n"
                f"  text_cdl: {ex['text_cdl']}\n"
                f"  image_cdl: {ex['image_cdl']}\n"
                f"  goal_cdl: {ex['goal_cdl']}\n"
                f"  problem_answer: {ex['problem_answer']}\n"
                f"  theorem_seqs: {ex.get('theorem_seqs', [])}\n"
                f"  theorem_seqs_dag: {ex.get('theorem_seqs_dag', _DEFAULT_DAG)}\n"
            ),
        })

    user_blocks.append({
        "type": "text",
        "text": (
            f"Now process this problem (ID: {problem_id}):\n"
            f"Natural Language Description: \"{problem_text or '(No text description, analyze the image only)'}\"\n\n"
            "Output a complete JSON object with all required fields."
        ),
    })

    img_block = _image_block(image_path)
    if img_block:
        user_blocks.append(img_block)

    return [{"role": "user", "content": user_blocks}]


def generate_claude_cdl(
    problem_text,
    image_path,
    predicate_list,
    model=DEFAULT_MODEL,
    problem_id=0,
    examples_data=None,
    api_key=None,
    max_tokens=8000,
    temperature=0.1,
):
    """Call Claude via the Anthropic SDK and return validated problem JSON."""
    try:
        from anthropic import Anthropic
    except ImportError:
        return {"status": "error", "message": "anthropic SDK not installed (pip install anthropic)"}

    if not image_path and not problem_text:
        return {"status": "error", "message": "neither image nor text provided"}

    golden_prompt = build_golden_prompt(predicate_list, examples_data)
    system_prompt = (
        golden_prompt
        + "\n\nIMPORTANT: Respond ONLY with a single JSON object. Do not wrap it in markdown, do not add commentary."
    )

    client = Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_prompt,
        messages=_build_anthropic_messages(problem_text, image_path, examples_data, problem_id),
    )

    raw = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
    data, err = parse_model_response(raw, problem_id, problem_text)
    if err:
        return {"status": "error", "message": err, "raw_output": raw}
    return {"status": "success", "data": data}

import base64
from pathlib import Path


def encode_image(image_path):
    image_path = Path(image_path)
    suffix = image_path.suffix.lower()
    mime_type = "image/jpeg" if suffix in {".jpg", ".jpeg"} else "image/png"
    return f"data:{mime_type};base64,{base64.b64encode(image_path.read_bytes()).decode('utf-8')}"


def build_geometry_prompt(problem_text, predicate_list, few_shot_examples=""):
    prompt = [
        "You are generating CDL for a geometry problem.",
        "Use only the allowed predicates.",
        f"Allowed predicates: {predicate_list}",
    ]
    if few_shot_examples:
        prompt.append(f"Examples:\n{few_shot_examples}")
    prompt.append(f"Problem:\n{problem_text}")
    return "\n\n".join(prompt)

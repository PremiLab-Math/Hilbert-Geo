"""Shared helpers, prompts, and schema for theorem-sequence + CDL generation."""

import base64
import json
import os
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

import PIL.Image
from pydantic import BaseModel, Field


class ProblemSchema(BaseModel):
    problem_id: int = Field(description="Unique identifier of the problem.")
    annotation: str = Field(description="Annotation. Empty string when none.")
    source: str = Field(description="Problem source, usually 'SolidGeo'.")
    problem_text_en: str = Field(description="Full English natural-language description of the problem.")
    construction_cdl: List[str] = Field(
        description=(
            "Auxiliary predicates that define the geometric construction "
            "(Shape / Collinear / Cocircular / Coplanar / Cospherical, etc.)."
        )
    )
    text_cdl: List[str] = Field(description="Geometric facts extracted ONLY from the textual description.")
    image_cdl: List[str] = Field(description="Geometric facts extracted ONLY from the image.")
    goal_cdl: str = Field(description="Solving goal, must be wrapped by 'Value(...)'.")
    problem_answer: str = Field(description="Standard answer: pure number or expression, no units.")
    problem_type: List[str] = Field(description="Problem type categories.")
    complexity_level: str = Field(description="Problem complexity level.")
    theorem_seqs: List[str] = Field(description="Sequence of theorems used to solve the problem.")
    theorem_seqs_dag: str = Field(description='JSON string of the theorem DAG, e.g. \'{"START": []}\'.')


PROMPT_TEMPLATE = """
You are an expert in geometry, logic, and computer science. Your task is to precisely convert a geometry problem (with natural language and an image) into a JSON object following the provided JSON Schema.
You must strictly follow the schema and output a complete JSON object.

Rule 0: Predicate Compliance (MOST IMPORTANT)
- All CDL predicates you generate (e.g., `Equal`, `Cone`, `LengthOfLine`) MUST be strictly chosen from the official list below.
- Using any predicate that does not appear in this list is strictly forbidden.

--- Official Predicate List ---
{valid_predicates_str}
--- End of Official Predicate List ---

Core Rules and Constraints:

1) Information Source Separation:
   - `text_cdl` MUST include only facts extracted from the natural language description.
   - `image_cdl` MUST include only facts directly observable from the image (e.g., length labels, right-angle marks, shape recognition).
   - If a fact appears in both text and image, include it in both fields.

2) construction_cdl - Geometric construction predicates (IMPORTANT):
   `construction_cdl` defines basic construction for entities, and MUST include the following types where applicable:
   - Shape predicates: define edges/segments of shapes
     * For segments/edges: `Shape(AB,BC,CD,DA)` or `Shape(OP,PO)` or `Shape(PQ,QP)`
     * For points (spheres etc.): `Shape(O)` or `Shape(P)`
     * Example: rectangles require `Shape(AB,BC,CD,DA)`; cylinders require `Shape(PQ,QP)`
   - Collinearity/Cocircular/Coplanar/Cospherical:
     * `Collinear(PABQ)` - P, A, B, Q are collinear
     * `Cocircular(O)` - O is on a circle (for cone/cylinder base center)
     * `Cocircular(P)`, `Cocircular(Q)` - P and Q on their respective circles
     * `Coplanar(U,ABCD)` - U coplanar with ABCD
     * `Cospherical(O)` - O is on a sphere (for spheres)
   Important:
   - Carefully analyze the image to identify all necessary edges/segments/relations
   - Only return `[]` when no construction info is truly needed
   - Most problems require at least one `Shape(...)`
   - Cones/cylinders often need `Shape(...)` and `Cocircular(...)`
   - Spheres often need `Shape(O)` and `Cospherical(O)`
   - Cubes/prisms often need multiple `Shape(...)` with `Coplanar(...)`

3) Answer formatting:
   - `problem_answer` MUST be a pure number or expression (e.g., "10", "254.47", "36*pi"), and MUST NOT contain units or extra text.

4) Core predicate logic:
   - Length/Height/Generator: `Equal(LengthOfLine(A,B),5)`, `Equal(HeightOfCone(O,P),12)`, `Equal(BusbarOfCone(O,P),13)`
   - Radius/Diameter: `Equal(RadiusOfCircle(O),5)`, `Value(DiameterOfCircle(O))`
   - Relations: `PerpendicularBetweenLine(A,B,C,D)`, `ParallelBetweenLine(A,B,C,D)`
   - Goal: the requested quantity MUST be wrapped by `Value(...)`.

5) Predicate and Operator Legality (CRITICAL):
   - Only reuse names from the official predicate list; DO NOT invent new construction predicates (e.g., `Triangle`, `Line`, `Angle` are FORBIDDEN).
   - Quantities allowed in CDL expressions (including `goal_cdl`) are LIMITED to:
     `VolumeOfCone`, `VolumeOfCylinder`, `VolumeOfSphere`, `VolumeOfCuboid`, `VolumeOfQuadrangularPyramid`,
     `SurfaceAreaOfCylinder`, `SurfaceAreaOfCuboid`, `SurfaceAreaOfQuadrangularPrism`, `SurfaceAreaOfQuadrangularPyramid`,
     `LateralareaOfCone`, `LateralareaOfCylinder`, `AreaOfCircle`, `AreaOfSphere`, `AreaOfCuboid`, `AreaOfQuadrilateral`,
     `PerimeterOfQuadrilateral`, `DiameterOfCircle`, `RadiusOfCircle`, `LengthOfLine`, `HeightOfCone`, `HeightOfCylinder`, `BusbarOfCone`.
     If a problem mentions other quantities, rewrite them using these standard quantities or include supporting info in `text_cdl/image_cdl` and then use the standard quantities.
   - Only the following algebraic operators are allowed: `Value`, `Add`, `Sub`, `Mul`, `Div`. For "1/2 X", write `Mul(1/2,X)`.
   - Formatting: NO extra spaces inside any predicate/operator. Use `Add(A,B,C)` and `Equal(HeightOfCylinder(P,Q),2)`, NOT `Add(A, B)` or `Equal(..., 2)`. Also avoid leading/trailing spaces in names.

6) Completeness Checks:
   - Ensure every entity used by `text_cdl`/`image_cdl` exists in `construction_cdl`
   - Ensure the target entity in `goal_cdl` exists in the construction as well
   - Self-check after generation: verify all predicates/operators are allowed, no extra spaces, and no undeclared entities are referenced.

7) Theorem Sequence (theorem_seqs / theorem_seqs_dag):
   - `theorem_seqs` is the ordered list of theorem applications used to derive the answer (string form, e.g. `"line_addition(1,AB,BC)"`).
   - `theorem_seqs_dag` is a JSON string describing the directed acyclic graph between those theorem steps; if unknown, use `"{{\\"START\\": []}}"`.
   - When the natural-language solution is available, derive these from it; otherwise leave `theorem_seqs` empty and `theorem_seqs_dag` as the START stub.

Important: Output Requirements
1. You MUST output a complete JSON object with all required fields.
2. All CDL fields MUST be arrays of strings (e.g., `["Cylinder(O,P)", "Equal(HeightOfCylinder(O,P),12)"]`).
3. `goal_cdl` MUST be a string (e.g., `"Value(VolumeOfCone(O,P))"`).
4. Required fields:
   - `problem_id`: integer
   - `annotation`: string (can be empty)
   - `source`: string (usually "SolidGeo")
   - `problem_text_en`: string
   - `construction_cdl`: array of strings
   - `text_cdl`: array of strings
   - `image_cdl`: array of strings
   - `goal_cdl`: string
   - `problem_answer`: string
   - `problem_type`: array of strings
   - `complexity_level`: string
   - `theorem_seqs`: array of strings (can be empty)
   - `theorem_seqs_dag`: JSON string (e.g., '{{"START": []}}')

Output Example:
JSON_EXAMPLE_PLACEHOLDER

Ensure the JSON is complete and properly formatted. Do NOT truncate or omit any fields.
"""

_DEFAULT_DAG = '{"START": []}'

JSON_EXAMPLE = """```json
{
  "problem_id": 1,
  "annotation": "",
  "source": "SolidGeo",
  "problem_text_en": "Find the volume of the cone.",
  "construction_cdl": ["Shape(OP,PO)", "Cocircular(O)"],
  "text_cdl": ["Equal(HeightOfCone(O,P),12)"],
  "image_cdl": ["Cone(O,P)", "Equal(BusbarOfCone(O,P),13)"],
  "goal_cdl": "Value(VolumeOfCone(O,P))",
  "problem_answer": "10",
  "problem_type": ["Solid Geometry"],
  "complexity_level": "Level 1",
  "theorem_seqs": [],
  "theorem_seqs_dag": "{\\"START\\": []}"
}
```"""


def encode_image(image_path):
    image_path = Path(image_path)
    suffix = image_path.suffix.lower()
    mime_type = "image/jpeg" if suffix in {".jpg", ".jpeg"} else "image/png"
    return f"data:{mime_type};base64,{base64.b64encode(image_path.read_bytes()).decode('utf-8')}"


def image_to_base64(image_path, max_size=(1024, 1024), quality=85):
    """Down-scale, JPEG-encode, and return a data URL for an image."""
    if not image_path:
        return None
    try:
        with PIL.Image.open(image_path) as img:
            img.thumbnail(max_size, PIL.Image.Resampling.LANCZOS)
            if img.mode != "RGB":
                img = img.convert("RGB")
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=quality)
        return f"data:image/jpeg;base64,{base64.b64encode(buffered.getvalue()).decode('utf-8')}"
    except Exception:
        return None


def load_valid_predicates(gdl_path):
    """Load all legal predicate names from a predicate_GDL.json file."""
    with open(gdl_path, "r", encoding="utf-8") as f:
        gdl_data = json.load(f)

    predicate_names = set()
    for category in ("Entity", "Relation", "Attribution"):
        for key in gdl_data.get(category, {}):
            predicate_names.add(key.split("(")[0])
    for preset_key in ("BasicEntity", "Construction"):
        for name in gdl_data.get("Preset", {}).get(preset_key, []):
            predicate_names.add(name)
    predicate_names.update({"Equal", "Value"})
    return sorted(predicate_names)


def load_few_shot_examples(train_dir, images_dir, max_examples=10):
    """Load few-shot example JSONs together with their base64-encoded images."""
    examples_data: List[Dict[str, Any]] = []
    if not train_dir or not os.path.isdir(train_dir):
        return examples_data, 0

    json_files = [f for f in os.listdir(train_dir) if f.endswith(".json")]
    json_files.sort(key=lambda x: int(x.split(".")[0]) if x.split(".")[0].isdigit() else 999_999)

    for json_file in json_files:
        if len(examples_data) >= max_examples:
            break
        problem_id = json_file.split(".")[0]
        try:
            with open(os.path.join(train_dir, json_file), "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue

        cdl_keys = ("construction_cdl", "text_cdl", "image_cdl", "goal_cdl")
        if not any(data.get(k) for k in cdl_keys):
            continue

        problem_text = (data.get("problem_text_en") or "").strip()
        if not problem_text:
            txt_path = os.path.join(train_dir, f"{problem_id}.txt")
            if os.path.exists(txt_path):
                with open(txt_path, "r", encoding="utf-8") as f:
                    problem_text = f.read().strip()

        img_b64 = None
        for ext in (".png", ".jpg", ".jpeg"):
            candidate = os.path.join(images_dir, f"{problem_id}{ext}") if images_dir else ""
            if candidate and os.path.exists(candidate):
                img_b64 = image_to_base64(candidate)
                break

        examples_data.append({
            "problem_id": problem_id,
            "problem_text": problem_text or "(no text)",
            "image_base64": img_b64,
            "text_cdl": data.get("text_cdl", []),
            "image_cdl": data.get("image_cdl", []),
            "construction_cdl": data.get("construction_cdl", []),
            "goal_cdl": data.get("goal_cdl", ""),
            "problem_answer": data.get("problem_answer", ""),
            "theorem_seqs": data.get("theorem_seqs", []),
            "theorem_seqs_dag": data.get("theorem_seqs_dag", '{"START": []}'),
        })

    return examples_data, len(examples_data)


def build_golden_prompt(predicate_list, examples_data=None):
    """Render the prompt template with the predicate list and example pointers."""
    if isinstance(predicate_list, (list, tuple, set)):
        predicate_str = ", ".join(sorted(predicate_list))
    else:
        predicate_str = str(predicate_list)

    prompt = PROMPT_TEMPLATE.format(valid_predicates_str=predicate_str)
    prompt = prompt.replace("JSON_EXAMPLE_PLACEHOLDER", JSON_EXAMPLE)

    if examples_data:
        prompt += "\n--- High-quality examples. STRICTLY follow their format and logic. ---\n"
        for i, ex in enumerate(examples_data, 1):
            img_note = f"Image: {ex['problem_id']}.png" if ex.get("image_base64") else "No image"
            prompt += (
                f"\n#### Example {i} (ID: {ex['problem_id']})\n"
                f"- problem_text: {ex['problem_text']}\n"
                f"- {img_note}\n"
                f"- text_cdl: {ex['text_cdl']}\n"
                f"- image_cdl: {ex['image_cdl']}\n"
                f"- construction_cdl: {ex['construction_cdl']}\n"
                f"- goal_cdl: {ex['goal_cdl']}\n"
                f"- problem_answer: {ex['problem_answer']}\n"
                f"- theorem_seqs: {ex.get('theorem_seqs', [])}\n"
                f"- theorem_seqs_dag: {ex.get('theorem_seqs_dag', _DEFAULT_DAG)}\n"
            )
    return prompt


def build_messages(problem_text, image_b64, golden_prompt, problem_id, examples_data=None):
    """Assemble system + few-shot + user messages in OpenAI chat format."""
    messages: List[Dict[str, Any]] = [{
        "role": "system",
        "content": golden_prompt + "\n\nIMPORTANT: Your JSON output must include all required fields and strictly follow the format above.",
    }]

    for i, ex in enumerate(examples_data or [], 1):
        ex_user_content: List[Dict[str, Any]] = [{
            "type": "text",
            "text": (
                f"Example {i} (ID: {ex['problem_id']}):\n"
                f"Natural Language Description: \"{ex['problem_text']}\"\n\n"
                "Please analyze the image and text, then generate the CDL fields in JSON format."
            ),
        }]
        if ex.get("image_base64"):
            ex_user_content.append({"type": "image_url", "image_url": {"url": ex["image_base64"]}})
        messages.append({"role": "user", "content": ex_user_content})
        messages.append({
            "role": "assistant",
            "content": json.dumps({
                "construction_cdl": ex["construction_cdl"],
                "text_cdl": ex["text_cdl"],
                "image_cdl": ex["image_cdl"],
                "goal_cdl": ex["goal_cdl"],
                "problem_answer": ex["problem_answer"],
                "theorem_seqs": ex.get("theorem_seqs", []),
                "theorem_seqs_dag": ex.get("theorem_seqs_dag", '{"START": []}'),
            }, ensure_ascii=False),
        })

    user_content: List[Dict[str, Any]] = [{
        "type": "text",
        "text": (
            f"Now process this problem (ID: {problem_id}):\n"
            f"Natural Language Description: \"{problem_text or '(No text description, analyze the image only)'}\"\n\n"
            "Please analyze the image and text, then generate a complete JSON output including all required fields."
        ),
    }]
    if image_b64:
        user_content.append({"type": "image_url", "image_url": {"url": image_b64}})
    messages.append({"role": "user", "content": user_content})

    return messages


def fix_incomplete_json(json_str):
    """Best-effort repair for truncated JSON returned by an LLM."""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass
    fixed = json_str.strip()
    if fixed.startswith("{") and not fixed.rstrip().endswith("}"):
        last_comma = fixed.rfind(",")
        fixed = (fixed[:last_comma] + "}") if last_comma > 0 else (fixed + "}")
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        return None


def _normalize_cdl_list(cdl_data):
    if cdl_data is None:
        return []
    if not isinstance(cdl_data, list):
        return []
    out: List[str] = []
    for item in cdl_data:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict):
            predicate = item.get("predicate") or (next(iter(item.keys()), None) if item else None)
            if not predicate:
                continue
            params = item.get("params") or item.get(predicate) or []
            if isinstance(params, list):
                out.append(f"{predicate}({','.join(str(p) for p in params)})")
            else:
                out.append(str(predicate))
    return out


def normalize_api_response(data, problem_id, problem_text_en):
    """Fill missing fields and coerce CDL fields to consistent shapes."""
    normalized: Dict[str, Any] = {
        "problem_id": data.get("problem_id") or problem_id,
        "annotation": data.get("annotation") or "",
        "source": data.get("source") or "SolidGeo",
        "problem_text_en": data.get("problem_text_en") or data.get("problem_text") or problem_text_en,
        "problem_answer": data.get("problem_answer") or "",
        "problem_type": data.get("problem_type") or [],
        "complexity_level": data.get("complexity_level") or "",
        "theorem_seqs": data.get("theorem_seqs") or [],
        "theorem_seqs_dag": data.get("theorem_seqs_dag") or '{"START": []}',
        "construction_cdl": _normalize_cdl_list(data.get("construction_cdl")),
        "text_cdl": _normalize_cdl_list(data.get("text_cdl")),
        "image_cdl": _normalize_cdl_list(data.get("image_cdl")),
    }

    goal_cdl = data.get("goal_cdl")
    if isinstance(goal_cdl, list) and goal_cdl:
        normalized["goal_cdl"] = goal_cdl[0] if isinstance(goal_cdl[0], str) else str(goal_cdl[0])
    elif isinstance(goal_cdl, str):
        normalized["goal_cdl"] = goal_cdl
    else:
        normalized["goal_cdl"] = ""

    nested = data.get("cdl")
    if isinstance(nested, dict):
        if "construction_cdl" in nested:
            normalized["construction_cdl"] = _normalize_cdl_list(nested["construction_cdl"])
        if "text_cdl" in nested:
            normalized["text_cdl"] = _normalize_cdl_list(nested["text_cdl"])
        if "image_cdl" in nested:
            normalized["image_cdl"] = _normalize_cdl_list(nested["image_cdl"])
        if "goal_cdl" in nested:
            g = nested["goal_cdl"]
            if isinstance(g, list) and g:
                normalized["goal_cdl"] = g[0] if isinstance(g[0], str) else str(g[0])
            elif isinstance(g, str):
                normalized["goal_cdl"] = g

    return normalized


def parse_model_response(raw_text, problem_id, problem_text):
    """Strip markdown fences, parse JSON, normalize, and validate against ProblemSchema."""
    text = (raw_text or "").strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = fix_incomplete_json(text)
        if parsed is None:
            return None, "JSON parse failed and could not be repaired."

    api_problem_id = parsed.get("problem_id")
    try:
        api_problem_id = int(api_problem_id) if api_problem_id is not None else None
    except (ValueError, TypeError):
        api_problem_id = None

    normalized = normalize_api_response(parsed, api_problem_id or problem_id, problem_text)
    try:
        validated = ProblemSchema(**normalized)
    except Exception as e:
        return None, f"Schema validation failed: {e}"
    return validated.dict(), None


def build_geometry_prompt(problem_text, predicate_list, few_shot_examples=""):
    """Lightweight single-string prompt builder kept for backward compatibility."""
    parts = [
        "You are generating CDL and a theorem sequence for a geometry problem.",
        "Use only the allowed predicates.",
        f"Allowed predicates: {predicate_list}",
    ]
    if few_shot_examples:
        parts.append(f"Examples:\n{few_shot_examples}")
    parts.append(f"Problem:\n{problem_text}")
    return "\n\n".join(parts)

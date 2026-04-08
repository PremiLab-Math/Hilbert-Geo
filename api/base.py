import base64
from pathlib import Path


def encode_image(image_path):
    image_path = Path(image_path)
    suffix = image_path.suffix.lower()
    mime_type = "image/jpeg" if suffix in {".jpg", ".jpeg"} else "image/png"
    return f"data:{mime_type};base64,{base64.b64encode(image_path.read_bytes()).decode('utf-8')}"


def _stringify_predicates(predicate_list):
    if isinstance(predicate_list, str):
        return predicate_list
    return "\n".join(str(predicate) for predicate in predicate_list)


def build_cdl_parsing_prompt(predicate_list, few_shot_examples=""):
    valid_predicates_str = _stringify_predicates(predicate_list)
    prompt = f"""You are an expert in geometry, logic, and computer science. Your task is to precisely convert a geometry problem (with natural language and an image) into a JSON object following the provided JSON Schema. You must strictly follow the schema and output a complete JSON object.

Rule 0: Predicate Compliance (MOST IMPORTANT)
- All CDL predicates you generate (e.g., Equal, Cone, LengthOfLine) MUST be strictly chosen from the official list below.
- Using any predicate that does not appear in this list is strictly forbidden.
--- Official Predicate List ---
{valid_predicates_str}
--- End of Official Predicate List ---

Core Rules and Constraints:
1) Information Source Separation:
- text_cdl MUST include only facts extracted from the natural language description.
- image_cdl MUST include only facts directly observable from the image (e.g., length labels, right-angle marks, shape recognition).
- If a fact appears in both text and image, include it in both fields.

2) construction_cdl - Geometric construction predicates (IMPORTANT):
construction_cdl defines basic construction for entities, and MUST include the following types where applicable:
- Shape predicates: define edges/segments of shapes
* For segments/edges: Shape(AB,BC,CD,DA) or Shape(OP,PO) or Shape(PQ,QP)
* For points (spheres etc.): Shape(O) or Shape(P)
* Example: rectangles require Shape(AB,BC,CD,DA); cylinders require Shape(PQ,QP)
- Collinearity/Cocircular/Coplanar/Cospherical:
* Collinear(PABQ) - P, A, B, Q are collinear
* Cocircular(O) - O is on a circle (for cone/cylinder base center)
* Coplanar(U,ABCD) - U coplanar with ABCD
* Cospherical(O) - O is on a sphere (for spheres)
Important:
- Carefully analyze the image to identify all necessary edges/segments/relations
- Most problems require at least one Shape(...)
- Cones/cylinders often need Shape(...) and Cocircular(...)
- Spheres often need Shape(O) and Cospherical(O)

3) Answer formatting:
- problem_answer MUST be a pure number or expression (e.g., "10", "36*pi"), and MUST NOT contain units or extra text.

4) Core predicate logic:
- Length/Height:
Equal(LengthOfLine(A,B),5),
Equal(HeightOfCone(O,P),12)
- Relations:
PerpendicularBetweenLine(A,B,C,D),
ParallelBetweenLine(A,B,C,D)
- Goal: the requested quantity MUST be wrapped by Value(...).

5) Predicate and Operator Legality (CRITICAL):
- Only reuse names from the official predicate list; DO NOT invent new construction predicates.
- Quantities allowed in CDL expressions are LIMITED to standard forms: VolumeOfCone, SurfaceAreaOfCylinder, AreaOfCircle, LengthOfLine, etc.
- Only the following algebraic operators are allowed: Value, Add, Sub, Mul, Div.
- Formatting: NO extra spaces inside any predicate/operator.

6) Completeness Checks:
- Ensure every entity used by text_cdl/image_cdl exists in construction_cdl
- Ensure the target entity in goal_cdl exists in the construction as well
- Self-check after generation: verify all predicates/operators are allowed, no extra spaces, and no undeclared entities are referenced.

Important: Output Requirements
1. You MUST output a complete JSON object with all required fields
2. All CDL fields MUST be arrays of strings
3. goal_cdl MUST be a string (e.g., "Value(VolumeOfCone(O,P))")"""
    if few_shot_examples:
        prompt = f"{prompt}\n\nFew-shot examples covering predicate usage:\n{few_shot_examples}"
    return prompt


def build_direct_solving_prompt(problem_text):
    return "\n".join(
        [
            "You are an expert in geometry and mathematics. Please solve the following geometry problem step by step.",
            "",
            "Important Instructions:",
            "1. Carefully analyze the problem text and the accompanying image",
            "2. Show your reasoning process step by step",
            "3. At the end, provide your final answer in a clear format",
            '4. Your final answer should be ONLY a number or mathematical expression (like "10", "5.5", "12*pi", "36*pi"), without any units or text',
            '5. Put your final answer on a line starting with "FINAL ANSWER: "',
            "Example format:",
            "FINAL ANSWER: 10",
            "or",
            "FINAL ANSWER: 36*pi",
            "Now, please solve this problem:",
            "",
            problem_text,
        ]
    )


def build_geometry_prompt(problem_text, predicate_list, few_shot_examples=""):
    return build_cdl_parsing_prompt(predicate_list, few_shot_examples=few_shot_examples)

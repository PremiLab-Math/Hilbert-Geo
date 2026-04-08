import os

from openai import OpenAI

from api.base import build_geometry_prompt, encode_image


def generate_cdl(problem_text, image_path, predicate_list, model="gpt-4o-mini"):
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    prompt = build_geometry_prompt(problem_text, predicate_list)
    image_url = encode_image(image_path)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": problem_text},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ],
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content

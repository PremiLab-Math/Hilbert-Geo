from api.openai_api import generate_cdl


def generate_gemini_cdl(problem_text, image_path, predicate_list, model="gemini-2.5-pro"):
    return generate_cdl(problem_text, image_path, predicate_list, model=model)

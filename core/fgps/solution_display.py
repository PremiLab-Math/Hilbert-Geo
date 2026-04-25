import re

from hilbert_geo.parse import inverse_parse_one, inverse_parse_one_theorem
from hilbert_geo.tools import (
    show_solution as _base_show_solution,
    get_solution_hypertree as _base_get_solution_hypertree,
    get_theorem_dag as _base_get_theorem_dag,
)


def _build_theorem_key_index(raw_theorem_gdl):
    theorem_key_index = {}
    if not isinstance(raw_theorem_gdl, dict):
        return theorem_key_index

    for theorem_key in raw_theorem_gdl:
        theorem_name = theorem_key.split("(", 1)[0]
        theorem_key_index.setdefault(theorem_name, theorem_key)

    return theorem_key_index


def _group_theorem_params(theorem, parsed_theorem_gdl):
    theorem_name, _, theorem_para = theorem
    if theorem_para is None or theorem_name not in parsed_theorem_gdl:
        return []

    grouped_para = []
    cursor = 0
    for para_len in parsed_theorem_gdl[theorem_name]["para_len"]:
        grouped_para.append("".join(theorem_para[cursor:cursor + para_len]))
        cursor += para_len
    return grouped_para


def _instantiate_theorem_premise(theorem, raw_theorem_gdl, parsed_theorem_gdl):
    theorem_name, theorem_branch, _ = theorem
    if theorem_name in {"prerequisite", "extended", "solve_eq", "init_problem"}:
        return None
    if not isinstance(raw_theorem_gdl, dict):
        return None

    theorem_key = _build_theorem_key_index(raw_theorem_gdl).get(theorem_name)
    if theorem_key is None:
        return None

    branch_key = str(theorem_branch) if theorem_branch is not None else "1"
    theorem_body = raw_theorem_gdl.get(theorem_key, {}).get(branch_key)
    if not theorem_body:
        return None

    premise = theorem_body.get("premise")
    if not premise:
        return None

    if "(" not in theorem_key or ")" not in theorem_key:
        return premise

    formal_para = [
        para.strip() for para in theorem_key.split("(", 1)[1].rsplit(")", 1)[0].split(",") if para.strip()
    ]
    actual_para = _group_theorem_params(theorem, parsed_theorem_gdl)
    if len(formal_para) != len(actual_para):
        return premise

    replaced = premise
    for formal, actual in sorted(zip(formal_para, actual_para), key=lambda item: len(item[0]), reverse=True):
        pattern = rf"(?<![A-Za-z]){re.escape(formal)}(?![A-Za-z])"
        replaced = re.sub(pattern, actual, replaced)

    return replaced


def _format_condition(problem, condition_id):
    if condition_id < 0:
        return f"[{condition_id}] prerequisite"

    predicate, item = problem.condition.items[condition_id][0], problem.condition.items[condition_id][1]
    if predicate == "Equation":
        condition_text = "Equation(" + str(item).replace(" ", "") + ")"
    else:
        condition_text = inverse_parse_one(predicate, item, problem)
    return f"[{condition_id}] {condition_text}"


def get_theorem_trace(problem, raw_theorem_gdl=None):
    theorem_trace = []
    for step in sorted(problem.timing):
        theorem, timing = problem.timing[step]
        conclusion_ids = list(problem.condition.ids_of_step.get(step, []))
        if theorem[0] == "init_problem" or not conclusion_ids:
            continue

        premise_ids = []
        for condition_id in conclusion_ids:
            premise_ids.extend(problem.condition.items[condition_id][2])
        premise_ids = sorted(set(premise_ids))

        theorem_trace.append(
            {
                "step": step,
                "theorem": inverse_parse_one_theorem(theorem, problem.parsed_theorem_GDL),
                "theorem_premise": _instantiate_theorem_premise(
                    theorem, raw_theorem_gdl, problem.parsed_theorem_GDL
                ),
                "premise_ids": premise_ids,
                "premise_conditions": [_format_condition(problem, condition_id) for condition_id in premise_ids],
                "conclusion_ids": conclusion_ids,
                "conclusions": [_format_condition(problem, condition_id) for condition_id in conclusion_ids],
                "timing": timing,
            }
        )

    return theorem_trace


def show_solution(problem, raw_theorem_gdl=None):
    _base_show_solution(problem)

    theorem_trace = get_theorem_trace(problem, raw_theorem_gdl)
    if not theorem_trace:
        return

    print()
    print("\033[34mTheorem Trace:\033[0m")
    for trace in theorem_trace:
        print(f"{trace['step']:>3} {trace['theorem']}")
        if trace["theorem_premise"]:
            print(f"    premise_formula: {trace['theorem_premise']}")
        if trace["premise_ids"]:
            print(f"    premise_ids: {tuple(trace['premise_ids'])}")
            for condition in trace["premise_conditions"]:
                print(f"      - {condition}")
        for conclusion in trace["conclusions"]:
            print(f"      + {conclusion}")
        print(f"    timing: {trace['timing']:.6f}s")


def get_solution_hypertree(problem, raw_theorem_gdl=None):
    hypertree = _base_get_solution_hypertree(problem)
    hypertree["theorem_trace"] = get_theorem_trace(problem, raw_theorem_gdl)
    return hypertree


def get_theorem_dag(problem):
    return _base_get_theorem_dag(problem)

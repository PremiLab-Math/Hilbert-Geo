if __package__ in {None, ""}:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hilbert_geo.data import DatasetLoader
from hilbert_geo.tools import load_json, save_json, safe_save_json, simple_show, show_solution
from hilbert_geo.tools import get_solution_hypertree, get_theorem_dag
from hilbert_geo.parse import parse_theorem_seqs
from hilbert_geo.solver import Interactor
from fgps import get_args
import os
import warnings
import time


def auto_run(path_datasets, dataset_name, path_logs):
    log_filename = os.path.join(path_logs, "run/auto_logs/{}.json".format(dataset_name))
    if not os.path.exists(log_filename):
        save_json({"start_pid": 1, "data": {}}, log_filename)
    log = load_json(log_filename)

    dl = DatasetLoader(dataset_name, path_datasets)
    solver = Interactor(dl.predicate_GDL, dl.theorem_GDL)
    warnings.filterwarnings("ignore")
    print("pid\tcorrect_answer\tsolved\tsolved_answer\ttiming(s)")

    for pid in range(log["start_pid"], dl.info["problem_number"] + 1):
        try:  # try solve
            timing = time.time()
            problem_CDL = dl.get_problem(pid)
            solver.load_problem(problem_CDL)

            for t_name, t_branch, t_para in parse_theorem_seqs(problem_CDL["theorem_seqs"]):
                solver.apply_theorem(t_name, t_branch, t_para)

            solver.problem.check_goal()  # check goal after applied theorem seqs

            timing = time.time() - timing

            simple_show(solver.problem, timing)  # show solved msg

            log["start_pid"] = pid + 1
            log["data"][pid] = [problem_CDL["problem_level"], timing]

            if pid % 100 == 0:
                safe_save_json(log, log_filename)

        except Exception as e:  # exception
            print("Exception: {}".format(repr(e)))

    safe_save_json(log, log_filename)


def run(path_datasets, dataset_name, path_logs):
    dl = DatasetLoader(dataset_name, path_datasets)
    solver = Interactor(dl.predicate_GDL, dl.theorem_GDL)
    while True:
        try:
            pid = input("<pid>:")
            problem_CDL = dl.get_problem(int(pid))
        except BaseException as e:
            print(repr(e) + "\n")
            continue

        solver.load_problem(problem_CDL)

        for t_name, t_branch, t_para in parse_theorem_seqs(problem_CDL["theorem_seqs"]):
            solver.apply_theorem(t_name, t_branch, t_para)

        solver.problem.check_goal()  # check goal after applied theorem seqs

        show_solution(solver.problem)  # show solving process

        save_json(solver.problem.parsed_problem_CDL,
                  os.path.join(path_logs, "run/problems/{}_{}_parsed_cdl.json".format(dataset_name, pid)))
        save_json(get_solution_hypertree(solver.problem),
                  os.path.join(path_logs, "run/problems/{}_{}_tree.json".format(dataset_name, pid)))
        save_json(get_theorem_dag(solver.problem),
                  os.path.join(path_logs, "run/problems/{}_{}_dag.json".format(dataset_name, pid)))

        print()


if __name__ == '__main__':
    args = get_args()

    if args.func == "auto_run":
        auto_run(args.path_datasets, args.dataset_name, args.path_logs)
    elif args.func == "run":
        run(args.path_datasets, args.dataset_name, args.path_logs)
    else:
        msg = "No function name {}.".format(args.func)
        raise Exception(msg)

    # auto_run(args.path_datasets, args.dataset_name, args.path_logs)
    # run(args.path_datasets, args.dataset_name, args.path_logs)

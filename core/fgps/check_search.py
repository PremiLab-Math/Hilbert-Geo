if __package__ in {None, ""}:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import os.path
from fgps import method, strategy, get_args
from hilbert_geo.tools import load_json
from hilbert_geo.data import DatasetLoader
import matplotlib.pyplot as plt


def check_search(path_datasets, dataset_name, path_logs):
    dl = DatasetLoader(dataset_name, path_datasets)
    config_count = 8  # search configuration count
    level_count = 6  # problem level count
    problem_total = [0 for _ in range(level_count + 1)]
    i_map = {}
    j_map = {}

    count = 0
    for m in method:
        for s in strategy:
            i_map[(m, s)] = count
            count += 1
    for pid in range(1, dl.info["problem_number"] + 1):
        t_length = dl.get_problem(pid)["problem_level"]
        if t_length <= 2:
            j_map[pid] = 1
        elif t_length <= 4:
            j_map[pid] = 2
        elif t_length <= 6:
            j_map[pid] = 3
        elif t_length <= 8:
            j_map[pid] = 4
        elif t_length <= 10:
            j_map[pid] = 5
        else:
            j_map[pid] = 6

        problem_total[j_map[pid]] += 1

    for i in range(1, level_count + 1):
        problem_total[0] += problem_total[i]

    print("problem count\ntotal" + "".join(["\tl{}".format(i + 1) for i in range(level_count)]))
    for i in range(level_count + 1):
        print("{}\t".format(problem_total[i]), end="")

    print("\n\nroughly\nmethod\tstrategy\tsolved\tunsolved\ttimeout\terror\tunhandled")
    for m in method:
        for s in strategy:
            log = load_json(os.path.join(path_logs, "search", "{}-log-{}-{}.json".format(dataset_name, m, s)))
            solved = len(log["solved_pid"])
            unsolved = len(log["unsolved_pid"])
            timeout = len(log["timeout_pid"])
            error = len(log["error_pid"])
            unhandled = problem_total[0] - (solved + unsolved + timeout + error)
            print("{}\t{}\t{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}".format(
                m.upper(), s.upper(),
                solved / problem_total[0] * 100,
                unsolved / problem_total[0] * 100,
                timeout / problem_total[0] * 100,
                error / problem_total[0] * 100,
                unhandled / problem_total[0] * 100))

    solved_count = [[0 for _ in range(level_count + 1)] for _ in range(config_count)]
    timing_solved = [[0 for _ in range(level_count + 1)] for _ in range(config_count)]
    timing_unsolved = [[0 for _ in range(level_count + 1)] for _ in range(config_count)]
    step_size_solved = [[0 for _ in range(level_count + 1)] for _ in range(config_count)]
    step_size_unsolved = [[0 for _ in range(level_count + 1)] for _ in range(config_count)]

    for m in method:
        for s in strategy:
            data = load_json(os.path.join(path_logs, "search", "{}-data-{}-{}.json".format(dataset_name, m, s)))
            data["unsolved"].update(data["timeout"])
            data["unsolved"].update(data["error"])
            i = i_map[(m, s)]

            for pid in range(1, dl.info["problem_number"] + 1):
                j = j_map[pid]
                if str(pid) in data["solved"]:
                    problem_data = data["solved"][str(pid)]
                    solved_count[i][j] += 1
                    timing_solved[i][j] += problem_data["timing"]
                    step_size_solved[i][j] += problem_data["step_size"]
                elif str(pid) in data["unsolved"]:
                    problem_data = data["unsolved"][str(pid)]
                    timing_unsolved[i][j] += problem_data["timing"]
                    step_size_unsolved[i][j] += problem_data["step_size"]

    for m in method:
        for s in strategy:
            i = i_map[(m, s)]
            for j in range(level_count):
                solved_count[i][0] += solved_count[i][j + 1]
                timing_solved[i][0] += timing_solved[i][j + 1]
                timing_unsolved[i][0] += timing_unsolved[i][j + 1]
                step_size_solved[i][0] += step_size_solved[i][j + 1]
                step_size_unsolved[i][0] += step_size_unsolved[i][j + 1]

    print("\nsolved\nmethod\tstrategy\ttotal" + "".join(["\tl{}".format(i + 1) for i in range(level_count)]))
    for m in method:
        for s in strategy:
            print("{}\t{}".format(m, s).upper(), end="")
            i = i_map[(m, s)]
            for j in range(level_count + 1):
                print("\t{:.2f}".format(solved_count[i][j] / problem_total[j] * 100), end="")
            print()

    print("\ntiming_solved\nmethod\tstrategy\ttotal" + "".join(["\tl{}".format(i + 1) for i in range(level_count)]))
    for m in method:
        for s in strategy:
            print("{}\t{}".format(m, s).upper(), end="")
            i = i_map[(m, s)]
            for j in range(level_count + 1):
                if solved_count[i][j] == 0:
                    print("\tNaN", end="")
                else:
                    timing_solved[i][j] = timing_solved[i][j] / solved_count[i][j]
                    print("\t{:.2f}".format(timing_solved[i][j]), end="")
            print()

    print("\ntiming_unsolved\nmethod\tstrategy\ttotal" + "".join(["\tl{}".format(i + 1) for i in range(level_count)]))
    for m in method:
        for s in strategy:
            print("{}\t{}".format(m, s).upper(), end="")
            i = i_map[(m, s)]
            for j in range(level_count + 1):
                timing_unsolved[i][j] = timing_unsolved[i][j] / (problem_total[j] - solved_count[i][j])
                print("\t{:.2f}".format(timing_unsolved[i][j]), end="")
            print()

    print("\nstep_size_solved\nmethod\tstrategy\ttotal" + "".join(["\tl{}".format(i + 1) for i in range(level_count)]))
    for m in method:
        for s in strategy:
            print("{}\t{}".format(m, s).upper(), end="")
            i = i_map[(m, s)]
            for j in range(level_count + 1):
                if solved_count[i][j] == 0:
                    print("\tNaN", end="")
                else:
                    step_size_solved[i][j] = step_size_solved[i][j] / solved_count[i][j]
                    print("\t{:.2f}".format(step_size_solved[i][j]), end="")
            print()

    print(
        "\nstep_size_unsolved\nmethod\tstrategy\ttotal" + "".join(["\tl{}".format(i + 1) for i in range(level_count)]))
    for m in method:
        for s in strategy:
            print("{}\t{}".format(m, s).upper(), end="")
            i = i_map[(m, s)]
            for j in range(level_count + 1):
                step_size_unsolved[i][j] = step_size_unsolved[i][j] / (problem_total[j] - solved_count[i][j])
                print("\t{:.2f}".format(step_size_unsolved[i][j]), end="")
            print()

    return i_map, timing_solved, timing_unsolved, step_size_solved, step_size_unsolved


def draw_search_results(path_datasets, dataset_name, path_logs):
    i_map, timing_solved, timing_unsolved, step_size_solved, step_size_unsolved = check_search(
        path_datasets, dataset_name, path_logs)
    x = [1, 2, 3, 4, 5, 6]

    plt.figure(figsize=(16, 8))
    fontsize = 14

    plt.subplot(241)
    for s in strategy:
        y = timing_solved[i_map[("fw", s)]][1:]
        plt.plot(x, y, label="{}-{}".format("fw", s).upper())
    plt.title("Time (forward, solved)", fontsize=fontsize)
    plt.xlabel("Problem Difficulty", fontsize=fontsize)
    plt.ylabel("Average time (s)", fontsize=fontsize)
    plt.legend(loc="upper left")

    plt.subplot(242)
    for s in strategy:
        y = timing_unsolved[i_map[("fw", s)]][1:]
        plt.plot(x, y, label="{}-{}".format("fw", s).upper())
    plt.title("Time (forward, unsolved)", fontsize=fontsize)
    plt.xlabel("Problem Difficulty", fontsize=fontsize)
    plt.ylabel("Average time (s)", fontsize=fontsize)
    plt.legend(loc="upper left")

    plt.subplot(243)
    for s in strategy:
        y = timing_solved[i_map[("bw", s)]][1:]
        plt.plot(x, y, label="{}-{}".format("bw", s).upper())
    plt.title("Time (backward, solved)", fontsize=fontsize)
    plt.xlabel("Problem Difficulty", fontsize=fontsize)
    plt.ylabel("Average time (s)", fontsize=fontsize)
    plt.legend(loc="upper left")

    plt.subplot(244)
    for s in strategy:
        y = timing_unsolved[i_map[("bw", s)]][1:]
        plt.plot(x, y, label="{}-{}".format("bw", s).upper())
    plt.title("Time (backward, unsolved)", fontsize=fontsize)
    plt.xlabel("Problem Difficulty", fontsize=fontsize)
    plt.ylabel("Average time (s)", fontsize=fontsize)
    plt.legend(loc="upper left")

    plt.subplot(245)
    for s in strategy:
        y = step_size_solved[i_map[("fw", s)]][1:]
        plt.plot(x, y, label="{}-{}".format("fw", s).upper())
    plt.title("Step (forward, solved)", fontsize=fontsize)
    plt.xlabel("Problem Difficulty", fontsize=fontsize)
    plt.ylabel("Average step", fontsize=fontsize)
    plt.legend(loc="upper left")

    plt.subplot(246)
    for s in strategy:
        y = step_size_unsolved[i_map[("fw", s)]][1:]
        plt.plot(x, y, label="{}-{}".format("fw", s).upper())
    plt.title("Step (forward, unsolved)", fontsize=fontsize)
    plt.xlabel("Problem Difficulty", fontsize=fontsize)
    plt.ylabel("Average step", fontsize=fontsize)
    plt.legend(loc="upper left")

    plt.subplot(247)
    for s in strategy:
        y = step_size_solved[i_map[("bw", s)]][1:]
        plt.plot(x, y, label="{}-{}".format("bw", s).upper())
    plt.title("Step (backward, solved)", fontsize=fontsize)
    plt.xlabel("Problem Difficulty", fontsize=fontsize)
    plt.ylabel("Average step", fontsize=fontsize)
    plt.legend(loc="upper left")

    plt.subplot(248)
    for s in strategy:
        y = step_size_unsolved[i_map[("bw", s)]][1:]
        plt.plot(x, y, label="{}-{}".format("bw", s).upper())
    plt.title("Step (backward, unsolved)", fontsize=fontsize)
    plt.xlabel("Problem Difficulty", fontsize=fontsize)
    plt.ylabel("Average step", fontsize=fontsize)
    plt.legend(loc="upper left")

    plt.tight_layout()
    plt.savefig(os.path.join(path_logs, "run/auto_logs/chart_search_results.pdf"), format='pdf')
    plt.show()


if __name__ == '__main__':
    args = get_args()
    if args.func == "check_search":
        check_search(args.path_datasets, "formalgeo7k_v1", "./231016")
    elif args.func == "draw_search_results":
        draw_search_results(args.path_datasets, "formalgeo7k_v1", "./231016")
    else:
        msg = "No function name {}.".format(args.func)
        raise Exception(msg)

    # check_search("F:/Datasets/released", "formalgeo7k_v1", "./231016")
    # draw_search_results("F:/Datasets/released", "formalgeo7k_v1", "./231016")

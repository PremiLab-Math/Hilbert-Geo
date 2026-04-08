if __package__ in {None, ""}:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import os.path
from fgps import get_args
from hilbert_geo.tools import load_json
from hilbert_geo.data import DatasetLoader
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


def add_commas(x, pos):
    """Add commas to large numbers."""
    return f'{x:,.0f}'


formatter = FuncFormatter(add_commas)


def check_run(path_datasets, dataset_name, path_logs, expanded=False):
    dl = DatasetLoader(dataset_name, path_datasets)
    logs = load_json(os.path.join(path_logs, "run/auto_logs/{}.json".format(dataset_name)))
    stop_pid = dl.info["problem_number"] if not expanded else dl.info["expanded_problem_number"]

    avg_time = {}  # {problem_level: [total_time, problem_count]}

    for pid in range(1, stop_pid + 1):
        level = logs["data"][str(pid)][0]
        timing = logs["data"][str(pid)][1]
        if level in avg_time:
            avg_time[level][0] += timing
            avg_time[level][1] += 1
        else:
            avg_time[level] = [timing, 1]
    if 0 in avg_time:
        if 1 in avg_time:
            avg_time[1][0] += avg_time[0][0]
            avg_time[1][1] += avg_time[0][1]
        else:
            avg_time[1] = avg_time[0]
        avg_time.pop(0)

    avg_time = {key: avg_time[key] for key in sorted(avg_time.keys())}
    print("{}(expanded={}):".format(dataset_name, expanded))
    print("problem_level\ttiming_total(s)\tproblem_count\tavg_time(ms)")
    for l in avg_time:
        avg_time[l].append(avg_time[l][0] / avg_time[l][1] * 1000)
        print("{}\t{}\t{}\t{}".format(l, avg_time[l][0], avg_time[l][1], avg_time[l][2]))

    return stop_pid, avg_time


def draw_run_results(path_datasets, path_logs):
    """{problem_level: [total_time, problem_count, avg_time]}"""
    stop_pid, avg_time_7k = check_run(path_datasets, "formalgeo7k_v1", path_logs, expanded=False)
    level_7k = []
    percentages_7k = []
    timing_7k = []
    for l in avg_time_7k:
        level_7k.append(l)
        percentages_7k.append(avg_time_7k[l][1] / stop_pid)
        timing_7k.append(avg_time_7k[l][2])

    stop_pid, avg_time_7k_e = check_run(path_datasets, "formalgeo7k_v1", path_logs, expanded=True)
    level_7k_e = []
    percentages_7k_e = []
    timing_7k_e = []
    for l in avg_time_7k_e:
        level_7k_e.append(l)
        percentages_7k_e.append(avg_time_7k_e[l][1] / stop_pid)
        timing_7k_e.append(avg_time_7k_e[l][2])

    stop_pid, avg_time_imo = check_run(path_datasets, "formalgeo-imo_v1", path_logs, expanded=False)
    level_imo = []
    percentages_imo = []
    timing_imo = []
    for l in avg_time_imo:
        level_imo.append(l)
        percentages_imo.append(avg_time_imo[l][1] / stop_pid)
        timing_imo.append(avg_time_imo[l][2])

    stop_pid, avg_time_imo_e = check_run(path_datasets, "formalgeo-imo_v1", path_logs, expanded=True)
    level_imo_e = []
    percentages_imo_e = []
    timing_imo_e = []
    for l in avg_time_imo_e:
        level_imo_e.append(l)
        percentages_imo_e.append(avg_time_imo_e[l][1] / stop_pid)
        timing_imo_e.append(avg_time_imo_e[l][2])

    plt.figure(figsize=(16, 8))
    fontsize = 14

    plt.subplot(241)
    plt.plot(level_7k, percentages_7k, label='formalgeo7k')
    plt.xlabel("Problem Level", fontsize=fontsize)
    plt.ylabel("Frequency (%)", fontsize=fontsize)
    plt.title(" ", fontsize=fontsize)
    plt.legend(loc="upper left")

    plt.subplot(242)
    plt.plot(level_7k_e, percentages_7k_e, label='formalgeo7k(DA)')
    plt.xlabel("Problem Level", fontsize=fontsize)
    plt.ylabel("Frequency (%)", fontsize=fontsize)
    plt.title(" ", fontsize=fontsize)
    plt.legend(loc="upper left")

    plt.subplot(243)
    plt.plot(level_imo, percentages_imo, label='formalgeo-imo')
    plt.xlabel("Problem Level", fontsize=fontsize)
    plt.ylabel("Frequency (%)", fontsize=fontsize)
    plt.title(" ", fontsize=fontsize)
    plt.legend(loc="upper left")

    plt.subplot(244)
    plt.plot(level_imo_e, percentages_imo_e, label='formalgeo-imo(DA)')
    plt.xlabel("Problem Level", fontsize=fontsize)
    plt.ylabel("Frequency (%)", fontsize=fontsize)
    plt.title(" ", fontsize=fontsize)
    plt.legend(loc="upper left")

    plt.subplot(245)
    plt.plot(level_7k, timing_7k, label='formalgeo7k')
    plt.xlabel("Problem Level", fontsize=fontsize)
    plt.ylabel("Average Time (ms)", fontsize=fontsize)
    plt.title(" ", fontsize=fontsize)
    plt.legend(loc="upper left")
    plt.gca().xaxis.set_major_formatter(formatter)
    plt.gca().yaxis.set_major_formatter(formatter)

    plt.subplot(246)
    plt.plot(level_7k_e, timing_7k_e, label='formalgeo7k(DA)')
    plt.xlabel("Problem Level", fontsize=fontsize)
    plt.ylabel("Average Time (ms)", fontsize=fontsize)
    plt.title(" ", fontsize=fontsize)
    plt.legend(loc="upper left")
    plt.gca().xaxis.set_major_formatter(formatter)
    plt.gca().yaxis.set_major_formatter(formatter)

    plt.subplot(247)
    plt.plot(level_imo, timing_imo, label='formalgeo-imo')
    plt.xlabel("Problem Level", fontsize=fontsize)
    plt.ylabel("Average Time (ms)", fontsize=fontsize)
    plt.title(" ", fontsize=fontsize)
    plt.legend(loc="upper left")
    plt.gca().xaxis.set_major_formatter(formatter)
    plt.gca().yaxis.set_major_formatter(formatter)

    plt.subplot(248)
    plt.plot(level_imo_e, timing_imo_e, label='formalgeo-imo(DA)')
    plt.xlabel("Problem Level", fontsize=fontsize)
    plt.ylabel("Average Time (ms)", fontsize=fontsize)
    plt.title(" ", fontsize=fontsize)
    plt.legend(loc="upper left")
    plt.gca().xaxis.set_major_formatter(formatter)
    plt.gca().yaxis.set_major_formatter(formatter)

    plt.tight_layout()
    plt.savefig(os.path.join(path_logs, "run/auto_logs/chart_problem_level.pdf"), format='pdf')
    plt.show()


if __name__ == '__main__':
    args = get_args()
    if args.func == "check_run":
        check_run(args.path_datasets, "formalgeo7k_v1", "./231016")
        print()
        check_run(args.path_datasets, "formalgeo7k_v1", "./231016", True)
        print()
        check_run(args.path_datasets, "formalgeo-imo_v1", "./231016")
        print()
        check_run(args.path_datasets, "formalgeo-imo_v1", "./231016", True)
    elif args.func == "draw_run_results":
        draw_run_results(args.path_datasets, "./231016")
    else:
        msg = "No function name {}.".format(args.func)
        raise Exception(msg)

    # check_run("F:/Datasets/released", "formalgeo7k_v1", "./231016")
    # check_run("F:/Datasets/released", "formalgeo7k_v1", "./231016", True)
    # check_run("F:/Datasets/released", "formalgeo-imo_v1", "./231016")
    # check_run("F:/Datasets/released", "formalgeo-imo_v1", "./231016", True)
    # draw_run_results("F:/Datasets/released", "./231016")

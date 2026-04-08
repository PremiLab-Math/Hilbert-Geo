if __package__ in {None, ""}:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import os
from pathlib import Path
from hilbert_geo.data import download_dataset
import psutil
import argparse
from fgps._paths import DATA_ROOT, LOG_ROOT, DEFAULT_DATASET_NAME

method = ["fw", "bw"]  # forward, backward
strategy = ["bfs", "dfs", "rs", "bs"]  # deep first, breadth first, random, beam


def get_args():
    parser = argparse.ArgumentParser(description="Welcome to use FGPS!")

    # func
    parser.add_argument("--func", type=str, required=False, default="",
                        help="function that you want to run")

    # file path
    parser.add_argument("--path_datasets", type=str, required=False, default=str(DATA_ROOT),
                        help="datasets path")
    parser.add_argument("--path_logs", type=str, required=False, default=str(LOG_ROOT),
                        help="path that save search log and result")

    # basic search para
    parser.add_argument("--dataset_name", type=str, required=False, default=DEFAULT_DATASET_NAME,
                        help="dataset name")
    parser.add_argument("--method", type=str, required=False, choices=("fw", "bw"), default="fw",
                        help="search method")
    parser.add_argument("--strategy", type=str, required=False, choices=("bfs", "dfs", "rs", "bs"), default="bfs",
                        help="search strategy")

    # other search para
    parser.add_argument("--max_depth", type=int, required=False, default=1500000,
                        help="max search depth")
    parser.add_argument("--beam_size", type=int, required=False, default=25000,
                        help="search beam size")
    parser.add_argument("--timeout", type=int, required=False, default=3600000,
                        help="search timeout")
    parser.add_argument("--process_count", type=int, required=False, default=int(psutil.cpu_count() * 0.8),
                        help="multi process count")
    parser.add_argument("--random_seed", type=int, required=False, default=700,
                        help="random seed")

    return parser.parse_args()


def create_log_archi(path_logs):
    path_logs = str(Path(path_logs))
    filepaths = [
        os.path.join(path_logs, "search"),
        os.path.join(path_logs, "run/auto_logs"),
        os.path.join(path_logs, "run/problems")
    ]

    for filepath in filepaths:
        if not os.path.exists(filepath):
            os.makedirs(filepath)


def download_datasets(path_datasets):
    path_datasets = str(Path(path_datasets))
    if not os.path.exists(path_datasets):
        os.makedirs(path_datasets)

    download_dataset("hilbert_geo_sample_1k", path_datasets)
    download_dataset("formalgeo-imo_v1", path_datasets)


if __name__ == '__main__':
    args = get_args()

    if args.func == "download_datasets":
        download_datasets(args.path_datasets)
    elif args.func == "create_log_archi":
        create_log_archi(args.path_logs)
    else:
        msg = "No function name {}.".format(args.func)
        raise Exception(msg)

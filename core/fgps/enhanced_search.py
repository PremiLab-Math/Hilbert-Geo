#!/usr/bin/env python3
"""
增强版搜索脚本，会跳过已有解题步骤的问题
"""

if __package__ in {None, ""}:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import os
import sys

from fgps.search import *  # noqa: F403
from hilbert_geo.tools import load_json

def check_problem_has_solution(dl, problem_id):
    """
    检查问题是否已经有解题步骤
    
    Args:
        dl: DatasetLoader实例
        problem_id: 问题ID
        
    Returns:
        bool: 如果有非空的解题步骤则返回True
    """
    try:
        problem_data = dl.get_problem(problem_id)
        theorem_seqs = problem_data.get("theorem_seqs", [])
        
        # 检查是否有非空的解题步骤
        if theorem_seqs and len(theorem_seqs) > 0:
            # 过滤掉空字符串和None
            non_empty_seqs = [seq for seq in theorem_seqs if seq and str(seq).strip()]
            if non_empty_seqs:
                return True
        
        return False
    
    except Exception as e:
        print(f"检查问题 {problem_id} 时出错: {e}")
        return False

def enhanced_search(args):
    """增强版搜索函数，会跳过已有解题步骤的问题"""
    dl = DatasetLoader(args.dataset_name, args.path_datasets)
    log_filename, data_filename = init_search_log(args, dl)
    log = load_json(log_filename)
    data = load_json(data_filename)
    problem_ids = []  # problem id
    process_ids = []  # process id
    
    reply_queue = Queue()
    
    skipped_with_solutions = 0
    skipped_in_log = 0
    
    # 如果要调整ID范围，可以在这里直接修改log中的值
    # 例如：log["start_pid"] = 100  # 从问题100开始
    #      log["end_pid"] = 200     # 到问题200结束
    test_problem_ids = [571]
    
    for problem_id in test_problem_ids:  # assign tasks
        # 首先检查日志中是否已处理
        if problem_id in log["solved_pid"] or problem_id in log["unsolved_pid"] or \
                problem_id in log["timeout_pid"] or problem_id in log["error_pid"]:
            skipped_in_log += 1
            continue
        
        # 然后检查问题是否已有解题步骤
        if check_problem_has_solution(dl, problem_id):
            print(f"⏭️ 跳过问题 {problem_id}：已有解题步骤")
            skipped_with_solutions += 1
            continue
            
        problem_ids.append(problem_id)
    
    problem_ids = problem_ids[::-1]
    
    print(f"📊 搜索统计:")
    print(f"  - 日志中已处理的问题: {skipped_in_log}")
    print(f"  - 已有解题步骤的问题: {skipped_with_solutions}")
    print(f"  - 待处理的问题: {len(problem_ids)}")
    print(f"  - 问题ID范围: {problem_ids[-1] if problem_ids else 'N/A'} - {problem_ids[0] if problem_ids else 'N/A'}")
    
    if not problem_ids:
        print("🎉 所有问题都已处理或有解题步骤！")
        return
    
    clean_count = 0
    print("\nprocess_id\tproblem_id\tresult\tmsg")
    # The loop should continue as long as there are problems to be processed or there are active processes running.
    while (clean_count < 23 and problem_ids) or process_ids:
        start_process(args, dl, problem_ids, process_ids, reply_queue)  # search
        
        if not process_ids and not problem_ids:  # 如果没有活跃进程且没有待处理问题
            break
            
        try:
            process_id, problem_id, result, msg, timing, step_size = reply_queue.get()
            data[result][str(problem_id)] = {"msg": msg, "timing": timing, "step_size": step_size}
            log["{}_pid".format(result)].append(problem_id)
            safe_save_json(log, log_filename)
            safe_save_json(data, data_filename)
            print("{}\t{}\t{}\t{}".format(process_id, problem_id, result, msg))

            if process_id in process_ids:
                process_ids.pop(process_ids.index(process_id))
            clean_count += 1
            if clean_count == int(args.process_count / 3):
                clean_process(process_ids)
                clean_count = 0
        
        except Exception as e:
            print(f"等待结果时出错: {type(e).__name__} - {e}")
            break

def enhanced_test_search(args, problem_id):
    """增强版测试搜索函数"""
    dl = DatasetLoader(args.dataset_name, args.path_datasets)
    
    # 检查问题是否已有解题步骤
    if check_problem_has_solution(dl, problem_id):
        print(f"⏭️ 问题 {problem_id} 已有解题步骤:")
        problem_data = dl.get_problem(problem_id)
        theorem_seqs = problem_data.get("theorem_seqs", [])
        for i, seq in enumerate(theorem_seqs, 1):
            print(f"  {i}. {seq}")
        return
    
    print(f"🔍 开始搜索问题 {problem_id}...")
    solve(args, dl, problem_id, None, True)

if __name__ == '__main__':
    # 检查是否有测试问题ID作为额外参数
    test_problem_id = None
    if '--test' in sys.argv:
        test_idx = sys.argv.index('--test')
        if test_idx + 1 < len(sys.argv):
            try:
                test_problem_id = int(sys.argv[test_idx + 1])
                # 移除测试参数，避免get_args()出错
                sys.argv.remove('--test')
                sys.argv.remove(str(test_problem_id))
            except ValueError:
                print("错误：--test 参数后必须跟一个有效的问题ID")
                sys.exit(1)
    
    args = get_args()
    
    if test_problem_id is not None:
        enhanced_test_search(args, test_problem_id)
    else:
        enhanced_search(args)

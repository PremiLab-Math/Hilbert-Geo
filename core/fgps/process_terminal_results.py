#!/usr/bin/env python3
"""
直接从终端输出处理搜索结果并更新问题文件
"""

if __package__ in {None, ""}:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
import os
import re
from pathlib import Path
from fgps._paths import DATA_ROOT, DEFAULT_DATASET_NAME

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def convert_search_result_to_theorem_seq(search_result_str):
    """
    将搜索结果字符串转换为定理序列格式
    
    输入: "[('circle_area_formula', '1', ('P',)), ('cylinder_volume_formula_common', '1', ('P', 'Q'))]"
    输出: ["circle_area_formula(P)", "cylinder_volume_formula_common(P,Q)"]
    """
    try:
        # 清理字符串
        search_result_str = search_result_str.strip()
        
        if not search_result_str or search_result_str == "None" or search_result_str == "[]":
            return []
        
        # 安全地解析Python字面量
        import ast
        search_result = ast.literal_eval(search_result_str)
        
        if not isinstance(search_result, list):
            return []
        
        theorem_seqs = []
        for theorem_info in search_result:
            if isinstance(theorem_info, tuple) and len(theorem_info) >= 3:
                theorem_name = theorem_info[0]
                # theorem_branch = theorem_info[1]  # 通常是 '1'
                theorem_params = theorem_info[2]
                
                # 构建定理调用格式
                if isinstance(theorem_params, (tuple, list)):
                    param_str = ','.join(str(p) for p in theorem_params)
                else:
                    param_str = str(theorem_params)
                
                theorem_call = f"{theorem_name}({param_str})"
                theorem_seqs.append(theorem_call)
        
        return theorem_seqs
    
    except Exception as e:
        print(f"转换搜索结果时出错: {e}")
        print(f"原始字符串: {search_result_str}")
        return []

def extract_solved_problems_from_terminal():
    """
    从您提供的终端输出中提取已解决的问题
    """
    # 这里是您提供的终端输出数据
    terminal_data = """
8172    1       solved  [('circle_property_length_of_radius_and_diameter', '1', ('O',))]
10400   2       solved  []
30812   5       solved  [('circle_area_formula', '1', ('P',)), ('circle_area_formula', '1', ('A',)), ('cylinder_volume_formula_common', '1', ('A', 'B')), ('cylinder_volume_formula_common', '1', ('P', 'Q'))]
37944   6       solved  [('circle_area_formula', '1', ('P',)), ('circle_property_length_of_radius_and_diameter', '1', ('Q',)), ('circle_property_length_of_radius_and_diameter', '1', ('A',)), ('circle_area_formula', '1', ('A',)), ('cylinder_volume_formula_common', '1', ('A', 'B')), ('cylinder_volume_formula_common', '1', ('P', 'Q'))]
38684   7       solved  [('circle_area_formula', '1', ('P',)), ('cylinder_volume_formula_common', '1', ('P', 'Q'))]
4924    8       solved  [('circle_area_formula', '1', ('P',)), ('cylinder_volume_formula_common', '1', ('P', 'Q'))]
38092   9       solved  [('circle_area_formula', '1', ('O',)), ('cone_volume_formula_common', '1', ('O', 'P'))]
9568    10      solved  [('circle_area_formula', '1', ('O',)), ('cone_volume_formula_common', '1', ('O', 'P'))]
38176   11      solved  [('circle_property_length_of_radius_and_diameter', '1', ('O',)), ('circle_area_formula', '1', ('O',)), ('cone_volume_formula_common', '1', ('O', 'P'))]
38548   12      solved  [('circle_area_formula', '1', ('O',)), ('cone_volume_formula_common', '1', ('O', 'P'))]
38356   13      solved  [('circle_area_formula', '1', ('O',)), ('cone_volume_formula_common', '1', ('O', 'P'))]
38700   14      solved  [('sphere_volume_formula', '1', ('O',))]
38580   15      solved  [('sphere_property_length_of_radius_and_diameter', '1', ('O',)), ('sphere_volume_formula', '1', ('O',))]
712     16      solved  [('sphere_property_length_of_radius_and_diameter', '1', ('O',)), ('sphere_volume_formula', '1', ('O',)), ('sphere_property_length_of_radius_and_diameter', '1', ('P',)), ('sphere_volume_formula', '1', ('P',))]
38840   17      solved  [('sphere_volume_formula', '1', ('O',))]
35672   18      solved  [('sphere_volume_formula', '1', ('O',))]
38560   19      solved  [('sphere_volume_formula', '1', ('O',))]
38824   20      solved  [('sphere_volume_formula', '1', ('O',))]
38076   21      solved  [('circle_area_formula', '1', ('P',)), ('circle_area_formula', '1', ('Q',)), ('cylinder_area_formula', '1', ('P', 'Q'))]
38456   22      solved  [('circle_area_formula', '1', ('P',)), ('circle_area_formula', '1', ('Q',)), ('cylinder_area_formula', '1', ('P', 'Q'))]
14600   23      solved  [('circle_area_formula', '1', ('P',)), ('circle_area_formula', '1', ('Q',)), ('cylinder_area_formula', '1', ('P', 'Q'))]
38340   24      solved  [('circle_area_formula', '1', ('P',)), ('circle_area_formula', '1', ('Q',)), ('cylinder_area_formula', '1', ('P', 'Q'))]
38512   25      solved  [('circle_area_formula', '1', ('P',)), ('circle_area_formula', '1', ('Q',)), ('cylinder_area_formula', '1', ('P', 'Q'))]
36324   26      solved  [('circle_area_formula', '1', ('P',)), ('circle_area_formula', '1', ('Q',)), ('cylinder_area_formula', '1', ('P', 'Q'))]
11688   27      solved  [('circle_area_formula', '1', ('P',)), ('circle_area_formula', '1', ('Q',)), ('cylinder_area_formula', '1', ('P', 'Q'))]
36936   28      solved  [('circle_area_formula', '1', ('P',)), ('circle_area_formula', '1', ('Q',)), ('circle_area_formula', '1', ('A',)), ('circle_area_formula', '1', ('B',)), ('cylinder_area_formula', '1', ('A', 'B')), ('cylinder_area_formula', '1', ('P', 'Q'))]
13872   30      solved  [('sphere_area_formula', '1', ('O',))]
38232   31      solved  [('sphere_property_length_of_radius_and_diameter', '1', ('O',)), ('sphere_area_formula', '1', ('O',))]
37784   32      solved  [('sphere_area_formula', '1', ('O',))]
30668   33      solved  [('circle_area_formula', '1', ('O',))]
38684   34      solved  [('sphere_area_formula', '1', ('O',)), ('circle_area_formula', '1', ('O',))]
38276   35      solved  [('sphere_area_formula', '1', ('O',)), ('circle_area_formula', '1', ('O',))]
38716   38      solved  [('cone_area_formula', '1', ('O', 'P')), ('sphere_area_formula', '1', ('O',))]
37912   39      solved  [('sphere_area_formula', '1', ('P',)), ('circle_area_formula', '1', ('Q',)), ('cylinder_area_formula', '1', ('P', 'Q'))]
38324   40      solved  [('sphere_area_formula', '1', ('A',))]
38432   41      solved  [('sphere_area_formula', '1', ('P',)), ('circle_area_formula', '1', ('Q',)), ('cylinder_area_formula', '1', ('P', 'Q'))]
21740   29      unsolved        None
39096   49      error   TypeError("unsupported operand type(s) for ^: 'Symbol' and 'Add'")
38940   52      solved  [('circle_area_formula', '1', ('P',)), ('cylinder_volume_formula_common', '1', ('P', 'Q'))]
37460   53      solved  [('circle_property_length_of_radius_and_diameter', '1', ('P',)), ('circle_area_formula', '1', ('P',)), ('cylinder_volume_formula_common', '1', ('P', 'Q'))]
39112   54      solved  [('circle_property_length_of_radius_and_diameter', '1', ('P',)), ('circle_area_formula', '1', ('P',)), ('cylinder_volume_formula_common', '1', ('P', 'Q'))]
39888   55      solved  [('circle_property_length_of_radius_and_diameter', '1', ('P',)), ('circle_area_formula', '1', ('P',)), ('cylinder_volume_formula_common', '1', ('P', 'Q'))]
712     56      solved  [('circle_property_length_of_radius_and_diameter', '1', ('P',)), ('circle_area_formula', '1', ('P',)), ('cylinder_volume_formula_common', '1', ('P', 'Q'))]
39044   57      solved  [('circle_area_formula', '1', ('P',)), ('cylinder_volume_formula_common', '1', ('P', 'Q'))]
20472   58      solved  [('circle_area_formula', '1', ('P',)), ('circle_area_formula', '1', ('A',)), ('cylinder_volume_formula_common', '1', ('A', 'B')), ('cylinder_volume_formula_common', '1', ('P', 'Q'))]
35780   59      solved  [('circle_area_formula', '1', ('P',)), ('cylinder_volume_formula_common', '1', ('P', 'Q'))]
10400   36      solved  [('circle_area_formula', '1', ('Q',)), ('cuboid_area_formula', '1', ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'))]
35824   60      solved  [('circle_area_formula', '1', ('P',)), ('cylinder_volume_formula_common', '1', ('P', 'Q'))]
36624   61      solved  [('circle_area_formula', '1', ('P',)), ('cylinder_volume_formula_common', '1', ('P', 'Q'))]
38180   62      solved  [('circle_area_formula', '1', ('A',)), ('circle_area_formula', '1', ('P',)), ('cylinder_volume_formula_common', '1', ('P', 'Q')), ('cylinder_volume_formula_common', '1', ('A', 'B'))]
39248   63      solved  [('circle_area_formula', '1', ('A',)), ('circle_property_length_of_radius_and_diameter', '1', ('C',)), ('circle_area_formula', '1', ('C',)), ('circle_area_formula', '1', ('P',)), ('cylinder_volume_formula_common', '1', ('P', 'Q')), ('cylinder_volume_formula_common', '1', ('A', 'B')), ('cylinder_volume_formula_common', '1', ('C', 'D'))]
40672   70      error   ValueError('not enough values to unpack (expected 2, got 1)')
40560   71      error   ValueError('not enough values to unpack (expected 2, got 1)')  
40092   73      error   KeyError('type')
40420   74      error   IndexError('string index out of range')
40312   75      error   KeyError('type')
40120   76      error   KeyError('type')
10912   77      error   KeyError('type')
40468   78      error   KeyError('type')
40916   79      error   KeyError('type')
39228   80      error   KeyError('type')
20220   65      solved  [('cube_area_formula', '1', ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'))]
40412   81      error   KeyError('type')
38740   82      error   KeyError('type')
36720   83      error   KeyError('type')
35384   84      unsolved        None
24228   85      solved  [('sphere_volume_formula', '1', ('A',)), ('sphere_volume_formula', '1', ('B',))]
38276   86      solved  []
24220   87      error   SyntaxError('invalid syntax', ('<string>', 1, 14, "Integer (12 )Symbol ('x' )^Integer (2 )+Integer (144 )Symbol ('x' )+Integer (384 )", 1, 20))       
38060   88      error   KeyError('type')
11928   89      error   Exception('Operator 3*pi*x* not defined, please check your expression.')
36292   90      error   KeyError('type')
38684   91      unsolved        None
37968   96      error   Exception("Predicate 'RightTriangularPyramid' not defined in current predicate GDL.")
36624   97      error   FileNotFoundError(2, 'No such file or directory')
21668   98      error   FileNotFoundError(2, 'No such file or directory')
3432    99      error   FileNotFoundError(2, 'No such file or directory')
1948    100     unsolved        None
38872   106     solved  [('circle_area_formula', '1', ('P',)), ('circle_area_formula', '1', ('Q',)), ('cylinder_area_formula', '1', ('P', 'Q'))]
16720   107     solved  [('circle_area_formula', '1', ('P',)), ('circle_area_formula', '1', ('Q',)), ('cylinder_area_formula', '1', ('P', 'Q'))]
36488   94      solved  [('cube_volume_formula', '1', ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'))]
40568   108     solved  [('circle_area_formula', '1', ('A',)), ('circle_area_formula', '1', ('B',)), ('circle_area_formula', '1', ('C',)), ('circle_area_formula', '1', ('D',)), ('circle_area_formula', '1', ('P',)), ('cylinder_area_formula', '1', ('A', 'B')), ('cylinder_area_formula', '1', ('C', 'D')), ('cylinder_area_formula', '1', ('P', 'Q'))]
"""
    
    solved_problems = {}
    
    # 解析终端输出
    lines = terminal_data.strip().split('\n')
    for line in lines:
        if 'solved' in line:
            # 使用正则表达式更准确地解析
            import re
            # 匹配格式: process_id   problem_id   solved   [theorem_list]
            match = re.match(r'(\d+)\s+(\d+)\s+(solved)\s+(.*)', line.strip())
            if match:
                try:
                    process_id = int(match.group(1))
                    problem_id = int(match.group(2))
                    result = match.group(3)
                    msg = match.group(4).strip()
                    
                    print(f"解析行: 问题ID={problem_id}, 结果={result}, 消息={msg[:100]}...")
                    
                    if result == 'solved' and msg != '[]':
                        theorem_seqs = convert_search_result_to_theorem_seq(msg)
                        if theorem_seqs:
                            solved_problems[problem_id] = theorem_seqs
                            print(f"✅ 问题 {problem_id}: {theorem_seqs}")
                        else:
                            print(f"⚠️ 问题 {problem_id}: 转换后为空")
                    else:
                        print(f"⏭️ 问题 {problem_id}: 跳过 (空结果或非solved)")
                
                except Exception as e:
                    print(f"❌ 解析行时出错: {line[:100]}...")
                    print(f"错误: {e}")
            else:
                print(f"⚠️ 无法匹配行格式: {line[:50]}...")
    
    return solved_problems

def update_problem_files(problems_dir, solved_problems):
    """
    更新问题文件，添加解题步骤
    """
    updated_count = 0
    
    for problem_id, theorem_seqs in solved_problems.items():
        problem_file = os.path.join(problems_dir, f"{problem_id}.json")
        
        if not os.path.exists(problem_file):
            print(f"⚠️ 问题文件不存在: {problem_file}")
            continue
        
        try:
            # 加载问题文件
            problem_data = load_json(problem_file)
            
            # 检查是否已经有解题步骤
            current_seqs = problem_data.get("theorem_seqs", [])
            if current_seqs and len(current_seqs) > 0:
                # 检查是否是空的或者只有空字符串
                non_empty_seqs = [seq for seq in current_seqs if seq and seq.strip()]
                if non_empty_seqs:
                    print(f"⏭️ 问题 {problem_id} 已有解题步骤，跳过")
                    continue
            
            # 更新解题步骤
            problem_data["theorem_seqs"] = theorem_seqs
            
            # 保存更新后的文件
            save_json(problem_data, problem_file)
            updated_count += 1
            print(f"✅ 更新问题 {problem_id}: {theorem_seqs}")
            
        except Exception as e:
            print(f"❌ 更新问题 {problem_id} 时出错: {e}")
    
    print(f"\n🎉 总共更新了 {updated_count} 个问题文件")
    return updated_count

def main():
    """主函数"""
    print("🔄 开始处理搜索结果...")
    
    # 获取已解决的问题
    solved_problems = extract_solved_problems_from_terminal()
    print(f"\n📊 找到 {len(solved_problems)} 个已解决的问题")
    
    if not solved_problems:
        print("❌ 没有找到已解决的问题")
        return
    
    # 配置路径
    problems_dir = DATA_ROOT / DEFAULT_DATASET_NAME / "problems"
    
    if not problems_dir.exists():
        print(f"❌ 问题目录不存在: {problems_dir}")
        return
    
    # 更新问题文件
    updated_count = update_problem_files(problems_dir, solved_problems)
    
    if updated_count > 0:
        print(f"\n✨ 成功！下次运行搜索时，这 {updated_count} 个问题将被跳过。")
    else:
        print(f"\n ℹ️ 没有问题文件需要更新（可能都已经有解题步骤了）。")

if __name__ == "__main__":
    main()

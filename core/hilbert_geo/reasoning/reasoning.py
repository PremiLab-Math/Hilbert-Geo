from hilbert_geo.problem import Problem
from hilbert_geo.core import EquationKiller as EqKiller
from hilbert_geo.parse import parse_predicate_gdl, parse_theorem_gdl, parse_problem_cdl
from hilbert_geo.tools import rough_equal, show_solution
from hilbert_geo.solver import Interactor
import json
import warnings
from copy import deepcopy


class GeometrySolver:
    """几何问题求解器类，封装问题处理与求解的完整流程"""
    
    def __init__(self, predicate_gdl_path, theorem_gdl_path):
        """
        初始化求解器
        
        :param predicate_gdl_path: 谓词定义GDL文件路径
        :param theorem_gdl_path: 定理定义GDL文件路径
        """
        self.predicate_gdl = self._load_predicate_gdl(predicate_gdl_path)
        self.theorem_gdl = self._load_theorem_gdl(theorem_gdl_path)
        self.problem = None
        self.solving_history = []
        
    def _load_predicate_gdl(self, path):
        """加载谓词定义"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return parse_predicate_gdl(json.load(f))
        except Exception as e:
            warnings.warn(f"加载谓词定义失败: {str(e)}")
            return None
    
    def _load_theorem_gdl(self, path):
        """加载定理定义"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return parse_theorem_gdl(json.load(f),self.predicate_gdl)
        except Exception as e:
            warnings.warn(f"加载定理定义失败: {str(e)}")
            return None
    
    def load_problem(self, problem_data):
        """
        加载问题数据
        
        :param problem_data
        """
        try:
            parsed_problem = parse_problem_cdl(problem_data)
            self.problem = Problem()
            self.problem.load_problem_by_fl(
                parsed_predicate_GDL=self.predicate_gdl,  # 解析后的谓词定义
                parsed_theorem_GDL=self.theorem_gdl,      # 解析后的定理定义
                parsed_problem=parsed_problem             # 解析后的问题数据（如 parse_problem_cdl 的返回值）
                )
            self.problem._construction_init()  # 执行条件扩展
            self.solving_history = [f"问题加载完成: {problem_data.get('problem_id', '未知ID')}"]
            return True
        except Exception as e:
            warnings.warn(f"加载问题失败: {str(e)}")
            return False
    
    def apply_theorem(self, theorem_name, branch=0):
        """
        应用指定定理
        
        :param theorem_name: 定理名称
        :param branch: 定理分支索引
        :return: 应用是否成功
        """
        if not self.problem:
            warnings.warn("请先加载问题")
            return False
            
        try:
            branch_key = list(self.theorem_gdl[theorem_name]["body"].keys())[branch]
            interactor = Interactor(self.predicate_gdl, self.theorem_gdl)
            update = Interactor.apply_theorem_by_name_and_branch(
                theorem_name, branch_key
            )
            if update:
                self.solving_history.append(
                    f"应用定理成功: {theorem_name} (分支 {branch})"
                )
                EqKiller.solve_equations(self.problem)  # 求解方程
                return True
            self.solving_history.append(
                f"应用定理失败: {theorem_name} (分支 {branch})"
            )
            return False
        except Exception as e:
            self.solving_history.append(
                f"应用定理出错: {theorem_name} - {str(e)}"
            )
            return False
    
    def check_goal(self):
        """检查目标是否已解决"""
        if not self.problem:
            return False, None
            
        self.problem.check_goal()
        if self.problem.goal.solved:
            return True, self.problem.goal.solved_answer
        return False, None
    
    def solve(self, max_steps=20):
        """
        自动求解问题
        
        :param max_steps: 最大求解步骤
        :return: (是否解决, 答案, 求解历史)
        """
        if not self.problem:
            warnings.warn("请先加载问题")
            return False, None, self.solving_history
            
        for step in range(max_steps):
            # 检查是否已解决
            solved, answer = self.check_goal()
            if solved:
                self.solving_history.append(f"步骤 {step + 1}: 目标已解决，答案: {answer}")
                return True, answer, self.solving_history
            
            # 尝试应用所有可用定理
            theorem_applied = False
            for theorem_name in self.theorem_gdl:
                    
                # 尝试所有分支
                for branch_idx, branch_key in enumerate(self.theorem_gdl[theorem_name]["body"].keys()):
                    if self.apply_theorem(theorem_name, branch_idx):
                        theorem_applied = True
                        break  # 应用成功后继续检查目标
                if theorem_applied:
                    break
            
            if not theorem_applied:
                self.solving_history.append(f"步骤 {step + 1}: 无可用定理可应用，求解终止")
                break
        
        # 最终检查
        solved, answer = self.check_goal()
        return solved, answer, self.solving_history
    
    def show_solution(self):
        """展示求解过程详情"""
        if not self.problem:
            warnings.warn("请先加载问题")
            return
        show_solution(self.problem)
    
    def get_history(self):
        """获取历史"""
        return self.solving_history
    
    def copy(self):
        """创建求解器副本（用于分支探索）"""
        new_solver = GeometrySolver(None, None)
        new_solver.predicate_gdl = deepcopy(self.predicate_gdl)
        new_solver.theorem_gdl = deepcopy(self.theorem_gdl)
        new_solver.problem = deepcopy(self.problem)
        new_solver.solving_history = deepcopy(self.solving_history)
        return new_solver
